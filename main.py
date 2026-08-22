import argparse
import yaml
import os
import sys
import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass
import itertools
from utils.logger import StageLogger
from utils.cleanup import clean_output_directory
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_1_5_zone_calibration import calibrate_zones_stage, ZoneMap
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking_fusion import tracking_fusion_stage
from stages.stage_4_event_segmentation import event_segmentation_stage
from stages.stage_5_output import output_stage

logger = StageLogger("MAIN")

def validate_config(config: dict):
    """Fails fast if required config keys are missing."""
    try:
        assert 'sampling' in config['video'] and 'target_fps' in config['video']['sampling'], "Missing video.sampling.target_fps"
        assert 'classes_of_interest' in config['object_detection'], "Missing object_detection.classes_of_interest"
        assert 'zone_calibration' in config, "Missing zone_calibration section"
        
        ev = config.get('event_segmentation')
        assert ev is not None, "Missing event_segmentation section"
        for key in ['start_threshold', 'start_n_frames', 'end_threshold', 'end_m_frames']:
            assert key in ev, f"Missing event_segmentation.{key}"
            
        hm = config.get('heatmap')
        assert hm is not None, "Missing heatmap section"
        for key in ['colormap', 'alpha', 'output_path']:
            assert key in hm, f"Missing heatmap.{key}"
            
        out = config.get('output')
        assert out is not None, "Missing output section"
        for key in ['timeline_json_path', 'sqlite_db_path']:
            assert key in out, f"Missing output.{key}"
            
    except AssertionError as e:
        logger.error(f"Config Validation Failed: {e}")
        sys.exit(1)

def progress_wrapper(stream):
    """Wraps a stream to print periodic progress."""
    for idx, item in enumerate(stream):
        if idx > 0 and idx % 20 == 0:
            logger.info(f"Pipeline running... Processed {idx} sampled frames")
        yield item

