import yaml
import itertools
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking import tracking_stage
import os

def download_yolov8n():
    os.makedirs("models", exist_ok=True)
    model_path = "models/yolov8n.pt"
    if not os.path.exists(model_path):
        print(f"Downloading {model_path} for testing...")
        from ultralytics import YOLO
        YOLO("yolov8n.pt") 
        if os.path.exists("yolov8n.pt"):
            os.rename("yolov8n.pt", model_path)
    return model_path

def test_full_pipeline():
    print("--- Starting Full Pipeline Test ---")
    download_yolov8n()
    
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
        stream_0, 
        (resize_w, resize_h), 
        clip_limit, 
        grid, 
        brightness_thresh,
        enable_stab,
        config.get('debug')
    )
    
    # tee the preprocessed stream to feed both 2A and 2B in parallel
    stream_1a, stream_1b = itertools.tee(stream_1, 2)
    
    stream_2a, stream_2a_test = itertools.tee(motion_detection_stage(stream_1a, config['motion_detection'], config.get('debug')))
    stream_2b, stream_2b_test = itertools.tee(object_detection_stage(stream_1b, config['object_detection'], config.get('debug')))
    
    # We will test up to Stage 3 tracking
    stream_3 = tracking_stage(stream_2a, stream_2b, config, config.get('debug'))
    
    print("\n--- Diagnostic: Raw YOLO Person Confidences & Track Events ---")
    print(f"{'Frame':<6} | {'Person Confs':<20} | {'Active Track IDs':<20} | {'Events'}")
    print("-" * 75)
    
    count = 0
    
    track_summary = {} # track_id -> {first_frame, last_frame, record_count}
    active_tracks_prev = set()
    
    try:
        for m_frame, od_frame, t_frame in zip(stream_2a_test, stream_2b_test, stream_3):
            count += 1
            frame_no = m_frame.frame_no
            
            # 1. Raw YOLO person confidences
            person_confs = []
            for d in od_frame.detections:
                if d.class_name == "person":
                    person_confs.append(round(d.confidence, 3))
                    
            # 2. Track creation and loss
            active_tracks_current = set(r['track_id'] for r in t_frame.records)
            events = []
            
            new_tracks = active_tracks_current - active_tracks_prev
            for tid in new_tracks:
                events.append(f"+ID:{tid}")
                
            lost_tracks = active_tracks_prev - active_tracks_current
            for tid in lost_tracks:
                events.append(f"-ID:{tid}")
                
            active_tracks_prev = active_tracks_current
            
            # Update summary
            for r in t_frame.records:
                tid = r['track_id']
                if tid not in track_summary:
                    track_summary[tid] = {'first': frame_no, 'last': frame_no, 'count': 0}
                track_summary[tid]['last'] = frame_no
                track_summary[tid]['count'] += 1
                
            # Print row
            confs_str = ", ".join(map(str, person_confs))
            tracks_str = ", ".join(map(str, active_tracks_current))
            events_str = ", ".join(events)
            print(f"{frame_no:<6} | {confs_str:<20} | {tracks_str:<20} | {events_str}")
                
    except AssertionError as e:
        print(f"Test Failed (Assertion): {e}")
    except Exception as e:
        print(f"Unexpected Exception: {e}")
    else:
        print("-" * 75)
        print(f"\n--- Permanent Per-Track Summary ---")
        print(f"{'Track ID':<10} | {'First Frame':<12} | {'Last Frame':<12} | {'Total Duration':<15} | {'Records'}")
        print("-" * 70)
        for tid, summary in track_summary.items():
            duration = summary['last'] - summary['first']
            print(f"{tid:<10} | {summary['first']:<12} | {summary['last']:<12} | {duration:<15} | {summary['count']}")
        
        print("\nTest Passed: Full pipeline completed successfully.")

if __name__ == '__main__':
    test_full_pipeline()
