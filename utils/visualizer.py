import cv2
import numpy as np
import os

def draw_text(img, text, pos=(10, 30), color=(0, 255, 0)):
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    return img

def visualize_stage_0(debug_cfg, frame, frame_no, timestamp):
    if not debug_cfg or not debug_cfg.get('enabled', False): return
    if not debug_cfg.get('save_images', False): return
    if frame_no % debug_cfg.get('save_every_n_frames', 1) != 0: return
    
    out_dir = os.path.join(debug_cfg.get('output_dir', 'outputs/debug/'), 'stage0')
    os.makedirs(out_dir, exist_ok=True)
    
    img = draw_text(frame.copy(), f"Stage 0 (Original) | Frame: {frame_no} | Time: {timestamp:.2f}s")
    cv2.imwrite(os.path.join(out_dir, f"frame_{frame_no:06d}.png"), img)

def visualize_stage_1(debug_cfg, original, resized, gray, clahe_out, final, frame_no, timestamp):
    if not debug_cfg or not debug_cfg.get('enabled', False): return
    if not debug_cfg.get('save_images', False): return
    if frame_no % debug_cfg.get('save_every_n_frames', 1) != 0: return
    
    out_dir = os.path.join(debug_cfg.get('output_dir', 'outputs/debug/'), 'stage1')
    os.makedirs(out_dir, exist_ok=True)
    
    # Resize all to match height of 'resized'
    h = resized.shape[0]
    
    def format_img(img, title):
        w = int(img.shape[1] * (h / img.shape[0]))
        img_res = cv2.resize(img, (w, h))
        if len(img_res.shape) == 2:
            img_res = cv2.cvtColor(img_res, cv2.COLOR_GRAY2BGR)
        return draw_text(img_res, title)

    imgs = [
        format_img(original, "Original"),
        format_img(resized, "Resized"),
        format_img(gray, "Gray"),
        format_img(clahe_out, "CLAHE"),
        format_img(final, "Final")
    ]
    
    combined = np.hstack(imgs)
    draw_text(combined, f"Frame: {frame_no} | Time: {timestamp:.2f}s", pos=(10, h - 20), color=(0, 0, 255))
    
    cv2.imwrite(os.path.join(out_dir, f"frame_{frame_no:06d}.png"), combined)

def visualize_stage_2a(debug_cfg, gray, raw_mask, clean_mask, color, boxes, frame_no, pct, warmup, suppressed):
    if not debug_cfg or not debug_cfg.get('enabled', False): return
    if not debug_cfg.get('save_images', False): return
    if frame_no % debug_cfg.get('save_every_n_frames', 1) != 0: return
    
    out_dir = os.path.join(debug_cfg.get('output_dir', 'outputs/debug/'), 'stage2a')
    os.makedirs(out_dir, exist_ok=True)
    
    h = gray.shape[0]
    
    def format_img(img, title):
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return draw_text(img.copy(), title)

    color_boxes = format_img(color, "BBoxes")
    for (x, y, w, box_h) in boxes:
        cv2.rectangle(color_boxes, (x, y), (x+w, y+box_h), (0, 0, 255), 2)
        
    imgs = [
        format_img(gray, "Gray"),
        format_img(raw_mask, "Raw Mask"),
        format_img(clean_mask, "Clean Mask"),
        color_boxes
    ]
    
    combined = np.hstack(imgs)
    
    info = f"Frame: {frame_no} | Motion: {pct:.1f}% | Warmup: {warmup} | Suppressed: {suppressed}"
    draw_text(combined, info, pos=(10, h - 20), color=(0, 0, 255))
    
    cv2.imwrite(os.path.join(out_dir, f"frame_{frame_no:06d}.png"), combined)

def visualize_stage_2b(debug_cfg, color, detections, frame_no, timestamp):
    if not debug_cfg or not debug_cfg.get('enabled', False): return
    if not debug_cfg.get('save_images', False): return
    if frame_no % debug_cfg.get('save_every_n_frames', 1) != 0: return
    
    out_dir = os.path.join(debug_cfg.get('output_dir', 'outputs/debug/'), 'stage2b')
    os.makedirs(out_dir, exist_ok=True)
    
    img = color.copy()
    for det in detections:
        x, y, w, h = det.bbox
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(img, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
    draw_text(img, f"Stage 2B (Objects: {len(detections)}) | Frame: {frame_no} | Time: {timestamp:.2f}s", color=(0, 0, 255))
    cv2.imwrite(os.path.join(out_dir, f"frame_{frame_no:06d}.png"), img)

def visualize_stage_3(debug_cfg, color, tracks, zones, frame_no, timestamp):
    if not debug_cfg or not debug_cfg.get('enabled', False): return
    if not debug_cfg.get('save_images', False): return
    if frame_no % debug_cfg.get('save_every_n_frames', 1) != 0: return
    
    out_dir = os.path.join(debug_cfg.get('output_dir', 'outputs/debug/'), 'stage3')
    os.makedirs(out_dir, exist_ok=True)
    
    img = color.copy()
    
    # Draw zones
    if zones:
        for z in zones:
            pts = np.array(z['polygon'], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (0, 255, 255), 2)
            cv2.putText(img, z['name'], tuple(pts[0][0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
    # Draw tracks
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    for track in tracks:
        x, y, w, h = track['bbox']
        color = colors[track['track_id'] % len(colors)]
        cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
        
        # Center point
        cx, cy = x + w//2, y + h//2
        cv2.circle(img, (cx, cy), 4, color, -1)
        
        zone_str = f" | Zone: {track['zone_id']}" if track['zone_id'] is not None else ""
        label = f"ID:{track['track_id']} {track['class']}{zone_str}"
        cv2.putText(img, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
    draw_text(img, f"Stage 3 (Tracks: {len(tracks)}) | Frame: {frame_no} | Time: {timestamp:.2f}s", color=(0, 0, 255))
    cv2.imwrite(os.path.join(out_dir, f"frame_{frame_no:06d}.png"), img)
