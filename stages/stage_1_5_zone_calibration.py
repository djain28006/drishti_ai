"""
Stage 1.5 — One-Time Student Zone Calibration
=============================================
Detection hierarchy (in order of priority):
  1. SAHI full-frame pass  (catches close/large students)
  2. Tiled + 2× upscale pass (catches far/small students)
  3. Multi-frame confidence aggregation across all calibration frames
  4. Spatial-gap estimation for students still missing after YOLO passes
     (marks zones as ESTIMATED vs DETECTED)

Once calibration finishes, all zones are LOCKED and never moved again.
"""
import os
import cv2
import json
import numpy as np
from typing import Generator, List, Tuple, Optional, Dict
from dataclasses import dataclass, asdict, field
from utils.logger import StageLogger
from stages.stage_1_preprocess import PreprocessedFrame

logger = StageLogger("STAGE 1.5")


# ─────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────

@dataclass
class ZoneSpec:
    zone_id: int
    name: str
    polygon: List[List[int]]
    baseline_median_motion: float
    baseline_variance: float
    center: List[int]
    is_estimated: bool = False      # True = spatial-gap estimate, no reliable YOLO detection
    zone_confidence: float = 1.0   # 0–1, fraction of calibration frames this position appeared
    location_desc: str = ""        # Human-readable physical seating position (e.g. Row 1 Back-Left)

@dataclass
class ZoneMap:
    zones: List[ZoneSpec]
    frame_shape: Tuple[int, int]
    calibration_frames_count: int
    timestamp: float
    reference_frame_path: str = ""


# ─────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────

def _iou(a: Tuple[int,int,int,int], b: Tuple[int,int,int,int]) -> float:
    ax1,ay1 = a[0], a[1]; ax2,ay2 = a[0]+a[2], a[1]+a[3]
    bx1,by1 = b[0], b[1]; bx2,by2 = b[0]+b[2], b[1]+b[3]
    ix = max(0, min(ax2,bx2) - max(ax1,bx1))
    iy = max(0, min(ay2,by2) - max(ay1,by1))
    inter = ix * iy
    union = a[2]*a[3] + b[2]*b[3] - inter
    return inter / (union + 1e-6)

def _center_dist(a: Tuple[int,int,int,int], b: Tuple[int,int,int,int]) -> float:
    cax, cay = a[0]+a[2]/2, a[1]+a[3]/2
    cbx, cby = b[0]+b[2]/2, b[1]+b[3]/2
    return float(np.sqrt((cax-cbx)**2 + (cay-cby)**2))

def _make_polygon(bx, by, bw, bh, padding_margin, padding_ratio, w_frame, h_frame):
    pad_w = max(4, min(padding_margin, int(bw * padding_ratio)))
    pad_h = max(4, min(padding_margin, int(bh * padding_ratio)))
    x1 = max(0, bx - pad_w)
    y1 = max(0, by - pad_h)
    x2 = min(w_frame, bx + bw + pad_w)
    y2 = min(h_frame, by + bh + pad_h + 4)
    return [[x1,y1],[x2,y1],[x2,y2],[x1,y2]], x1, y1, x2, y2

def _nms(boxes_confs: List[Tuple[Tuple[int,int,int,int], float]],
         iou_thresh: float = 0.4) -> List[Tuple[Tuple[int,int,int,int], float]]:
    """Simple greedy NMS. boxes_confs = list of ((x,y,w,h), conf)."""
    if not boxes_confs:
        return []
    boxes_confs = sorted(boxes_confs, key=lambda x: -x[1])
    kept = []
    suppressed = [False] * len(boxes_confs)
    for i, (box_i, conf_i) in enumerate(boxes_confs):
        if suppressed[i]:
            continue
        kept.append((box_i, conf_i))
        for j in range(i+1, len(boxes_confs)):
            if not suppressed[j] and _iou(box_i, boxes_confs[j][0]) > iou_thresh:
                suppressed[j] = True
    return kept


# ─────────────────────────────────────────────────────────
# Pass 1: SAHI full-frame detection (existing behaviour)
# ─────────────────────────────────────────────────────────

