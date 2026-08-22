import yaml
import itertools
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_1_5_zone_calibration import calibrate_zones_stage
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking_fusion import tracking_fusion_stage, FusedTrackFrame

def test_stage_3_tracking_fusion():
    print("--- Starting Stage 3 Tracking & Fusion Test ---")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
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
    zone_map = calibrate_zones_stage(stream_1_calib, config)
    
    stream_1a, stream_1b = itertools.tee(stream_1_run, 2)
    stream_2a = motion_detection_stage(stream_1a, zone_map, config['motion_detection'])
    stream_2a_obj, stream_2a_track = itertools.tee(stream_2a, 2)
    
    stream_2b = object_detection_stage(stream_1b, stream_2a_obj, config['object_detection'])
    
    stream_3 = tracking_fusion_stage(stream_2a_track, stream_2b, zone_map, config)
    
    count = 0
    try:
        for f_frame in stream_3:
            count += 1
            assert isinstance(f_frame, FusedTrackFrame), "Not a FusedTrackFrame"
            assert len(f_frame.records) == len(zone_map.zones), "Record count mismatch"
            if count >= 10:
                break
    except Exception as e:
        print(f"Test Failed: {e}")
    else:
        print("Test Passed: Stage 3 Tracking Fusion verifications succeeded.")

if __name__ == '__main__':
    test_stage_3_tracking_fusion()
