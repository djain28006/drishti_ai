import cv2
import numpy as np
from typing import Generator, List, Tuple, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from utils.logger import StageLogger
from stages.stage_1_preprocess import PreprocessedFrame
from stages.stage_1_5_zone_calibration import ZoneMap, ZoneSpec

logger = StageLogger("STAGE 2A")

@dataclass
class ZoneMotionResult:
    zone_id: int
    motion_score: float
    baseline_deviation: float
    boundary_crossing: bool
    crossed_into_zone_id: Optional[int]

@dataclass
class MotionFrame:
    """Dataclass representing the output of the motion detection stage."""
    motion_mask: np.ndarray
    motion_boxes: List[Tuple[int, int, int, int]]
    zone_results: List[ZoneMotionResult]
    global_motion_score: float
    global_motion_percentage: float
    frame_no: int
    timestamp: float
    is_warmup: bool
    global_motion_suppressed: bool

class MotionDetectorStrategy(ABC):
    @abstractmethod
    def detect(self, gray_frame: np.ndarray) -> np.ndarray:
        """Returns binary motion mask given a grayscale frame."""
        pass

class MOG2Strategy(MotionDetectorStrategy):
    def __init__(self, history: int = 500, var_threshold: float = 16, detect_shadows: bool = True):
        self.mog2 = cv2.createBackgroundSubtractorMOG2(
            history=history, 
            varThreshold=var_threshold, 
            detectShadows=detect_shadows
        )
        
    def detect(self, gray_frame: np.ndarray) -> np.ndarray:
        mask = self.mog2.apply(gray_frame)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        return mask

def get_motion_strategy(config: dict, target_fps: int = 5) -> MotionDetectorStrategy:
    """Create the configured motion detector strategy.

    target_fps is accepted for signature compatibility but history is intentionally
    NOT scaled by FPS. Benchmark (2026-08-22) showed time-based scaling
    (history = history_seconds * target_fps) is counterproductive: shorter histories
    make MOG2 adapt faster and absorb slow cheating behaviors (gradual lean, sustained
    peek) as 'new background', reducing Stage 2A triggers at every FPS value tested.
    Fixed history=500 frames is the correct value regardless of sampling rate.
    """
    mog2_cfg = config.get("mog2", {})
    history = mog2_cfg.get("history", 500)
    logger.info(f"MOG2 history: {history} frames (fixed, not FPS-scaled — see docstring)")
    return MOG2Strategy(
        history=history,
        var_threshold=mog2_cfg.get("var_threshold", 16.0),
        detect_shadows=mog2_cfg.get("detect_shadows", True)
    )