def _sahi_detect(color_frame: np.ndarray, detection_model,
                 conf_thresh: float, slice_size: int = 256,
                 overlap: float = 0.4) -> List[Tuple[Tuple[int,int,int,int], float]]:
    """Runs SAHI sliced prediction with small tiles for better small-object coverage."""
    from sahi.predict import get_sliced_prediction
    result = get_sliced_prediction(
        color_frame, detection_model,
        slice_height=slice_size, slice_width=slice_size,
        overlap_height_ratio=overlap, overlap_width_ratio=overlap,
        postprocess_type="NMS",
        verbose=0
    )
    out = []
    for obj in result.object_prediction_list:
        cls = obj.category.name.lower()
        if obj.score.value >= conf_thresh and cls not in ("phone", "chit"):
            b = obj.bbox.to_xywh()
            out.append(((int(b[0]),int(b[1]),int(b[2]),int(b[3])), float(obj.score.value)))
    return out


# ─────────────────────────────────────────────────────────
# Pass 2: Tiled + 2× upscale detection
# ─────────────────────────────────────────────────────────

def _tiled_upscale_detect(color_frame: np.ndarray, detection_model,
                           conf_thresh: float,
                           tile_rows: int = 3, tile_cols: int = 3,
                           upscale: float = 2.0) -> List[Tuple[Tuple[int,int,int,int], float]]:
    """
    Divides the frame into a grid of overlapping tiles, upscales each tile by
    `upscale` before running YOLO, then remaps coordinates back to the original
    frame. This allows detection of students that occupy very few pixels.
    """
    h, w = color_frame.shape[:2]
    overlap = 0.3

    step_x = int(w / (tile_cols - overlap * (tile_cols - 1)))
    step_y = int(h / (tile_rows - overlap * (tile_rows - 1)))
    tile_w = int(step_x * (1 + overlap))
    tile_h = int(step_y * (1 + overlap))

    from sahi.predict import get_sliced_prediction
    all_boxes = []

    for row in range(tile_rows):
        for col in range(tile_cols):
            ox = min(col * step_x, w - tile_w)
            oy = min(row * step_y, h - tile_h)
            ox = max(0, ox); oy = max(0, oy)
            x2 = min(ox + tile_w, w); y2 = min(oy + tile_h, h)
            tile = color_frame[oy:y2, ox:x2]
            if tile.size == 0:
                continue

            # 2× upscale
            th, tw = tile.shape[:2]
            tile_up = cv2.resize(tile, (int(tw * upscale), int(th * upscale)),
                                 interpolation=cv2.INTER_LINEAR)

            # Run SAHI on upscaled tile with moderate slice size
            result = get_sliced_prediction(
                tile_up, detection_model,
                slice_height=min(256, tile_up.shape[0]),
                slice_width=min(256, tile_up.shape[1]),
                overlap_height_ratio=0.2, overlap_width_ratio=0.2,
                postprocess_type="NMS", verbose=0
            )
            for obj in result.object_prediction_list:
                cls = obj.category.name.lower()
                if obj.score.value < conf_thresh or cls in ("phone", "chit"):
                    continue
                b = obj.bbox.to_xywh()
                # Remap from upscaled-tile coords back to original-frame coords
                rx = int(ox + b[0] / upscale)
                ry = int(oy + b[1] / upscale)
                rw = int(b[2] / upscale)
                rh = int(b[3] / upscale)
                # Clamp to frame
                rx = max(0, min(rx, w-1)); ry = max(0, min(ry, h-1))
                rw = min(rw, w-rx); rh = min(rh, h-ry)
                if rw > 5 and rh > 5:
                    all_boxes.append(((rx, ry, rw, rh), float(obj.score.value)))

    return all_boxes


# ─────────────────────────────────────────────────────────
# Multi-frame aggregation
# ─────────────────────────────────────────────────────────

