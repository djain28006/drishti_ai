import cv2
import numpy as np
from configparser import ConfigParser
# Let's just create a test video directly for testing Stage 0

def create_test_video(output_path='sample.mp4', frames=100, fps=30):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (640, 480))
    for i in range(frames):
        # Create a simple frame that changes color
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Moving square
        x = (i * 5) % 640
        cv2.rectangle(frame, (x, 200), (x+50, 250), (0, 255, 0), -1)
        out.write(frame)
    out.release()
    print(f"Created test video {output_path}")

if __name__ == '__main__':
    create_test_video()