def run_pipeline(config_path: str, input_video: str, debug_override: bool, clean_first: bool = False, device_override: str = None):
    if clean_first:
        logger.info("Clean slate requested (--clean). Wiping old output artifacts...")
        clean_output_directory("outputs")

    with open(config_path, 'r', encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    if input_video:
        config['video']['input_path'] = input_video

    if device_override:
        if 'object_detection' not in config:
            config['object_detection'] = {}
        config['object_detection']['device'] = device_override
        
    if debug_override:
        if 'debug' not in config:
            config['debug'] = {}
        config['debug']['enabled'] = True
        
    validate_config(config)
    
    video_path = config['video']['input_path']
    if not os.path.exists(video_path):
        logger.error(f"Input video not found: {video_path}")
        sys.exit(1)

    import torch
    dev_target = str(config.get('object_detection', {}).get('device', 'auto')).strip()
    if dev_target.lower() in ('auto', 'cuda', 'cuda:0') and torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"[HARDWARE ACCELERATION] Running on GPU: {gpu_name} (CUDA {torch.version.cuda}, PyTorch {torch.__version__})")
    elif torch.cuda.is_available():
        logger.info(f"[HARDWARE] Device set to: {dev_target} (GPU available: {torch.cuda.get_device_name(0)})")
    else:
        logger.info(f"[HARDWARE] Device set to: {dev_target} (CPU execution)")
        
    logger.info(f"Starting 7-Stage Pipeline for video: {video_path}")
    
    try:
        # Configuration extractions
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
        
        # STAGE 0: Video Ingestion
        stream_0 = video_ingestion_stage(video_path, skip, sample_rate, max_corrupt, target_fps, config.get('debug'))
        
        # STAGE 1: Preprocessing
        stream_1 = preprocess_stage(
            stream_0, (resize_w, resize_h), clip_limit, grid, brightness_thresh, enable_stab, config.get('debug')
        )
        
        # Split Stream 1 into Calibration stream and Main processing stream
        stream_1_calib, stream_1_run = itertools.tee(stream_1, 2)

        # STAGE 1.5: Zone Calibration (runs once to lock ZoneMap before per-frame processing)
        zone_map: ZoneMap = calibrate_zones_stage(stream_1_calib, config)
        
        # Split Main Stream 1 into Stage 2A motion and Stage 2B object detection
        stream_1a, stream_1b = itertools.tee(stream_1_run, 2)
        
        # STAGE 2A: Per-Zone Motion Detection
        # target_fps passed so MOG2 history scales to a fixed real-world time window.
        stream_2a = motion_detection_stage(stream_1a, zone_map, config['motion_detection'], config.get('debug'), target_fps=target_fps)
        
        # Split Stage 2A into Object Detection ROI control, Tracking Fusion, and Heatmap Accumulation
        stream_2a_obj, stream_2a_track, stream_2a_heat = itertools.tee(stream_2a, 3)
        
        # STAGE 2B: ROI-Restricted Object Detection
        stream_2b = object_detection_stage(stream_1b, stream_2a_obj, config['object_detection'], config.get('debug'))
        
        # STAGE 3: Tracking & Signal Fusion
        stream_3 = tracking_fusion_stage(stream_2a_track, stream_2b, zone_map, config, config.get('debug'))

        # Split Stage 3 stream — one copy to Stage 4 (event segmentation), one to Stage 5 (activity accumulation)
        stream_3_event, stream_3_output = itertools.tee(stream_3, 2)

        # STAGE 4: Event Segmentation & Room-Wide Suppression Check
        stream_4 = event_segmentation_stage(stream_3_event, video_path, config['event_segmentation'], config.get('debug'), zone_map=zone_map)
        stream_4_prog = progress_wrapper(stream_4)

        # STAGE 5: Dual Heatmap, SQLite DB, Incident Fusion & Forensic Capsules
        var, events, incidents = output_stage(stream_2a_heat, stream_3_output, stream_4_prog, zone_map, config, video_path=video_path)
        
        # ── Final Validation Report
        det_zones  = [z for z in zone_map.zones if not z.is_estimated]
        est_zones  = [z for z in zone_map.zones if z.is_estimated]
        events_by_zone: dict = {}
        for ev in events:
            events_by_zone.setdefault(ev.zone_id, []).append(ev)

        logger.info("\n" + "=" * 57)
        logger.info("FINAL FORENSIC PIPELINE REPORT")
        logger.info("=" * 57)

        logger.info("\n[CALIBRATION & PHYSICAL MAP]")
        logger.info(f"  Total zones          : {len(zone_map.zones)}")
        logger.info(f"  DETECTED zones       : {len(det_zones)}  (YOLO confirmed)")
        logger.info(f"  ESTIMATED zones      : {len(est_zones)}  (spatial-gap estimated)")
        for z in zone_map.zones:
            tag = "EST" if z.is_estimated else f"calib={int(z.zone_confidence*100)}%"
            logger.info(f"    {z.name} -> {z.location_desc} [{tag}] center={z.center}")

        logger.info("\n[PRIORITIZED INCIDENTS & EVIDENCE CAPSULES]")
        logger.info(f"  Total Incidents Created : {len(incidents)}")
        for inc in incidents:
            logger.info(f"    [{inc.risk_level}] Incident {inc.incident_id} | Score: {inc.risk_score}/100 | "
                        f"{inc.primary_class.upper()} @ {inc.location_desc} ({inc.duration_seconds:.2f}s)")

        logger.info("\n[EVENTS SEGMENTATION]")
        logger.info(f"  Total events segmented : {len(events)}")
        for z in zone_map.zones:
            evs = events_by_zone.get(z.zone_id, [])
            if evs:
                for ev in evs:
                    room_tag = " [ROOM-WIDE]" if getattr(ev, 'is_room_wide', False) else ""
                    logger.info(f"    {z.name} Zone {z.zone_id}{room_tag}: Event {ev.event_id} "
                                f"@ {ev.start_timestamp:.2f}s->{ev.end_timestamp:.2f}s "
                                f"motionAvg={ev.avg_motion_score:.4f}")
            else:
                logger.info(f"    {z.name} Zone {z.zone_id}: 0 events (0% activity — zone active, no anomaly)")

        logger.info("\n[OUTPUTS]")
        logger.info(f"  Zone Map JSON        : {config['zone_calibration']['zone_map_path']}")
        logger.info(f"  Calibration Preview  : {config['zone_calibration']['preview_path']}")
        logger.info(f"  Raw Motion Heatmap   : {config['heatmap']['output_path']} (var={var:.2f})")
        logger.info(f"  Student Activity Map : {config['heatmap']['student_heatmap_path']}")
        logger.info(f"  Annotated Frame      : {config['heatmap']['annotated_frame_path']}")
        logger.info(f"  Timeline JSON        : {config['output']['timeline_json_path']}")
        logger.info(f"  SQLite DB            : {config['output']['sqlite_db_path']}")
        logger.info(f"  Event Clips          : outputs/events/ ({len(events)} clips)")

        logger.info("\n[STATUS]  All pipeline stages completed successfully.")
        logger.info("=" * 57 + "\n")

        # STAGE 6: Forensic PDF Report
        report_cfg = config.get('report', {})
        if report_cfg.get('enabled', True):
            try:
                from report.pdf_report import generate_forensic_report
                pdf_path = generate_forensic_report(
                    incidents_path  = 'outputs/incidents.json',
                    capsules_dir    = config.get('evidence_capsule', {}).get('output_dir', 'outputs/capsules'),
                    zone_map_path   = config['zone_calibration']['zone_map_path'],
                    timeline_path   = config['output']['timeline_json_path'],
                    heatmap_student = config['heatmap']['student_heatmap_path'],
                    heatmap_raw     = config['heatmap']['output_path'],
                    annotated_frame = config['heatmap']['annotated_frame_path'],
                    output_pdf_path = report_cfg.get('output_path', 'outputs/forensic_report.pdf'),
                    video_path      = video_path,
                    config          = config,
                )
                size_kb = os.path.getsize(pdf_path) // 1024
                logger.info(f"[STAGE 6] Forensic PDF report saved: {pdf_path} ({size_kb} KB)")
            except Exception as e:
                logger.warning(f"[STAGE 6] PDF report generation failed (non-fatal): {e}")

        
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Exam Cheating Detection Pipeline")
    parser.add_argument("--input", type=str, help="Path to input video file (overrides config)")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Path to configuration YAML")
    parser.add_argument("--device", type=str, default=None, choices=["cuda", "cuda:0", "cpu", "auto"], help="Inference device: cuda, cpu, or auto (overrides config)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (overrides config)")
    parser.add_argument("--clean", action="store_true", help="Wipe all previous outputs before running pipeline")
    
    args = parser.parse_args()
    run_pipeline(args.config, args.input, args.debug, clean_first=args.clean, device_override=args.device)

if __name__ == "__main__":
    main()
