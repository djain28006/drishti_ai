import yaml
import itertools
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking import tracking_stage
from stages.stage_4_event import event_segmentation_stage
from stages.stage_5_output import output_stage, get_events

def test_stage_5():
    print("--- Starting Stage 5 Output Test ---")
    
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    import torch
    config['object_detection']['device'] = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    video_path = config['video']['input_path']
    skip = config['video']['skip_initial_frames']
    sample_rate = config['video']['frame_sample_rate']
    max_corrupt = config['video']['max_consecutive_corrupt_frames']
    target_fps = config['video'].get('sampling', {}).get('target_fps', 0)
    
    resize_w = config['preprocessing']['resize_width']
    resize_h = config['preprocessing']['resize_height']
    clip_limit = config['preprocessing']['clahe_clip_limit']
    grid = tuple(config['preprocessing']['clahe_tile_grid_size'])
    brightness_thresh = config['preprocessing']['brightness_jump_threshold']
    enable_stab = config['preprocessing']['enable_stabilization']
    
    stream_0 = video_ingestion_stage(video_path, skip, sample_rate, max_corrupt, target_fps, config.get('debug'))
    stream_1 = preprocess_stage(
        stream_0, (resize_w, resize_h), clip_limit, grid, brightness_thresh, enable_stab, config.get('debug')
    )
    
    stream_1a, stream_1b = itertools.tee(stream_1, 2)
    stream_2a = motion_detection_stage(stream_1a, config['motion_detection'], config.get('debug'))
    
    # Tee stream_2a to give a copy to stage 5 (heatmap)
    stream_2a_track, stream_2a_heat = itertools.tee(stream_2a, 2)
    
    stream_2b = object_detection_stage(stream_1b, config['object_detection'], config.get('debug'))
    
    stream_3 = tracking_stage(stream_2a_track, stream_2b, config, config.get('debug'))
    
    stream_4 = event_segmentation_stage(stream_3, video_path, config['event_segmentation'], config.get('debug'))
    
    # Run output stage
    var, events = output_stage(stream_2a_heat, stream_4, config)
    
    print(f"\nHeatmap Variance: {var:.2f}")
    
    # Query database
    db_path = config.get('output', {}).get('sqlite_db_path', 'outputs/events.db')
    queried = get_events(db_path, class_name="person")
    
    print(f"SQLite Row Count for 'person': {len(queried)}")
    if len(queried) > 0:
        sample = queried[0]
        print(f"Sample Query Result: {sample}")
        
    print("\nTest Passed: Stage 5 completed successfully.")

if __name__ == '__main__':
    test_stage_5()
