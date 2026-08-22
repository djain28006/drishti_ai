import os
import random
from pathlib import Path
import cv2
from utils import setup_logger
from config import MERGED_DIR, VERIFICATION_DIR, TARGET_CLASSES

logger = setup_logger("visualizer")

COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    (0, 255, 255), (255, 0, 255), (128, 128, 128)
]

def draw_boxes(img_path, lbl_path, out_path):
    img = cv2.imread(str(img_path))
    if img is None:
        logger.error(f"Could not read image {img_path}")
        return False
        
    h_img, w_img = img.shape[:2]
    
    if lbl_path.exists():
        with open(lbl_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls_id = int(parts[0])
                    x_c = float(parts[1])
                    y_c = float(parts[2])
                    w = float(parts[3])
                    h = float(parts[4])
                    
                    # Convert to pixel coordinates
                    left = int((x_c - w/2) * w_img)
                    top = int((y_c - h/2) * h_img)
                    right = int((x_c + w/2) * w_img)
                    bottom = int((y_c + h/2) * h_img)
                    
                    color = COLORS[cls_id % len(COLORS)]
                    label_name = TARGET_CLASSES[cls_id] if cls_id < len(TARGET_CLASSES) else str(cls_id)
                    
                    cv2.rectangle(img, (left, top), (right, bottom), color, 2)
                    cv2.putText(img, label_name, (left, max(top - 5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
    cv2.imwrite(str(out_path), img)
    return True

def get_classes_in_label(lbl_path):
    classes = set()
    if lbl_path.exists():
        with open(lbl_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    try:
                        classes.add(int(parts[0]))
                    except ValueError:
                        pass
    return classes

def visualize_samples(num_samples_per_class=10):
    logger.info(f"Generating up to {num_samples_per_class} verification samples per class")
    if not MERGED_DIR.exists():
        logger.error("Merged dataset not found.")
        return
        
    class_samples = {cls: [] for cls in TARGET_CLASSES}
    
    # Collect images
    for split in ["train", "valid", "test"]:
        img_dir = MERGED_DIR / split / "images"
        if not img_dir.exists():
            continue
            
        for img_path in img_dir.glob("*.*"):
            if not img_path.is_file():
                continue
                
            lbl_path = MERGED_DIR / split / "labels" / f"{img_path.stem}.txt"
            img_classes = get_classes_in_label(lbl_path)
            
            for cls_id in img_classes:
                if 0 <= cls_id < len(TARGET_CLASSES):
                    cls_name = TARGET_CLASSES[cls_id]
                    if len(class_samples[cls_name]) < num_samples_per_class:
                        class_samples[cls_name].append((img_path, lbl_path))
            
            # Check if all classes have enough samples
            if all(len(samples) >= num_samples_per_class for samples in class_samples.values()):
                break
        else:
            continue
        break
        
    success_count = 0
    for cls_name, samples in class_samples.items():
        if not samples:
            logger.warning(f"No samples found for class '{cls_name}'.")
            continue
            
        class_out_dir = VERIFICATION_DIR / cls_name
        class_out_dir.mkdir(parents=True, exist_ok=True)
        
        for img_path, lbl_path in samples:
            out_path = class_out_dir / f"vis_{img_path.name}"
            if draw_boxes(img_path, lbl_path, out_path):
                success_count += 1
                
    logger.info(f"Successfully generated {success_count} class-specific visualizations in {VERIFICATION_DIR}")

if __name__ == "__main__":
    visualize_samples()
