import os
import cv2
from typing import Generator, List, Tuple, Optional, Any
from dataclasses import dataclass
from utils.logger import StageLogger
from stages.stage_1_preprocess import PreprocessedFrame
from stages.stage_2a_motion import MotionFrame

logger = StageLogger("STAGE 2B")

@dataclass
class Detection:
    """Dataclass representing a single object detection."""
    class_name: str
    class_id: int
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    zone_id: Optional[int] = None

@dataclass
class ObjectDetectionFrame:
    """Dataclass representing the output of the object detection stage."""
    detections: List[Detection]
    frame_no: int
    timestamp: float
    model_version: str
    color_frame: Optional[Any] = None

def object_detection_stage(
    preprocessed_stream: Generator[PreprocessedFrame, None, None],
    motion_stream: Any = None,
    config_dict: Optional[dict] = None,
    debug_cfg: dict = None
) -> Generator[ObjectDetectionFrame, None, None]:
    """
    Applies ROI-restricted object detection to a stream of preprocessed frames using SAHI + YOLO.
    Consumes Stage 2A MotionFrame to focus detection on active motion zones if provided.
    """
    import torch
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction

    # Handle backward-compatible calling convention: object_detection_stage(stream, config_dict)
    if isinstance(motion_stream, dict) and config_dict is None:
        config_dict = motion_stream
        motion_stream = None
    if config_dict is None:
        config_dict = {}
    
    model_path = config_dict.get("model_path", "yolov8n.pt")
    if not os.path.exists(model_path):
        for fallback in ['yolov8n.pt', 'models/yolov8n.pt', 'best.pt', 'models/best.pt']:
            if os.path.exists(fallback):
                model_path = fallback
                break

    device_req = str(config_dict.get("device", "cuda" if torch.cuda.is_available() else "cpu")).strip()
    if device_req.lower() == 'auto' or device_req.lower().startswith('cuda'):
        if torch.cuda.is_available():
            device = 'cuda:0' if device_req.lower() in ('auto', 'cuda') else device_req
            torch.backends.cudnn.benchmark = True
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU Acceleration active on {gpu_name} (Device: {device})")
        else:
            logger.warning(f"CUDA requested ({device_req}) but CUDA is not available. Falling back to CPU.")
            device = 'cpu'
    else:
        device = device_req

    conf_thresh = config_dict.get("confidence_threshold", 0.12)
    classes_of_interest = config_dict.get("classes_of_interest", None)
    
    sahi_cfg = config_dict.get("sahi", {})
    sahi_enabled = sahi_cfg.get("enabled", True)
    slice_height = sahi_cfg.get("slice_height", 512)
    slice_width = sahi_cfg.get("slice_width", 512)
    
    if not os.path.exists(model_path):
        logger.error(f"Model file missing: {model_path}")
        raise FileNotFoundError(f"Model file missing: {model_path}")
        
    try:
        detection_model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=model_path,
            confidence_threshold=conf_thresh,
            device=device
        )
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise
        
    dev_str = f"Device: {device} ({torch.cuda.get_device_name(0)})" if "cuda" in str(device) and torch.cuda.is_available() else f"Device: {device}"
    logger.info(f"Started ROI-restricted object detection (Model: {model_path}, Conf: {conf_thresh}, {dev_str})")
    frames_processed = 0
    
    stream_pairs = zip(preprocessed_stream, motion_stream) if motion_stream is not None else ((pf, None) for pf in preprocessed_stream)

    try:
        for p_frame, m_frame in stream_pairs:
            if p_frame is None or p_frame.color_frame is None or p_frame.color_frame.size == 0:
                continue
                
            color_frame = p_frame.color_frame
            
            # Identify active zones from Stage 2A motion output
            active_zones = []
            if m_frame is not None and hasattr(m_frame, 'zone_results'):
                active_zones = [
                    z for z in m_frame.zone_results 
                    if z.motion_score > 0.0001 or z.baseline_deviation > 0 or z.boundary_crossing
                ]
            
            detections = []
            
            # Run detection if active zones exist, or no motion stream provided, or as routine baseline check.
            if motion_stream is None or active_zones or frames_processed % 3 == 0:
                result = get_sliced_prediction(
                    color_frame,
                    detection_model,
                    slice_height=slice_height,
                    slice_width=slice_width,
                    overlap_height_ratio=0.2,
                    overlap_width_ratio=0.2,
                    postprocess_type="NMS"
                )
                
                for obj in result.object_prediction_list:
                    score = obj.score.value
                    cls_id = obj.category.id
                    cls_name = obj.category.name
                    cls_clean = cls_name.lower().strip()
                    
                    if classes_of_interest:
                        allowed = [c.lower().strip() for c in classes_of_interest]
                        if cls_clean not in allowed and "phone" not in cls_clean and "cell" not in cls_clean:
                            continue
                        
                    if score < conf_thresh:
                        continue
                        
                    bbox = obj.bbox.to_xywh()
                    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    
                    detections.append(Detection(
                        class_name=cls_name,
                        class_id=int(cls_id) if cls_id is not None else 0,
                        bbox=(x, y, w, h),
                        confidence=score
                    ))
            
            output = ObjectDetectionFrame(
                detections=detections,
                frame_no=p_frame.frame_no,
                timestamp=p_frame.timestamp,
                model_version=model_path,
                color_frame=color_frame
            )
            
            logger.info(f"Processed frame {p_frame.frame_no} (Active Zones: {len(active_zones)}, Detections: {len(detections)})")
            frames_processed += 1
            yield output
            
    except GeneratorExit:
        logger.info("Generator closed early by the caller.")
    except Exception as e:
        logger.error(f"Exception during object detection: {str(e)}")
    finally:
        logger.info("Object detection completed.")
        logger.info(f"Total frames processed: {frames_processed}")