def motion_detection_stage(
    preprocessed_stream: Generator[PreprocessedFrame, None, None],
    zone_map: ZoneMap,
    config_dict: dict,
    debug_cfg: dict = None,
    target_fps: int = 5,
) -> Generator[MotionFrame, None, None]:
    """
    Applies motion detection to a stream of preprocessed frames using ZoneMap.
    Outputs per-zone motion scores, baseline deviations, and boundary crossing flags.

    Args:
        target_fps: Sampling rate of the pipeline. Used to compute a time-based MOG2
                    history window so background memory stays constant across FPS settings.
    """
    strategy = get_motion_strategy(config_dict, target_fps=target_fps)
    
    morph_cfg = config_dict.get("morphology", {})
    kernel_size = morph_cfg.get("kernel_size", 5)
    iterations = morph_cfg.get("iterations", 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    
    min_motion_area = config_dict.get("min_motion_area", 200)
    warmup_frames = config_dict.get("warmup_frames", 15)
    
    gm_cfg = config_dict.get("global_motion_suppression", {})
    gm_enabled = gm_cfg.get("enabled", True)
    gm_threshold_percentage = gm_cfg.get("threshold_percentage", 70)
    
    logger.info(f"Started per-zone motion detection (Zones: {len(zone_map.zones)}, Warmup: {warmup_frames})")
    frames_processed = 0

    try:
        for frame_data in preprocessed_stream:
            if frame_data is None or frame_data.gray_frame is None or frame_data.gray_frame.size == 0:
                logger.error(f"Corrupted frame at frame {frame_data.frame_no if frame_data else 'unknown'}. Skipping.")
                continue

            # Background subtraction & morphology
            raw_mask = strategy.detect(frame_data.gray_frame)
            mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel, iterations=iterations)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iterations)

            # Contours and bounding boxes
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_boxes = [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) >= min_motion_area]

            # Global motion metrics
            global_score = float(np.sum(mask > 0))
            total_pixels = mask.size
            global_percentage = (global_score / total_pixels) * 100.0 if total_pixels > 0 else 0.0

            is_warmup = frames_processed < warmup_frames
            global_motion_suppressed = False
            if gm_enabled and global_percentage > gm_threshold_percentage:
                global_motion_suppressed = True

            # Per-zone motion analysis against locked ZoneMap baselines
            zone_results: List[ZoneMotionResult] = []
            h_img, w_img = mask.shape

            for z_spec in zone_map.zones:
                pts = np.array(z_spec.polygon, dtype=np.int32)
                x1_z = max(0, int(np.min(pts[:, 0])))
                y1_z = max(0, int(np.min(pts[:, 1])))
                x2_z = min(w_img, int(np.max(pts[:, 0])))
                y2_z = min(h_img, int(np.max(pts[:, 1])))

                roi = mask[y1_z:y2_z, x1_z:x2_z]
                motion_score = 0.0
                if roi.size > 0:
                    motion_score = float(np.count_nonzero(roi)) / float(roi.size)

                # Baseline deviation
                deviation = motion_score - z_spec.baseline_median_motion

                # Boundary crossing check: thin border strip around zone
                boundary_crossing = False
                crossed_into_id = None

                # Check boundary strip motion against neighboring zones
                border_roi_top = mask[max(0, y1_z - 5):y1_z, x1_z:x2_z]
                border_roi_right = mask[y1_z:y2_z, x2_z:min(w_img, x2_z + 5)]
                
                if (border_roi_top.size > 0 and np.count_nonzero(border_roi_top) > 5) or \
                   (border_roi_right.size > 0 and np.count_nonzero(border_roi_right) > 5):
                    boundary_crossing = True
                    # Check neighboring zone ID if available
                    for neighbor in zone_map.zones:
                        if neighbor.zone_id != z_spec.zone_id:
                            n_pts = np.array(neighbor.polygon, dtype=np.int32)
                            nx1 = max(0, int(np.min(n_pts[:, 0])))
                            ny1 = max(0, int(np.min(n_pts[:, 1])))
                            nx2 = min(w_img, int(np.max(n_pts[:, 0])))
                            ny2 = min(h_img, int(np.max(n_pts[:, 1])))
                            if abs(x2_z - nx1) < 20 or abs(y1_z - ny2) < 20:
                                crossed_into_id = neighbor.zone_id
                                break

                z_res = ZoneMotionResult(
                    zone_id=z_spec.zone_id,
                    motion_score=round(motion_score, 4),
                    baseline_deviation=round(deviation, 4),
                    boundary_crossing=boundary_crossing,
                    crossed_into_zone_id=crossed_into_id
                )
                zone_results.append(z_res)

            output = MotionFrame(
                motion_mask=mask,
                motion_boxes=motion_boxes,
                zone_results=zone_results,
                global_motion_score=global_score,
                global_motion_percentage=global_percentage,
                frame_no=frame_data.frame_no,
                timestamp=frame_data.timestamp,
                is_warmup=is_warmup,
                global_motion_suppressed=global_motion_suppressed
            )

            logger.info(f"Processed frame {frame_data.frame_no} (Per-Zone Motion Results: {len(zone_results)})")
            frames_processed += 1
            yield output

    except GeneratorExit:
        logger.info("Generator closed early by the caller.")
    except Exception as e:
        logger.error(f"Exception during per-zone motion detection: {str(e)}")
    finally:
        logger.info("Per-zone motion detection completed.")
        logger.info(f"Total frames processed: {frames_processed}")
