import yaml
import numpy as np
import cv2
import itertools
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_1_5_zone_calibration import calibrate_zones_stage, ZoneMap
from stages.stage_2a_motion import motion_detection_stage, MotionFrame

def test_stage_2a():
    print("--- Starting Stage 2A Per-Zone Motion Test ---")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    config['motion_detection']['warmup_frames'] = 2
    
    video_path = config['video']['input_path']
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
    
    stream_0 = video_ingestion_stage(video_path, skip, sample_rate, max_corrupt, target_fps)
    stream_1 = preprocess_stage(stream_0, (resize_w, resize_h), clip_limit, grid, brightness_thresh, enable_stab)
    
    stream_1_calib, stream_1_run = itertools.tee(stream_1, 2)
    zone_map: ZoneMap = calibrate_zones_stage(stream_1_calib, config)
    
    stream_2a = motion_detection_stage(stream_1_run, zone_map, config['motion_detection'])
    
    count = 0
    try:
        for m_frame in stream_2a:
            count += 1
            assert isinstance(m_frame, MotionFrame), "Not a MotionFrame"
            assert isinstance(m_frame.motion_mask, np.ndarray), "Mask not an ndarray"
            assert len(m_frame.zone_results) == len(zone_map.zones), "Zone results mismatch"
            
            if count >= 10:
                break
                
    except AssertionError as e:
        print(f"Test Failed: {e}")
    except Exception as e:
        print(f"Unexpected Exception: {e}")
    else:
        print("Test Passed: Stage 2A per-zone motion verifications succeeded.")

if __name__ == '__main__':
    test_stage_2a()
