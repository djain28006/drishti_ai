import cv2
import numpy as np
from typing import Generator, Tuple
from dataclasses import dataclass
from utils.logger import StageLogger
from stages.stage_0_ingestion import FrameData

logger = StageLogger("STAGE 1")

@dataclass
class PreprocessedFrame:
    """Dataclass representing the output of the preprocessing stage."""
    gray_frame: np.ndarray
    color_frame: np.ndarray
    frame_no: int
    timestamp: float

def preprocess_stage(
    frame_stream: Generator[FrameData, None, None],
    resize_dims: Tuple[int, int] = (640, 480),
    clahe_clip_limit: float = 2.0,
    clahe_tile_grid_size: Tuple[int, int] = (8, 8),
    brightness_jump_threshold: float = 50.0,
    enable_stabilization: bool = False,
    debug_cfg: dict = None
) -> Generator[PreprocessedFrame, None, None]:
    """
    Applies resizing, grayscale conversion, CLAHE, and basic denoising.
    Handles brightness jump detection as specified in edge cases.
    
    Args:
        frame_stream: The generator from Stage 0 yielding FrameData.
        resize_dims: Width, Height to resize frames to.
        clahe_clip_limit: Threshold for contrast limiting.
        clahe_tile_grid_size: Size of grid for histogram equalization.
        brightness_jump_threshold: Absolute difference in mean brightness to trigger a log.
        enable_stabilization: Flag to enable video stabilization (currently deferred).
        debug_cfg: Optional debug configuration dict.
        
    Yields:
        PreprocessedFrame object.
    """
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=clahe_tile_grid_size)
    last_mean_brightness = -1.0
    
    logger.info(f"Started preprocessing (Resize: {resize_dims}, CLAHE clip: {clahe_clip_limit}, Stabilization: {enable_stabilization})")

    frames_processed = 0

    try:
        for frame_data in frame_stream:
            # Placeholder for Video Stabilization
            if enable_stabilization:
                pass

            # Resize
            color_frame = cv2.resize(frame_data.frame, resize_dims)
            
            # Grayscale
            gray_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)
            
            # Brightness jump check
            current_mean = np.mean(gray_frame)
            if last_mean_brightness >= 0:
                diff = abs(current_mean - last_mean_brightness)
                if diff > brightness_jump_threshold:
                    logger.info(f"Large brightness jump detected at frame {frame_data.frame_no} (Diff: {diff:.2f})")
            last_mean_brightness = current_mean
            
            # Apply CLAHE on grayscale to improve contrast for motion detection
            clahe_frame = clahe.apply(gray_frame)
            
            # Apply light Gaussian blur for denoising (helps MOG2 later)
            final_gray = cv2.GaussianBlur(clahe_frame, (5, 5), 0)
            
            if debug_cfg and debug_cfg.get('enabled', False):
                from utils.visualizer import visualize_stage_1
                visualize_stage_1(
                    debug_cfg,
                    frame_data.frame,
                    color_frame,
                    gray_frame,
                    clahe_frame,
                    final_gray,
                    frame_data.frame_no,
                    frame_data.timestamp
                )
            
            output = PreprocessedFrame(
                gray_frame=final_gray,
                color_frame=color_frame,
                frame_no=frame_data.frame_no,
                timestamp=frame_data.timestamp
            )
            
            logger.info(f"Processed frame {frame_data.frame_no}")
            frames_processed += 1
            yield output
            
    except GeneratorExit:
        logger.info("Generator closed early by the caller.")
    except Exception as e:
        logger.error(f"Exception during preprocessing: {str(e)}")
    finally:
        logger.info("Preprocessing completed.")
        logger.info(f"Total frames processed: {frames_processed}")