def _aggregate_multiframe(
    per_frame_boxes: List[List[Tuple[Tuple[int,int,int,int], float]]],
    cluster_dist: float = 60.0,
    iou_thresh: float = 0.20,
    min_frame_fraction: float = 0.05
) -> List[Tuple[Tuple[int,int,int,int], float]]:
    """
    Aggregates person detections across multiple calibration frames.
    Returns stable clusters with confidence = fraction_of_frames_appeared.

    A position that appears in many frames gets high confidence.
    A position that appears only once gets low confidence but is still kept.
    """
    # Flatten all detections into one list tagged with (box, conf, frame_idx)
    clusters: List[Dict] = []

    for frame_idx, frame_boxes in enumerate(per_frame_boxes):
        for (box, conf) in frame_boxes:
            matched = None
            for c in clusters:
                if (_iou(box, c['box']) >= iou_thresh or
                        _center_dist(box, c['box']) <= cluster_dist):
                    matched = c
                    break
            if matched:
                matched['detections'].append((box, conf, frame_idx))
                # Update cluster bbox to running union
                mx = min(matched['box'][0], box[0])
                my = min(matched['box'][1], box[1])
                mx2 = max(matched['box'][0]+matched['box'][2], box[0]+box[2])
                my2 = max(matched['box'][1]+matched['box'][3], box[1]+box[3])
                matched['box'] = (mx, my, mx2-mx, my2-my)
            else:
                clusters.append({'box': box, 'detections': [(box, conf, frame_idx)]})

    n_frames = len(per_frame_boxes)
    result = []
    for c in clusters:
        unique_frames = len(set(fi for _,_,fi in c['detections']))
        frac = unique_frames / max(n_frames, 1)
        if frac < min_frame_fraction:
            continue
        avg_conf = float(np.mean([co for _,co,_ in c['detections']]))
        # Use median bbox for stability
        xs = [b[0] for b,_,_ in c['detections']]
        ys = [b[1] for b,_,_ in c['detections']]
        ws = [b[2] for b,_,_ in c['detections']]
        hs = [b[3] for b,_,_ in c['detections']]
        stable_box = (int(np.median(xs)), int(np.median(ys)),
                      int(np.median(ws)), int(np.median(hs)))
        peak_conf = max(co for _,co,_ in c['detections'])
        # zone_confidence = standardized calibration reliability (50% temporal presence + 50% peak confidence)
        zone_conf = round(0.50 * frac + 0.50 * min(1.0, 2.5 * peak_conf), 3)
        result.append((stable_box, zone_conf))

    return result


# ─────────────────────────────────────────────────────────
# Spatial-gap estimation for missing students
# ─────────────────────────────────────────────────────────

