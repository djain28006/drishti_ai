"""
scripts/benchmark_fps_tradeoff.py
---------------------------------
Systematically benchmarks target_fps in [2, 3, 4, 5] on test2.mp4.
Collects:
- Total frames processed
- Total runtime (s)
- Raw candidate triggers
- Total object detections in Stage 2B (by class: peeking, phone, chit, hand, supplement-passing)
- Active zones triggered in Stage 2A
- Final segmented incidents
- Calibrated zone count and average confidence
"""

import sys
import os
import time
import json
import yaml
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_1_5_zone_calibration import calibrate_zones_stage, ZoneMap
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking_fusion import tracking_fusion_stage
from stages.stage_4_event_segmentation import event_segmentation_stage
from stages.stage_5_output import output_stage

def benchmark_fps_values(video_path="test2.mp4", fps_list=[2, 3, 4, 5]):
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        base_cfg = yaml.safe_load(f)

    results = []

    for tfps in fps_list:
        print(f"\n================================================================================")
        print(f"               RUNNING FULL BENCHMARK FOR target_fps = {tfps} FPS               ")
        print(f"================================================================================")
        
        cfg = json.loads(json.dumps(base_cfg)) # deep copy
        cfg['video']['sampling']['target_fps'] = tfps
        cfg['video']['input_path'] = video_path
        # Ensure fast debug I/O is used
        cfg['debug']['save_every_n_frames'] = 30
        cfg['preprocessing']['enable_stabilization'] = False
        cfg['zone_calibration']['enable_upscale_pass'] = False

        t_start = time.perf_counter()

        # Stage 0 & 1
        s0 = video_ingestion_stage(
            video_path,
            cfg['video']['skip_initial_frames'],
            cfg['video']['frame_sample_rate'],
            cfg['video']['max_consecutive_corrupt_frames'],
            tfps,
            cfg.get('debug')
        )
        s1 = preprocess_stage(
            s0,
            (cfg['preprocessing']['resize_width'], cfg['preprocessing']['resize_height']),
            cfg['preprocessing']['clahe_clip_limit'],
            tuple(cfg['preprocessing']['clahe_tile_grid_size']),
            cfg['preprocessing']['brightness_jump_threshold'],
            cfg['preprocessing']['enable_stabilization'],
            cfg.get('debug')
        )

        frames = []
        for f in s1:
            frames.append(f)
        n_frames = len(frames)

        # Stage 1.5 Calibration
        t_calib_start = time.perf_counter()
        def calib_stream():
            for f in frames:
                yield f
        zone_map: ZoneMap = calibrate_zones_stage(calib_stream(), cfg)
        t_calib = time.perf_counter() - t_calib_start

        # Stage 2A Motion
        t_runtime_start = time.perf_counter()
        def s2a_in():
            for f in frames:
                yield f
        s2a = motion_detection_stage(s2a_in(), zone_map, cfg['motion_detection'], cfg.get('debug'))
        motion_frames = []
        for mf in s2a:
            motion_frames.append(mf)

        # Count active motion zones across all frames
        total_active_motion_evals = sum(len(mf.zone_results) for mf in motion_frames)
        total_motion_active_count = sum(sum(1 for z in mf.zone_results if z.motion_score > 0.0001 or z.baseline_deviation > 0 or z.boundary_crossing) for mf in motion_frames)

        # Stage 2B Object Detection
        def s2b_in_frames():
            for f in frames:
                yield f
        def s2b_in_motion():
            for mf in motion_frames:
                yield mf
        s2b = object_detection_stage(s2b_in_frames(), s2b_in_motion(), cfg['object_detection'], cfg.get('debug'))
        roi_frames = []
        for rf in s2b:
            roi_frames.append(rf)

        # Count detections by class
        det_class_counts = {}
        total_detections = 0
        for rf in roi_frames:
            for det in rf.detections:
                cls_name = det.class_name
                det_class_counts[cls_name] = det_class_counts.get(cls_name, 0) + 1
                total_detections += 1

        # Stage 3 Tracking Fusion
        def s3_in_motion():
            for mf in motion_frames:
                yield mf
        def s3_in_roi():
            for rf in roi_frames:
                yield rf
        s3 = tracking_fusion_stage(s3_in_motion(), s3_in_roi(), zone_map, cfg, cfg.get('debug'))
        fusion_frames = []
        for ff in s3:
            fusion_frames.append(ff)

        # Stage 4 Event Segmentation
        def s4_in():
            for ff in fusion_frames:
                yield ff
        s4 = event_segmentation_stage(s4_in(), video_path, cfg['event_segmentation'], cfg.get('debug'), zone_map=zone_map)
        events = [ev for ev in s4]
        
        # Stage 5 Output Generation
        def s5_heat():
            for mf in motion_frames:
                yield mf
        def s5_fusion():
            for ff in fusion_frames:
                yield ff
        def s5_events():
            for ev in events:
                yield ev
        var, final_events, incidents = output_stage(s5_heat(), s5_fusion(), s5_events(), zone_map, cfg, video_path=video_path)
        
        t_end = time.perf_counter()
        t_total = t_end - t_start
        t_runtime = t_end - t_runtime_start

        avg_conf = np.mean([z.zone_confidence for z in zone_map.zones]) if zone_map.zones else 0.0

        results.append({
            'target_fps': tfps,
            'processed_frames': n_frames,
            'total_time_s': round(t_total, 2),
            'calib_time_s': round(t_calib, 2),
            'runtime_time_s': round(t_runtime, 2),
            'per_frame_ms': round((t_runtime / max(1, n_frames)) * 1000, 1),
            'zones_count': len(zone_map.zones),
            'zone_avg_conf': round(float(avg_conf), 3),
            'motion_active_triggers': total_motion_active_count,
            'total_object_detections': total_detections,
            'detections_by_class': det_class_counts,
            'events_count': len(events),
            'incidents_count': len(incidents) if incidents is not None else len(events)
        })

    print("\n\n==========================================================================================")
    print("                 SYSTEMATIC FPS TRADEOFF BENCHMARK REPORT (test2.mp4)                     ")
    print("==========================================================================================")
    print(f"{'Target FPS':<12} | {'Frames':<8} | {'Total Time':<12} | {'Per-Frame':<12} | {'Motion Triggers':<16} | {'Object Detections':<18} | {'Incidents':<10}")
    print("-" * 100)
    for r in results:
        print(f"{r['target_fps']:<12} | {r['processed_frames']:<8} | {r['total_time_s']:>10.2f}s | {r['per_frame_ms']:>9.1f}ms | {r['motion_active_triggers']:>16} | {r['total_object_detections']:>18} | {r['incidents_count']:>10}")
    print("-" * 100)
    
    print("\nDETAILED DETECTION BREAKDOWN BY CLASS:")
    for r in results:
        print(f"  target_fps={r['target_fps']}: Total={r['total_object_detections']} detections -> {r['detections_by_class']}")

    # Save to JSON for analysis
    with open('outputs/fps_benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nSaved benchmark results to outputs/fps_benchmark_results.json")

if __name__ == '__main__':
    benchmark_fps_values()
