import cv2
import os

def check_video():
    path = 'sample.mp4'
    if not os.path.exists(path):
        print("File does not exist.")
        return
        
    cap = cv2.VideoCapture(path)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps if fps > 0 else 0
    
    print(f"CAP_PROP_FRAME_COUNT: {frame_count}")
    print(f"CAP_PROP_FPS: {fps}")
    print(f"Calculated duration: {duration:.2f}s")
    
    count = 0
    while True:
        ret, _ = cap.read()
        if not ret: break
        count += 1
        
    print(f"Actual frames read from video: {count}")
    cap.release()

if __name__ == '__main__':
    check_video()
