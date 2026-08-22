import yaml
import itertools
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_2a_motion import motion_detection_stage
from stages.stage_2b_object import object_detection_stage
from stages.stage_3_tracking import tracking_stage

def test_anomalies():
    print("--- Running Anomaly Diagnosis ---")
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
    stream_2a, stream_2a_test = itertools.tee(motion_detection_stage(stream_1a, config['motion_detection'], config.get('debug')))
    stream_2b, stream_2b_test = itertools.tee(object_detection_stage(stream_1b, config['object_detection'], config.get('debug')))
    
    stream_3 = tracking_stage(stream_2a, stream_2b, config, config.get('debug'))
    
    print("\n--- Track 1 Diagnosis ---")
    print(f"{'Frame':<6} | {'Class':<10} | {'Conf':<6} | {'BBox'}")
    
    track_1_logs = []
    track_2_logs = []
    track_3_logs = []
    
    for m_frame, od_frame, t_frame in zip(stream_2a_test, stream_2b_test, stream_3):
        for r in t_frame.records:
            tid = r['track_id']
            if tid == 1:
                track_1_logs.append(r)
            elif tid == 2 and 139 <= r['frame_no'] <= 163:
                track_2_logs.append(r)
            elif tid == 3:
                track_3_logs.append(r)
                
    for r in track_1_logs:
        print(f"{r['frame_no']:<6} | {r['class']:<10} | {r['confidence']:.3f} | {r['bbox']}")
        
    print("\n--- Track 2 and Track 3 Diagnosis (Frames 139-163) ---")
    print(f"{'Frame':<6} | {'Track 2 BBox':<25} | {'Track 2 Conf':<15} | {'Track 3 Class':<15} | {'Track 3 BBox':<25} | {'Track 3 Conf'}")
    
    # Align by frame
    frames_overlap = sorted(list(set([r['frame_no'] for r in track_2_logs] + [r['frame_no'] for r in track_3_logs])))
    for f_no in frames_overlap:
        t2 = next((r for r in track_2_logs if r['frame_no'] == f_no), None)
        t3 = next((r for r in track_3_logs if r['frame_no'] == f_no), None)
        
        t2_bbox = str(t2['bbox']) if t2 else "None"
        t2_conf = f"{t2['confidence']:.3f}" if t2 else "None"
        
        t3_cls = str(t3['class']) if t3 else "None"
        t3_bbox = str(t3['bbox']) if t3 else "None"
        t3_conf = f"{t3['confidence']:.3f}" if t3 else "None"
        
        print(f"{f_no:<6} | {t2_bbox:<25} | {t2_conf:<15} | {t3_cls:<15} | {t3_bbox:<25} | {t3_conf}")

if __name__ == '__main__':
    test_anomalies()
