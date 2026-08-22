import yaml
import itertools
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking import tracking_stage
from stages.stage_4_event import event_segmentation_stage

def test_stage_4():
    print("--- Starting Stage 4 Event Segmentation Test ---")
    
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
    stream_2b = object_detection_stage(stream_1b, config['object_detection'], config.get('debug'))
    
    stream_3 = tracking_stage(stream_2a, stream_2b, config, config.get('debug'))
    
    raw_scores = []
    def intercept_stream_3(s3):
        for t_frame in s3:
            for r in t_frame.records:
                raw_scores.append(r['motion_score'])
            yield t_frame
            
    stream_4 = event_segmentation_stage(intercept_stream_3(stream_3), video_path, config['event_segmentation'], config.get('debug'))
    
    all_events = []
    
    try:
        for events in stream_4:
            for ev in events:
                all_events.append(ev)
                print(f"New Event Detected! ID: {ev.event_id}, Track: {ev.track_id}, Start: {ev.start_timestamp:.2f}s, End: {ev.end_timestamp:.2f}s, Dur: {ev.duration_seconds:.2f}s, AvgMotion: {ev.avg_motion_score:.3f}")
                print(f"  -> Clip saved to: {ev.clip_path}")
                
    except AssertionError as e:
        print(f"Test Failed (Assertion): {e}")
    except Exception as e:
        print(f"Unexpected Exception: {e}")
    else:
        print("\n--- Event Summary ---")
        print(f"Total events found: {len(all_events)}")
        for i, ev in enumerate(all_events):
            print(f"[{i+1}] Track {ev.track_id} | Zone {ev.zone_id} | Class '{ev.class_name}' | {ev.start_timestamp:.2f}s -> {ev.end_timestamp:.2f}s (Dur: {ev.duration_seconds:.2f}s)")
            
        print("\n--- Raw Motion Scores ---")
        print(f"Full List: {raw_scores}")
        if raw_scores:
            print(f"Min: {min(raw_scores):.4f}, Max: {max(raw_scores):.4f}, Mean: {sum(raw_scores)/len(raw_scores):.4f}")
            
        print("\nTest Passed: Stage 4 completed successfully.")

if __name__ == '__main__':
    test_stage_4()