def _estimate_missing_zones(
    detected: List[Tuple[Tuple[int,int,int,int], float]],
    expected_count: int,
    frame_h: int, frame_w: int,
    existing_zone_specs: List  # list of ZoneSpec-like objects
) -> List[Tuple[Tuple[int,int,int,int], float]]:
    """
    If detected < expected_count, estimate probable desk positions by
    analysing the spatial grid of existing detections:

    Strategy
    --------
    1. Compute the median bbox size of confirmed detections.
    2. Model the classroom as a 2-D point cloud and find regions that are
       spatially isolated from all confirmed zones.
    3. Fill those gaps with estimated zones of median size.

    Returns estimated boxes as list of ((x,y,w,h), confidence=0.0)
    so the caller knows they are estimates.
    """
    if not detected or len(detected) >= expected_count:
        return []

    missing = expected_count - len(detected)

    # Median size of confirmed bboxes — use this for estimated zones
    ws = [d[0][2] for d in detected]
    hs = [d[0][3] for d in detected]
    med_w = max(20, int(np.median(ws))) if ws else 60
    med_h = max(20, int(np.median(hs))) if hs else 80

    # Centers of confirmed detections
    det_centers = [(d[0][0]+d[0][2]//2, d[0][1]+d[0][3]//2) for d in detected]

    # Build a grid of candidate positions across the frame
    # (coarser than the frame resolution — we don't want micro-gaps)
    stride_x = max(med_w, 60)
    stride_y = max(med_h, 60)
    candidates = []
    for gy in range(stride_y//2, frame_h - stride_y//2, stride_y):
        for gx in range(stride_x//2, frame_w - stride_x//2, stride_x):
            # Skip if too close to any confirmed detection
            too_close = any(
                abs(gx - cx) < stride_x * 0.8 and abs(gy - cy) < stride_y * 0.8
                for cx, cy in det_centers
            )
            if not too_close:
                candidates.append((gx, gy))

    if not candidates:
        return []

    # Sort candidates by their minimum distance to any confirmed detection
    # — prefer positions that are near other students (likely desk rows)
    def min_dist_to_detected(pt):
        if not det_centers:
            return 0
        return min(np.sqrt((pt[0]-cx)**2+(pt[1]-cy)**2) for cx,cy in det_centers)

    candidates.sort(key=min_dist_to_detected)

    # Also filter out candidates that are too close to image borders
    border_margin = med_w // 2
    candidates = [
        c for c in candidates
        if (c[0] > border_margin and c[0] < frame_w - border_margin and
            c[1] > border_margin and c[1] < frame_h - border_margin)
    ]

    estimated = []
    used_centers = list(det_centers)
    for gx, gy in candidates:
        if len(estimated) >= missing:
            break
        # Check not too close to already-picked estimates
        too_close = any(
            abs(gx-ux) < stride_x*0.8 and abs(gy-uy) < stride_y*0.8
            for ux,uy in used_centers
        )
        if not too_close:
            ex = max(0, gx - med_w//2)
            ey = max(0, gy - med_h//2)
            ew = min(med_w, frame_w - ex)
            eh = min(med_h, frame_h - ey)
            estimated.append(((ex, ey, ew, eh), 0.0))  # conf=0.0 marks as estimated
            used_centers.append((gx, gy))

    logger.info(f"Estimated {len(estimated)} additional zones from spatial gap analysis.")
    return estimated


# ─────────────────────────────────────────────────────────
# Main calibration function
# ─────────────────────────────────────────────────────────

def calibrate_zones_stage(
    preprocessed_stream: Generator[PreprocessedFrame, None, None],
    config_dict: dict
) -> ZoneMap:
    calib_cfg = config_dict.get('zone_calibration', {})
    calib_frames_count = calib_cfg.get('calibration_window_frames', 100)
    calib_conf_thresh = calib_cfg.get('calibration_confidence_threshold', 0.10)
    stability_thresh = calib_cfg.get('centroid_stability_threshold', 60.0)
    padding_ratio = calib_cfg.get('padding_ratio', 0.25)
    padding_margin = calib_cfg.get('padding_margin', 20)
    expected_seats = calib_cfg.get('expected_seat_count', 8)
    zone_map_path = calib_cfg.get('zone_map_path', 'outputs/zones/zone_map.json')
    preview_path = calib_cfg.get('preview_path', 'outputs/zones/zone_calibration_preview.jpg')
    tile_rows = calib_cfg.get('tile_rows', 2)
    tile_cols = calib_cfg.get('tile_cols', 2)
    upscale_factor = calib_cfg.get('upscale_factor', 2.0)
    min_frame_fraction = calib_cfg.get('min_frame_fraction', 0.05)
    max_sample_frames = calib_cfg.get('max_calib_sample_frames', 10)
    enable_upscale_pass = calib_cfg.get('enable_upscale_pass', False)

    import torch
    obj_cfg = config_dict.get('object_detection', {})
    model_path = obj_cfg.get('model_path', 'best.pt')
    for fallback in ['best.pt', 'models/best.pt', 'yolov8n.pt', 'models/yolov8n.pt']:
        if os.path.exists(fallback):
            model_path = fallback
            break

    device_req = str(obj_cfg.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')).strip()
    if device_req.lower() == 'auto' or device_req.lower().startswith('cuda'):
        if torch.cuda.is_available():
            device = 'cuda:0' if device_req.lower() in ('auto', 'cuda') else device_req
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU Acceleration active for Zone Calibration on {gpu_name} (Device: {device})")
        else:
            logger.warning(f"CUDA requested ({device_req}) but CUDA is not available. Falling back to CPU.")
            device = 'cpu'
    else:
        device = device_req

    logger.info(f"Starting Zone Calibration -- hierarchy: SAHI -> {'Tiled-2x -> ' if enable_upscale_pass else ''}MultiFrame -> GapEstimate (Device: {device})")
    logger.info(f"Config: frames={calib_frames_count}, conf={calib_conf_thresh}, expected_seats={expected_seats}, upscale_pass={enable_upscale_pass}")

    # ── Buffer calibration frames
    calibration_frames: List[PreprocessedFrame] = []
    for _ in range(calib_frames_count):
        try:
            calibration_frames.append(next(preprocessed_stream))
        except StopIteration:
            break

    if not calibration_frames:
        logger.error("No frames available for zone calibration.")
        return ZoneMap(zones=[], frame_shape=(480, 640), calibration_frames_count=0, timestamp=0.0)

    sample_frame = calibration_frames[-1]
    sample_color_frame = sample_frame.color_frame
    h_frame, w_frame = sample_color_frame.shape[:2]

    # ── Load YOLO model
    from sahi import AutoDetectionModel
    detection_model = AutoDetectionModel.from_pretrained(
        model_type="yolov8",
        model_path=model_path,
        confidence_threshold=calib_conf_thresh,
        device=device
    )

    # ── Keyframe-Based Robust Multi-Pass Calibration
    n_frames = len(calibration_frames)
    # Sample 5 distributed keyframes across the full calibration window
    keyframe_indices = sorted(list(set([
        0,
        n_frames // 4,
        n_frames // 2,
        (3 * n_frames) // 4,
        max(0, n_frames - 1)
    ])))
    logger.info(f"Robust Keyframe Calibration: Running deep multi-pass hierarchy on {len(keyframe_indices)} keyframes (indices: {keyframe_indices}).")

    per_frame_boxes: List[List[Tuple[Tuple[int,int,int,int], float]]] = []
    all_raw_person_boxes = []

    for fi in keyframe_indices:
        p_frame = calibration_frames[fi]
        frame_boxes: List[Tuple[Tuple[int,int,int,int], float]] = []

        # Pass 1: SAHI small-tile sliced detection (192px with 0.45 overlap)
        pass1 = _sahi_detect(p_frame.color_frame, detection_model,
                              calib_conf_thresh, slice_size=192, overlap=0.45)
        frame_boxes.extend(pass1)

        # Pass 2: Optional Tiled 2x-upscale detection for far/small students (if enabled)
        if enable_upscale_pass:
            pass2 = _tiled_upscale_detect(p_frame.color_frame, detection_model,
                                           calib_conf_thresh, tile_rows, tile_cols,
                                           upscale_factor)
            frame_boxes.extend(pass2)

        # NMS within frame
        frame_boxes = _nms(frame_boxes, iou_thresh=0.35)
        per_frame_boxes.append(frame_boxes)
        all_raw_person_boxes.extend([b for b, _ in frame_boxes])

    logger.info(f"Total raw candidate detections: {sum(len(f) for f in per_frame_boxes)} across {len(per_frame_boxes)} keyframes.")

    # ── Multi-frame aggregation across keyframes with tight cluster distance
    stable_detections = _aggregate_multiframe(
        per_frame_boxes,
        cluster_dist=35.0,
        iou_thresh=0.20,
        min_frame_fraction=0.20
    )

    # ── Suppress intra-person duplicate detections (e.g. head/torso vs full-body)
    def _suppress_intra_person(boxes_confs):
        boxes_confs = sorted(boxes_confs, key=lambda x: -x[1])
        kept = []
        for b, conf in boxes_confs:
            cx, cy = b[0] + b[2]//2, b[1] + b[3]//2
            duplicate = False
            for kb, kconf in kept:
                k_cx, k_cy = kb[0] + kb[2]//2, kb[1] + kb[3]//2
                dist = np.sqrt((cx - k_cx)**2 + (cy - k_cy)**2)
                ax1, ay1, ax2, ay2 = b[0], b[1], b[0]+b[2], b[1]+b[3]
                bx1, by1, bx2, by2 = kb[0], kb[1], kb[0]+kb[2], kb[1]+kb[3]
                ix = max(0, min(ax2,bx2) - max(ax1,bx1))
                iy = max(0, min(ay2,by2) - max(ay1,by1))
                iou = (ix * iy) / (b[2]*b[3] + kb[2]*kb[3] - ix*iy + 1e-6)

                if iou > 0.15 or dist < 42.0 or (kb[0] <= cx <= kb[0]+kb[2] and kb[1] <= cy <= kb[1]+kb[3]):
                    duplicate = True
                    break
            if not duplicate:
                kept.append((b, conf))
        return kept

    stable_detections = _suppress_intra_person(stable_detections)
    # Filter out spurious noise boxes < 20px and low confidence noise
    stable_detections = [b for b in stable_detections if b[1] >= 0.04 and b[0][2] >= 20 and b[0][3] >= 25]

    # Sort top-left→bottom-right (row-major)
    stable_detections.sort(key=lambda d: (d[0][1] // 50, d[0][0]))

    logger.info(f"After multi-frame aggregation & intra-person suppression: {len(stable_detections)} stable detected zones.")

    # ── Webcam / Single-User Adaptive Zone Handling ──
    if len(stable_detections) <= 2:
        logger.info("Single-User / Live Webcam Mode Detected: Adapting primary student proctoring zone.")
        primary_box = (int(w_frame * 0.05), int(h_frame * 0.05), int(w_frame * 0.90), int(h_frame * 0.90))
        if not stable_detections:
            stable_detections = [(primary_box, 0.99)]
        elif len(stable_detections) == 1:
            # Expand single detection slightly for full coverage
            b, c = stable_detections[0]
            eb = (max(0, b[0] - 30), max(0, b[1] - 30), min(w_frame, b[2] + 60), min(h_frame, b[3] + 60))
            stable_detections = [(eb, c)]

    # ── Spatial-gap estimation for missing zones (if explicit expected_seats set higher)
    estimated_boxes = []
    if len(stable_detections) > 2 and len(stable_detections) < expected_seats:
        estimated_boxes = _estimate_missing_zones(
            stable_detections, expected_seats, h_frame, w_frame, []
        )

    # ── Background subtractor for baseline motion across calibration window
    mog2 = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)
    frame_motion_masks = []
    for p_frame in calibration_frames:
        mask = mog2.apply(p_frame.gray_frame)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        frame_motion_masks.append(mask)

    # ── Build ZoneSpec list (DETECTED zones first, then ESTIMATED)
    zone_specs: List[ZoneSpec] = []
    idx = 1

    def _make_polygon(bx, by, bw, bh, padding_margin, padding_ratio, w_frame, h_frame):
        pad_w = max(4, min(padding_margin, int(bw * padding_ratio)))
        pad_h = max(4, min(padding_margin, int(bh * padding_ratio)))
        x1 = max(0, bx - pad_w)
        y1 = max(0, by - pad_h)
        x2 = min(w_frame, bx + bw + pad_w)
        y2 = min(h_frame, by + bh + pad_h + 4)
        return [[x1,y1],[x2,y1],[x2,y2],[x1,y2]], x1, y1, x2, y2

    def _zone_baseline(frame_motion_masks, y1, x1, y2, x2):
        scores = []
        for mask in frame_motion_masks:
            roi = mask[y1:y2, x1:x2]
            if roi.size > 0:
                scores.append(float(np.count_nonzero(roi)) / float(roi.size))
            else:
                scores.append(0.0)
        return (float(np.median(scores)) if scores else 0.0001,
                float(np.var(scores)) if scores else 0.00001)

    def _compute_location_desc(cx: int, cy: int, w: int, h: int) -> str:
        row_str = "Row 1 (Back)" if cy < h * 0.38 else ("Row 2 (Middle)" if cy < h * 0.62 else "Row 3 (Front)")
        col_str = "Left Desk" if cx < w * 0.28 else ("Center-Left Desk" if cx < w * 0.48 else ("Center-Right Desk" if cx < w * 0.72 else "Right Desk"))
        return f"{row_str} -- {col_str}"

    for (bx, by, bw, bh), zone_conf in stable_detections:
        polygon, x1, y1, x2, y2 = _make_polygon(bx, by, bw, bh, padding_margin, padding_ratio, w_frame, h_frame)
        base_med, base_var = _zone_baseline(frame_motion_masks, y1, x1, y2, x2)
        cx, cy = bx + bw//2, by + bh//2
        z = ZoneSpec(
            zone_id=idx,
            name=f"S{idx}",
            polygon=polygon,
            baseline_median_motion=round(base_med, 6),
            baseline_variance=round(base_var, 6),
            center=[cx, cy],
            is_estimated=False,
            zone_confidence=round(zone_conf, 3),
            location_desc=_compute_location_desc(cx, cy, w_frame, h_frame)
        )
        zone_specs.append(z)
        idx += 1

    for (bx, by, bw, bh), _ in estimated_boxes:
        polygon, x1, y1, x2, y2 = _make_polygon(bx, by, bw, bh, padding_margin, padding_ratio, w_frame, h_frame)
        base_med, base_var = _zone_baseline(frame_motion_masks, y1, x1, y2, x2)
        cx, cy = bx + bw//2, by + bh//2
        z = ZoneSpec(
            zone_id=idx,
            name=f"S{idx}",
            polygon=polygon,
            baseline_median_motion=round(base_med, 6),
            baseline_variance=round(base_var, 6),
            center=[cx, cy],
            is_estimated=True,
            zone_confidence=0.0,
            location_desc=_compute_location_desc(cx, cy, w_frame, h_frame)
        )
        zone_specs.append(z)
        idx += 1

    detected_count = sum(1 for z in zone_specs if not z.is_estimated)
    estimated_count = sum(1 for z in zone_specs if z.is_estimated)
    logger.info(f"Final ZoneMap: {detected_count} DETECTED + {estimated_count} ESTIMATED = {len(zone_specs)} total zones.")

    zone_map = ZoneMap(
        zones=zone_specs,
        frame_shape=(h_frame, w_frame),
        calibration_frames_count=len(calibration_frames),
        timestamp=sample_frame.timestamp
    )

    # ── Save zone_map.json
    os.makedirs(os.path.dirname(zone_map_path), exist_ok=True)
    with open(zone_map_path, 'w') as f:
        json.dump([asdict(z) for z in zone_specs], f, indent=2)
    logger.info(f"Locked and saved ZoneMap ({len(zone_specs)} zones) to: {zone_map_path}")

    # ── Save reference frame
    ref_frame_path = os.path.join(os.path.dirname(zone_map_path), "reference_frame.jpg")
    cv2.imwrite(ref_frame_path, sample_color_frame)
    zone_map.reference_frame_path = ref_frame_path

    # ── Save calibration preview (DETECTED=green solid, ESTIMATED=orange dashed)
    save_calibration_preview(sample_color_frame, all_raw_person_boxes, zone_specs, preview_path)

    return zone_map


# ─────────────────────────────────────────────────────────
# Calibration preview visualisation
# ─────────────────────────────────────────────────────────

def _draw_dashed_rect(img, x1, y1, x2, y2, color, thickness=2, dash_len=10):
    """Draws a dashed rectangle to visually distinguish estimated zones."""
    pts = [(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
    for i in range(len(pts)-1):
        p1, p2 = pts[i], pts[i+1]
        dx = p2[0]-p1[0]; dy = p2[1]-p1[1]
        dist = max(1, int(np.sqrt(dx*dx+dy*dy)))
        for d in range(0, dist, dash_len*2):
            t0 = d/dist; t1 = min((d+dash_len)/dist, 1.0)
            s = (int(p1[0]+t0*dx), int(p1[1]+t0*dy))
            e = (int(p1[0]+t1*dx), int(p1[1]+t1*dy))
            cv2.line(img, s, e, color, thickness)


def save_calibration_preview(
    color_frame: np.ndarray,
    raw_person_bboxes: List[Tuple[int,int,int,int]],
    zone_specs,
    output_path: str
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = color_frame.copy()
    overlay = img.copy()

    # Draw raw YOLO candidate bboxes (thin green)
    for (px, py, pw, ph) in raw_person_bboxes:
        cv2.rectangle(img, (px,py), (px+pw,py+ph), (0,200,0), 1)

    detected_color  = (0, 255,  80)   # bright green — DETECTED
    estimated_color = (0, 165, 255)   # orange       — ESTIMATED

    for z in zone_specs:
        poly_pts = np.array(z.polygon, dtype=np.int32).reshape((-1,1,2))
        color = estimated_color if z.is_estimated else detected_color

        cv2.fillPoly(overlay, [poly_pts], color)

        x1, y1 = z.polygon[0]
        x2, y2 = z.polygon[2]

        if z.is_estimated:
            _draw_dashed_rect(img, x1, y1, x2, y2, color, thickness=2)
        else:
            cv2.polylines(img, [poly_pts], isClosed=True, color=color, thickness=2)

        tag = "EST" if z.is_estimated else f"{int(z.zone_confidence*100)}%"
        label = f"{z.name} [{tag}]"
        cv2.putText(img, label, (x1+4, y1+16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,0), 3)
        cv2.putText(img, label, (x1+4, y1+16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)

    cv2.addWeighted(overlay, 0.22, img, 0.78, 0, img)

    # Header
    cv2.rectangle(img, (0,0), (img.shape[1], 44), (10,10,10), -1)
    det_n   = sum(1 for z in zone_specs if not z.is_estimated)
    est_n   = sum(1 for z in zone_specs if z.is_estimated)
    cv2.putText(img,
        f"STAGE 1.5 ZONE CALIBRATION  |  DETECTED: {det_n} (green)   ESTIMATED: {est_n} (orange)",
        (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 1)

    cv2.imwrite(output_path, img)
    logger.info(f"Saved calibration preview to: {output_path} "
                f"(DETECTED={det_n}, ESTIMATED={est_n})")
