import yaml
import numpy as np
from stages.stage_0_ingestion import video_ingestion_stage
from stages.stage_1_preprocess import preprocess_stage, PreprocessedFrame

def test_stage_1():
    print("--- Starting Stage 1 Test ---")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    video_path = config['video']['input_path']
    skip = config['video']['skip_initial_frames']
    sample_rate = config['video']['frame_sample_rate']
    max_corrupt = config['video']['max_consecutive_corrupt_frames']
    
    resize_w = config['preprocessing']['resize_width']
    resize_h = config['preprocessing']['resize_height']
    clip_limit = config['preprocessing']['clahe_clip_limit']
    grid = tuple(config['preprocessing']['clahe_tile_grid_size'])
    brightness_thresh = config['preprocessing']['brightness_jump_threshold']
    
    # Chain generators
    stream_0 = video_ingestion_stage(video_path, skip, sample_rate, max_corrupt)
    stream_1 = preprocess_stage(
        stream_0, 
        (resize_w, resize_h), 
        clip_limit, 
        grid, 
        brightness_thresh
    )
    
    count = 0
    try:
        for processed in stream_1:
            count += 1
            
            # Verify Schema
            assert isinstance(processed, PreprocessedFrame), "Yielded object is not a PreprocessedFrame"
            assert isinstance(processed.gray_frame, np.ndarray), "gray_frame is not ndarray"
            assert isinstance(processed.color_frame, np.ndarray), "color_frame is not ndarray"
            
            # Verify Shape
            assert processed.color_frame.shape == (resize_h, resize_w, 3), f"Color frame shape incorrect: {processed.color_frame.shape}"
            assert processed.gray_frame.shape == (resize_h, resize_w), f"Gray frame shape incorrect: {processed.gray_frame.shape}"
            
            if count >= 3:
                print("--- Breaking early to test cleanup ---")
                stream_1.close() # Test cascading generator cleanup
                break
                
    except AssertionError as e:
        print(f"Test Failed: {e}")
    except Exception as e:
        print(f"Unexpected Exception: {e}")
    else:
        print("Test Passed: Stage 1 verifications succeeded.")

if __name__ == '__main__':
    test_stage_1()
