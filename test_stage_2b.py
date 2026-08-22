import yaml
import os
import urllib.request
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage
from stages.stage_2b_object import object_detection_stage, ObjectDetectionFrame, Detection

def download_yolov8n():
    os.makedirs("models", exist_ok=True)
    model_path = "models/yolov8n.pt"
    if not os.path.exists(model_path):
        print(f"Downloading {model_path} for testing...")
        # A quick way to get it is through ultralytics
        from ultralytics import YOLO
        YOLO("yolov8n.pt") # downloads to current dir
        if os.path.exists("yolov8n.pt"):
            os.rename("yolov8n.pt", model_path)
    return model_path

def test_stage_2b():
    print("--- Starting Stage 2B Test ---")
    download_yolov8n()
    
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    import torch
    # Use GPU if available for faster test execution, fallback to CPU safely
    config['object_detection']['device'] = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    video_path = config['video']['input_path']
    skip = config['video']['skip_initial_frames']
    sample_rate = config['video']['frame_sample_rate']
    max_corrupt = config['video']['max_consecutive_corrupt_frames']
    
    resize_w = config['preprocessing']['resize_width']
    resize_h = config['preprocessing']['resize_height']
    clip_limit = config['preprocessing']['clahe_clip_limit']
    grid = tuple(config['preprocessing']['clahe_tile_grid_size'])
    brightness_thresh = config['preprocessing']['brightness_jump_threshold']
    enable_stab = config['preprocessing']['enable_stabilization']
    
    # 1. Setup Generators
    stream_0 = video_ingestion_stage(video_path, skip, sample_rate, max_corrupt)
    stream_1 = preprocess_stage(
        stream_0, 
        (resize_w, resize_h), 
        clip_limit, 
        grid, 
        brightness_thresh,
        enable_stab
    )
    
    # Empty detection test hook
    def stream_1_interceptor():
        count = 0
        for frame in stream_1:
            count += 1
            if count == 3:
                # Inject a black frame which should result in zero detections
                import numpy as np
                frame.color_frame = np.zeros_like(frame.color_frame)
            yield frame

    stream_2b = object_detection_stage(stream_1_interceptor(), config['object_detection'])
    
    count = 0
    try:
        for od_frame in stream_2b:
            count += 1
            
            # Verify Schema
            assert isinstance(od_frame, ObjectDetectionFrame), "Not an ObjectDetectionFrame"
            assert isinstance(od_frame.detections, list), "Detections not a list"
            assert isinstance(od_frame.model_version, str), "Model version not string"
            
            # Verify coordinates and confidence
            for det in od_frame.detections:
                assert isinstance(det, Detection)
                x, y, w, h = det.bbox
                assert 0 <= x < resize_w, f"x out of bounds: {x}"
                assert 0 <= y < resize_h, f"y out of bounds: {y}"
                assert 0.0 <= det.confidence <= 1.0, f"Confidence out of bounds: {det.confidence}"
                assert isinstance(det.class_name, str)
                
            # Verify empty detection on injected frame
            if count == 3:
                assert len(od_frame.detections) == 0, f"Expected 0 detections on black frame, got {len(od_frame.detections)}"
                
            if count >= 4:
                print("--- Breaking early to test cleanup ---")
                stream_2b.close()
                break
                
    except AssertionError as e:
        print(f"Test Failed: {e}")
    except Exception as e:
        print(f"Unexpected Exception: {e}")
    else:
        print("Test Passed: Stage 2B verifications succeeded.")

if __name__ == '__main__':
    test_stage_2b()
