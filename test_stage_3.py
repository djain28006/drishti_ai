import yaml
import os
import json
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking import tracking_stage, TrackingFrame
from utils.logger import StageLogger

logger = StageLogger("TEST3")

def download_yolov8n():
    os.makedirs("models", exist_ok=True)
    model_path = "models/yolov8n.pt"
    if not os.path.exists(model_path):
        from ultralytics import YOLO
        YOLO("yolov8n.pt") 
        if os.path.exists("yolov8n.pt"):
            os.rename("yolov8n.pt", model_path)
    return model_path

def test_stage_3():
    download_yolov8n()
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    import torch
    config['object_detection']['device'] = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # define dummy zone for test
    config['zones'] = [
        {"id": 1, "name": "Test Zone", "polygon": [[0, 0], [300, 0], [300, 300], [0, 300]]}
    ]
    
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
        stream_0, 
        (resize_w, resize_h), 
        clip_limit, 
        grid, 
        brightness_thresh,
        enable_stab,
        config.get('debug')
    )
    
    import itertools
    from stages.stage_2a_motion import motion_detection_stage
    stream_1a, stream_1b = itertools.tee(stream_1, 2)
    
    stream_2a = motion_detection_stage(stream_1a, config['motion_detection'], config.get('debug'))
    stream_2b = object_detection_stage(stream_1b, config['object_detection'], config.get('debug'))
    
    stream_3 = tracking_stage(stream_2a, stream_2b, config, config.get('debug'))
    
    count = 0
    unique_tracks = set()
    track_logs = []
    
    try:
        for t_frame in stream_3:
            count += 1
            
            # verify schema
            assert isinstance(t_frame, TrackingFrame)
            
            for t in t_frame.records:
                unique_tracks.add(t['track_id'])
                track_logs.append({
                    "frame_no": t['frame_no'],
                    "timestamp": t['timestamp'],
                    "track_id": t['track_id'],
                    "class": t['class'],
                    "bbox": t['bbox'],
                    "zone_id": t['zone_id'],
                    "confidence": t['confidence'],
                    "motion_score": t['motion_score']
                })
                
            if count >= 10:
                print("--- Breaking early to test cleanup ---")
                stream_3.close()
                break
                
    except AssertionError as e:
        logger.error(f"Test Failed (Assertion): {e}")
    except Exception as e:
        logger.error(f"Unexpected Exception: {e}")
    else:
        print("\n--- Test Summary ---")
        print(f"Frames processed: {count}")
        print(f"Unique tracks found: {len(unique_tracks)}")
        print("Sample of track log:")
        print(json.dumps(track_logs[:3], indent=2))
        print("Test Passed: Stage 3 completed successfully.")

if __name__ == '__main__':
    test_stage_3()
