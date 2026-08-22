import os
import yaml
from utils.cleanup import clean_output_directory
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_1_5_zone_calibration import calibrate_zones_stage, ZoneMap

def test_stage_1_5():
    print("=== Testing Stage 1.5 Zone Calibration ===")
    
    # Wipe outputs directory cleanly before test
    clean_output_directory("outputs")
    
    config_path = "config/config.yaml"
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    video_path = config["video"]["input_path"]
    if not os.path.exists(video_path):
        print(f"Input video missing: {video_path}")
        return

    # Ingestion & Preprocessing streams
    stream_0 = video_ingestion_stage(
        video_path,
        skip_initial_frames=config["video"]["skip_initial_frames"],
        frame_sample_rate=config["video"]["frame_sample_rate"],
        max_consecutive_corrupt_frames=config["video"]["max_consecutive_corrupt_frames"],
        target_fps=config["video"]["sampling"]["target_fps"],
        debug_cfg=config.get("debug")
    )

    stream_1 = preprocess_stage(
        stream_0,
        resize_dims=(config["preprocessing"]["resize_width"], config["preprocessing"]["resize_height"]),
        clahe_clip_limit=config["preprocessing"]["clahe_clip_limit"],
        clahe_tile_grid_size=tuple(config["preprocessing"]["clahe_tile_grid_size"]),
        brightness_jump_threshold=config["preprocessing"]["brightness_jump_threshold"],
        enable_stabilization=config["preprocessing"]["enable_stabilization"],
        debug_cfg=config.get("debug")
    )

    # Run Stage 1.5 Zone Calibration
    zone_map: ZoneMap = calibrate_zones_stage(stream_1, config)

    print("\n--- Calibration Results ---")
    print(f"Total Locked Zones: {len(zone_map.zones)}")
    for z in zone_map.zones:
        print(f"  [{z.name}] ID: {z.zone_id} | Polygon: {z.polygon} | Baseline Median: {z.baseline_median_motion:.6f} | Baseline Var: {z.baseline_variance:.6f}")

    # Assertions
    json_path = config["zone_calibration"]["zone_map_path"]
    preview_path = config["zone_calibration"]["preview_path"]

    assert os.path.exists(json_path), f"Missing locked zone map JSON at {json_path}"
    assert os.path.exists(preview_path), f"Missing calibration preview image at {preview_path}"
    assert len(zone_map.zones) > 0, "No zones were generated during calibration!"

    print(f"\nSUCCESS: Stage 1.5 Zone Calibration verified!")
    print(f"Locked Zone Map: {json_path}")
    print(f"Calibration Preview: {preview_path}")

if __name__ == "__main__":
    test_stage_1_5()
