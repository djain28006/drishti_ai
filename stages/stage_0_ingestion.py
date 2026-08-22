import cv2
import time
import os
from typing import Generator, Tuple
from dataclasses import dataclass
import numpy as np
from utils.logger import StageLogger

logger = StageLogger("STAGE 0")

@dataclass
class FrameData:
    """Dataclass representing the output of the ingestion stage for a single frame."""
    frame: np.ndarray
    frame_no: int
    timestamp: float
    fps: float
    resolution: Tuple[int, int]


def video_ingestion_stage(
    video_path: str, 
    skip_initial_frames: int = 0, 
    frame_sample_rate: int = 1,
    max_consecutive_corrupt_frames: int = 10,
    target_fps: float = 0,
    debug_cfg: dict = None
) -> Generator[FrameData, None, None]:
    """
    Ingests video and yields frames with normalized timestamps.
    Handles variable FPS, graceful failure on corruption, and stream-processing.
    
    Args:
        video_path: Path to the input video file.
        skip_initial_frames: Number of frames to skip at the beginning.
        frame_sample_rate: Process every Nth frame (Deprecated if target_fps > 0).
        max_consecutive_corrupt_frames: Threshold to abort stream on contiguous errors.
        target_fps: Target frames per second to yield (0 = use frame_sample_rate).
        debug_cfg: Debug configuration dictionary.
        
    Yields:
        FrameData object for each processed frame.
    """
    if frame_sample_rate < 1:
        logger.error(f"Invalid frame_sample_rate {frame_sample_rate}. Defaulting to 1.")
        frame_sample_rate = 1
        
    if skip_initial_frames < 0:
        logger.error(f"Invalid skip_initial_frames {skip_initial_frames}. Defaulting to 0.")
        skip_initial_frames = 0
        
    if not os.path.exists(video_path):
        logger.error(f"Video file does not exist: {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video file: {video_path}")
        return

    # Attempt to get nominal FPS
    nominal_fps = cap.get(cv2.CAP_PROP_FPS)
    if nominal_fps <= 0 or not np.isfinite(nominal_fps): # handle NaN, 0 or negative
        nominal_fps = 30.0
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resolution = (width, height)
    
    frames_read = 0
    frames_yielded = 0
    frames_skipped = 0
    consecutive_corrupt_frames = 0
    last_timestamp = -1.0
    start_time = time.time()
    
    # Frame interval calculation
    if target_fps > 0:
        frame_interval = max(1, round(nominal_fps / target_fps))
    else:
        frame_interval = frame_sample_rate
        
    effective_fps = nominal_fps / frame_interval
    
    logger.info(f"Started ingestion for {os.path.basename(video_path)} (Resolution: {width}x{height}, Native FPS: {nominal_fps})")
    logger.info(f"Sampling applied: Target FPS={target_fps}, Interval={frame_interval}, Effective Output FPS={effective_fps:.2f}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if frames_read == 0:
                    logger.error("Empty video or immediate read failure.")
                break
                
            frames_read += 1
            
            if frame is None or frame.size == 0:
                consecutive_corrupt_frames += 1
                logger.error(f"Corrupted frame encountered at frame {frames_read}. (Consecutive: {consecutive_corrupt_frames})")
                if consecutive_corrupt_frames >= max_consecutive_corrupt_frames:
                    logger.error(f"Exceeded max consecutive corrupt frames ({max_consecutive_corrupt_frames}). Aborting stream.")
                    logger.error(f"Last successful frame: {frames_read - consecutive_corrupt_frames}")
                    break
                continue
            else:
                consecutive_corrupt_frames = 0
            
            if frames_read <= skip_initial_frames:
                frames_skipped += 1
                continue
                
            # Skip frames based on calculated frame interval
            # The first frame after skip_initial_frames should be yielded (offset by 1)
            if (frames_read - skip_initial_frames - 1) % frame_interval != 0:
                frames_skipped += 1
                continue

            # Calculate timestamp in seconds
            msec = cap.get(cv2.CAP_PROP_POS_MSEC)
            if msec > 0:
                timestamp = msec / 1000.0
                # Monotonic check: fallback if stuck
                if timestamp <= last_timestamp:
                    timestamp = frames_read / nominal_fps
            else:
                timestamp = frames_read / nominal_fps
                
            last_timestamp = timestamp
            
            if debug_cfg and debug_cfg.get('enabled', False):
                from utils.visualizer import visualize_stage_0
                visualize_stage_0(debug_cfg, frame, frames_read, timestamp)
                
            output = FrameData(
                frame=frame,
                frame_no=frames_read,
                timestamp=timestamp,
                fps=nominal_fps,
                resolution=resolution
            )
            
            logger.info(f"Yielded frame {frames_read}")
            frames_yielded += 1
            yield output
            
    except GeneratorExit:
        logger.info("Generator closed early by the caller.")
    except Exception as e:
        logger.error(f"Exception during ingestion: {str(e)}")
        logger.error(f"Last successful frame: {frames_read - consecutive_corrupt_frames}")
    finally:
        cap.release()
        elapsed = time.time() - start_time
        logger.info("Ingestion completed.")
        logger.info(f"Total frames read: {frames_read}")
        logger.info(f"Total frames yielded: {frames_yielded}")
        logger.info(f"Total frames skipped: {frames_skipped}")
        logger.info(f"Elapsed time: {elapsed:.2f}s")
