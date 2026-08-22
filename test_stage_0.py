import yaml
import numpy as np
from stages.stage_0_ingestion import video_ingestion_stage, FrameData

def test_stage_0():
    print("--- Starting Test ---")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    video_path = config['video']['input_path']
    skip = config['video']['skip_initial_frames']
    sample_rate = config['video']['frame_sample_rate']
    max_corrupt = config['video'].get('max_consecutive_corrupt_frames', 10)
    
    stream = video_ingestion_stage(video_path, skip, sample_rate, max_corrupt)
    
    last_frame_no = -1
    last_timestamp = -1.0
    
    count = 0
    try:
        for frame_data in stream:
            count += 1
            
            # Verify Schema
            assert isinstance(frame_data, FrameData), "Yielded object is not a FrameData instance"
            assert isinstance(frame_data.frame, np.ndarray), "Frame is not a numpy array"
            assert isinstance(frame_data.frame_no, int), "Frame number is not an integer"
            assert isinstance(frame_data.timestamp, float), "Timestamp is not a float"
            
            # Verify logic
            assert frame_data.frame_no > last_frame_no, f"Frame number did not increase (last: {last_frame_no}, current: {frame_data.frame_no})"
            assert frame_data.timestamp >= last_timestamp, f"Timestamp did not increase monotonically (last: {last_timestamp}, current: {frame_data.timestamp})"
            
            last_frame_no = frame_data.frame_no
            last_timestamp = frame_data.timestamp
            
            if count >= 5:
                print("--- Breaking early to test generator cleanup ---")
                stream.close() # Explicitly test generator cleanup
                break
                
    except AssertionError as e:
        print(f"Test Failed: {e}")
    except Exception as e:
        print(f"Unexpected Exception: {e}")
    else:
        print("Test Passed: All verifications succeeded.")

if __name__ == '__main__':
    test_stage_0()
