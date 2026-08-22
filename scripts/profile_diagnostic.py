"""
scripts/profile_diagnostic.py
-----------------------------
High-precision non-invasive benchmark instrumentation for Drishti AI 7-stage pipeline.
Measures wall-clock time, per-stage latency, per-frame latency, slice counts, and CPU/GPU metrics.
"""

import sys
import os
import time
import cv2
import yaml
import numpy as np
import itertools
from sahi.slicing import slice_image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_1_5_zone_calibration import calibrate_zones_stage, ZoneMap, _sahi_detect, _tiled_upscale_detect, _nms, _aggregate_multiframe
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking_fusion import tracking_fusion_stage
from stages.stage_4_event_segmentation import event_segmentation_stage
from stages.stage_5_output import output_stage

def run_diagnostic():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    video_path = config['video']['input_path']

    print("================================================================================")
    print("           DRISHTI AI — END-TO-END PIPELINE PERFORMANCE DIAGNOSTIC              ")
    print("================================================================================")

    # 1. Video Ingestion properties
    cap = cv2.VideoCapture(video_path)
    native_fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    native_fps = cap.get(cv2.CAP_PROP_FPS)
    native_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    native_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    skip = config['video']['skip_initial_frames']
    sample_rate = config['video']['frame_sample_rate']
    max_corrupt = config['video']['max_consecutive_corrupt_frames']
    target_fps = config['video']['sampling']['target_fps']
    resize_w = config['preprocessing']['resize_width']
    resize_h = config['preprocessing']['resize_height']
    clip_limit = config['preprocessing']['clahe_clip_limit']
    grid = tuple(config['preprocessing']['clahe_tile_grid_size'])
    brightness_thresh = config['preprocessing']['brightness_jump_threshold']
    enable_stab = config['preprocessing']['enable_stabilization']

    # Measure Stage 0 & 1
    t0_1_start = time.perf_counter()
    s0 = video_ingestion_stage(video_path, skip, sample_rate, max_corrupt, target_fps, config.get('debug'))
    s1 = preprocess_stage(s0, (resize_w, resize_h), clip_limit, grid, brightness_thresh, enable_stab, config.get('debug'))
    
    preprocessed_frames = []
    for pf in s1:
        preprocessed_frames.append(pf)
    t0_1_time = time.perf_counter() - t0_1_start
    n_processed_frames = len(preprocessed_frames)

    # Breakdown Stage 1.5 Calibration
    import torch
    from sahi import AutoDetectionModel
    model_path = config.get('object_detection', {}).get('model_path', 'best.pt')
    for fallback in ['best.pt', 'models/best.pt', 'yolov8n.pt', 'models/yolov8n.pt']:
        if os.path.exists(fallback):
            model_path = fallback
            break

    device_req = str(config.get('object_detection', {}).get('device', 'cuda' if torch.cuda.is_available() else 'cpu')).strip()
    if device_req.lower() == 'auto' or device_req.lower().startswith('cuda'):
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    else:
        device = device_req
    
    t_mod_start = time.perf_counter()
    calib_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        model_path=model_path,
        confidence_threshold=0.08,
        device=device
    )
    t_mod_load = time.perf_counter() - t_mod_start

    n_frames = len(preprocessed_frames)
    keyframe_indices = sorted(list(set([0, n_frames // 4, n_frames // 2, (3 * n_frames) // 4, max(0, n_frames - 1)])))

    t_sahi_pass = 0.0
    t_tile_pass = 0.0
    t_nms_pass = 0.0

    enable_upscale_pass = config.get('zone_calibration', {}).get('enable_upscale_pass', False)
    per_frame_boxes = []
    for fi in keyframe_indices:
        pf = preprocessed_frames[fi]
        # (a) SAHI small tile pass (192px)
        tsa = time.perf_counter()
        p1 = _sahi_detect(pf.color_frame, calib_model, 0.08, slice_size=192, overlap=0.45)
        t_sahi_pass += (time.perf_counter() - tsa)

        # (b) Optional 2x2 Tiled upscale pass
        p2 = []
        if enable_upscale_pass:
            ttu = time.perf_counter()
            p2 = _tiled_upscale_detect(pf.color_frame, calib_model, 0.08, 2, 2, 2.0)
            t_tile_pass += (time.perf_counter() - ttu)

        # (c) NMS
        tnm = time.perf_counter()
        boxes = _nms(p1 + p2, iou_thresh=0.35)
        t_nms_pass += (time.perf_counter() - tnm)
        per_frame_boxes.append(boxes)

    # (d) Aggregation & suppression
    tag = time.perf_counter()
    stable = _aggregate_multiframe(per_frame_boxes, cluster_dist=35.0, iou_thresh=0.20, min_frame_fraction=0.15)
    t_aggregate_pass = time.perf_counter() - tag

    # Baseline motion calculation
    t_bm = time.perf_counter()
    mog2 = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)
    frame_motion_masks = []
    for pf in preprocessed_frames:
        mask = mog2.apply(pf.gray_frame)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        frame_motion_masks.append(mask)
    t_baseline_motion = time.perf_counter() - t_bm

    # Run actual Stage 1.5 function
    def calib_stream():
        for pf in preprocessed_frames:
            yield pf
    zone_map: ZoneMap = calibrate_zones_stage(calib_stream(), config)
    t1_5_total_time = time.perf_counter() - t0_1_start

    # Measure Stage 2A Motion Detection
    t2a_start = time.perf_counter()
    def stream_2a_in():
        for pf in preprocessed_frames:
            yield pf
    s2a = motion_detection_stage(stream_2a_in(), zone_map, config['motion_detection'], config.get('debug'))
    motion_results = []
    for mf in s2a:
        motion_results.append(mf)
    t2a_total_time = time.perf_counter() - t2a_start

    # Measure Stage 2B Object Detection
    t2b_start = time.perf_counter()
    def stream_2b_in():
        for pf in preprocessed_frames:
            yield pf
    def stream_2b_motion_in():
        for mf in motion_results:
            yield mf
    s2b = object_detection_stage(stream_2b_in(), stream_2b_motion_in(), config['object_detection'], config.get('debug'))
    roi_results = []
    for rf in s2b:
        roi_results.append(rf)
    t2b_total_time = time.perf_counter() - t2b_start

    # Measure Stage 3 Tracking Fusion
    t3_start = time.perf_counter()
    def stream_3_motion_in():
        for mf in motion_results:
            yield mf
    def stream_3_roi_in():
        for rf in roi_results:
            yield rf
    s3 = tracking_fusion_stage(stream_3_motion_in(), stream_3_roi_in(), zone_map, config, config.get('debug'))
    fusion_results = []
    for ff in s3:
        fusion_results.append(ff)
    t3_total_time = time.perf_counter() - t3_start

    # Measure Stage 4 Event Segmentation
    t4_start = time.perf_counter()
    def stream_4_in():
        for ff in fusion_results:
            yield ff
    s4 = event_segmentation_stage(stream_4_in(), video_path, config['event_segmentation'], config.get('debug'), zone_map=zone_map)
    events_segmented = []
    for ev in s4:
        events_segmented.append(ev)
    t4_total_time = time.perf_counter() - t4_start

    # Measure Stage 5 Output Generation
    t5_start = time.perf_counter()
    def stream_5_heat_in():
        for mf in motion_results:
            yield mf
    def stream_5_fusion_in():
        for ff in fusion_results:
            yield ff
    def stream_5_events_in():
        for ev in events_segmented:
            yield ev
    var, events, incidents = output_stage(stream_5_heat_in(), stream_5_fusion_in(), stream_5_events_in(), zone_map, config, video_path=video_path)
    t5_total_time = time.perf_counter() - t5_start

    # Measure End-to-End Real Pipeline Run
    t_pipeline_total = t0_1_time + t1_5_total_time + t2a_total_time + t2b_total_time + t3_total_time + t4_total_time + t5_total_time

    # SAHI Slice Counts
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    slice_res_2b = slice_image(test_img, slice_height=512, slice_width=512, overlap_height_ratio=0.2, overlap_width_ratio=0.2)
    n_slices_2b = len(slice_res_2b.images) if hasattr(slice_res_2b, 'images') else 2

    slice_res_calib_sahi = slice_image(test_img, slice_height=192, slice_width=192, overlap_height_ratio=0.45, overlap_width_ratio=0.45)
    n_slices_calib_sahi = len(slice_res_calib_sahi.images) if hasattr(slice_res_calib_sahi, 'images') else 16

    # ---------------------------------------------------------
    # PRINT RESULTS
    # ---------------------------------------------------------
    print("\n--- 1. FRAME SAMPLING & INGESTION TELEMETRY ---")
    print(f"  Source Video: {video_path} ({native_w}x{native_h})")
    print(f"  Source Video Native FPS: {native_fps:.1f} FPS")
    print(f"  Source Video Native Frames: {native_fc} frames ({native_fc/native_fps:.2f}s total recording)")
    print(f"  Configured target_fps: {target_fps} FPS (Interval: Every {int(round(native_fps/target_fps))}th frame)")
    print(f"  Sampled Frames Processed: {n_processed_frames} frames ({n_processed_frames/native_fc*100:.1f}% of native footage)")

    print("\n--- 2. PER-STAGE TIMING BREAKDOWN ---")
    stages_data = [
        ("Stage 0 + Stage 1: Ingestion & Preprocessing (CLAHE + Stabilization)", t0_1_time, t0_1_time / n_processed_frames * 1000, "ms/frame"),
        ("Stage 1.5: Zone Calibration (One-Time Keyframe Hierarchy)", t1_5_total_time, t1_5_total_time / len(keyframe_indices) * 1000, "ms/keyframe"),
        ("Stage 2A: Per-Zone Motion Estimation (MOG2)", t2a_total_time, t2a_total_time / n_processed_frames * 1000, "ms/frame"),
        ("Stage 2B: ROI Object Detection (YOLOv8 + SAHI)", t2b_total_time, t2b_total_time / n_processed_frames * 1000, "ms/frame"),
        ("Stage 3: Tracking & Anomaly Signal Fusion", t3_total_time, t3_total_time / n_processed_frames * 1000, "ms/frame"),
        ("Stage 4: Event Segmentation & Unified Clip Cutting", t4_total_time, t4_total_time, "ms/stage"),
        ("Stage 5: Output Generation (DB, Heatmaps, Capsules)", t5_total_time, t5_total_time, "ms/stage"),
    ]

    print(f"{'Pipeline Stage':<68} | {'Total Time (s)':<14} | {'Per-Frame Latency':<20} | {'% of Runtime':<12}")
    print("-" * 120)
    for name, total_t, per_f, unit in stages_data:
        pct = (total_t / t_pipeline_total) * 100
        print(f"{name:<68} | {total_t:>12.2f}s | {per_f:>10.1f} {unit:<8} | {pct:>10.1f}%")
    print("-" * 120)
    print(f"{'TOTAL PIPELINE RUNTIME':<68} | {t_pipeline_total:>12.2f}s | {'':<20} | {100.0:>10.1f}%\n")

    print("--- 3. ZONE CALIBRATION SPECIFICS (STAGE 1.5 BREAKDOWN) ---")
    print(f"  Configured Calibration Window: {config.get('zone_calibration',{}).get('calibration_window_percent')*100:.0f}% ({config.get('zone_calibration',{}).get('calibration_window_frames')} frames)")
    print(f"  Keyframes Analyzed: {len(keyframe_indices)} keyframes (Indices: {keyframe_indices})")
    print(f"  (a) SAHI 192px Small-Tile Pass (45% overlap): {t_sahi_pass:.2f}s ({t_sahi_pass/len(keyframe_indices):.2f}s/keyframe, {n_slices_calib_sahi} tiles/keyframe)")
    print(f"  (b) 2x2 Grid Quadrant 2x-Upscale Pass: {t_tile_pass:.2f}s ({t_tile_pass/len(keyframe_indices):.2f}s/keyframe, 4 quadrants/keyframe)")
    print(f"  (c) Intra-Frame NMS Filtering: {t_nms_pass*1000:.1f}ms")
    print(f"  (d) Multi-Frame Centroid Proximity & Cluster Fusion: {t_aggregate_pass*1000:.1f}ms")
    print(f"  (e) MOG2 Initial Seating Baseline Computation: {t_baseline_motion:.2f}s")
    print(f"  Stage 1.5 Calibration Total Time: {t1_5_total_time:.2f}s (One-time startup cost)")

    gpu_info = f" ({torch.cuda.get_device_name(0)})" if 'cuda' in str(device).lower() and torch.cuda.is_available() else ""
    print(f"  Inference Device: {device.upper()}{gpu_info}")
    print(f"  Model Weights: {model_path}")
    print(f"  SAHI Slicing Dimensions: {config.get('object_detection',{}).get('sahi',{}).get('slice_height')}x{config.get('object_detection',{}).get('sahi',{}).get('slice_width')} px")
    print(f"  SAHI Overlap: {config.get('object_detection',{}).get('sahi',{}).get('overlap_height_ratio')*100:.0f}% height / {config.get('object_detection',{}).get('sahi',{}).get('overlap_width_ratio')*100:.0f}% width")
    print(f"  Slices Generated Per Frame: {n_slices_2b} slices (on 640x480 frame)")
    print(f"  Stage 2B Average Time Per Frame: {t2b_total_time/n_processed_frames*1000:.1f} ms/frame")
    print(f"  Stage 2B Cumulative Time: {t2b_total_time:.2f}s ({t2b_total_time/t_pipeline_total*100:.1f}% of total runtime)")

    print("\n--- 5. OTHER OVERHEAD & I/O PROFILE ---")
    print(f"  Debug Image Saving Enabled: {config.get('debug',{}).get('save_images')}")
    print(f"  Debug Save Rate: Every {config.get('debug',{}).get('save_every_n_frames')} frame(s) (Outputs to: {config.get('debug',{}).get('output_dir')})")
    print(f"  Preprocessing CLAHE Grid: {grid}, Clip Limit: {clip_limit}")
    print(f"  Frame Stabilization Enabled: {enable_stab}")
    print(f"  FFmpeg Clip Cutting & Encoding (Stage 4): {t4_total_time:.2f}s")
    print(f"  Evidence Capsule Snapshots & DB (Stage 5): {t5_total_time:.2f}s")
    print("================================================================================\n")

if __name__ == '__main__':
    run_diagnostic()
