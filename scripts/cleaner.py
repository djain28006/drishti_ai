import os
import shutil
import csv
from pathlib import Path
from utils import setup_logger, write_yaml
from config import DATASETS, CLEANED_DIR, SKIPPED_DIR, TARGET_CLASSES
from mapper import get_class_mapping

logger = setup_logger("cleaner")

def init_skipped_csvs():
    SKIPPED_DIR.mkdir(parents=True, exist_ok=True)
    for csv_name in ["missing_images.csv", "missing_labels.csv"]:
        csv_path = SKIPPED_DIR / csv_name
        if not csv_path.exists():
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["dataset_alias", "split", "filename"])

def log_skipped(dataset_alias, split, filename, reason):
    csv_name = "missing_images.csv" if reason == "missing_image" else "missing_labels.csv"
    csv_path = SKIPPED_DIR / csv_name
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([dataset_alias, split, filename])

def clean_dataset(dataset_alias, original_dir):
    logger.info(f"Cleaning dataset: {dataset_alias}")
    
    stats = {
        "Images": 0,
        "Annotations": 0,
        "Removed annotations": 0,
        "Empty labels": 0,
        "Skipped labels": 0
    }
    
    if not original_dir.exists():
        logger.error(f"Dataset directory not found: {original_dir}")
        return stats
        
    yaml_path = original_dir / "data.yaml"
    if not yaml_path.exists():
        logger.error(f"data.yaml not found in {original_dir}")
        return stats
        
    id_mapping = get_class_mapping(dataset_alias, yaml_path)
    
    clean_ds_dir = CLEANED_DIR / dataset_alias
    
    # Process splits
    for split in ["train", "valid", "test"]:
        img_dir = original_dir / split / "images"
        lbl_dir = original_dir / split / "labels"
        
        if not img_dir.exists() and not lbl_dir.exists():
            continue
            
        logger.info(f"Processing {split} split for {dataset_alias}")
        
        out_img_dir = clean_ds_dir / split / "images"
        out_lbl_dir = clean_ds_dir / split / "labels"
        out_img_dir.mkdir(parents=True, exist_ok=True)
        out_lbl_dir.mkdir(parents=True, exist_ok=True)
        
        img_stems = {f.stem: f for f in img_dir.glob("*.*") if f.is_file()} if img_dir.exists() else {}
        lbl_stems = {f.stem: f for f in lbl_dir.glob("*.txt") if f.is_file()} if lbl_dir.exists() else {}
        
        all_stems = set(img_stems.keys()).union(set(lbl_stems.keys()))
        
        for stem in all_stems:
            img_file = img_stems.get(stem)
            lbl_file = lbl_stems.get(stem)
            
            if not img_file:
                logger.warning(f"Missing image for label {lbl_file.name}")
                log_skipped(dataset_alias, split, lbl_file.name, "missing_image")
                stats["Skipped labels"] += 1
                continue
                
            if not lbl_file:
                logger.warning(f"Missing label for image {img_file.name}")
                log_skipped(dataset_alias, split, img_file.name, "missing_label")
                stats["Skipped labels"] += 1
                continue
                
            stats["Images"] += 1
            
            valid_lines = []
            with open(lbl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line_num, line in enumerate(lines, 1):
                    parts = line.strip().split()
                    if not parts:
                        continue
                    if len(parts) != 5:
                        logger.warning(f"Skipping malformed line in {lbl_file.name}:{line_num} (needs exactly 5 values)")
                        continue
                    try:
                        old_id = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        w = float(parts[3])
                        h = float(parts[4])
                        
                        if w <= 0 or h <= 0 or x - w/2 < 0 or x + w/2 > 1 or y - h/2 < 0 or y + h/2 > 1:
                            logger.warning(f"Skipping line with invalid coordinates in {lbl_file.name}:{line_num}")
                            continue
                            
                        stats["Annotations"] += 1
                        new_id = id_mapping.get(old_id, "REMOVE")
                        if new_id != "REMOVE":
                            new_line = f"{new_id} {x} {y} {w} {h}"
                            valid_lines.append(new_line)
                        else:
                            stats["Removed annotations"] += 1
                    except ValueError:
                        logger.warning(f"Skipping line with non-numeric values in {lbl_file.name}:{line_num}")
                        continue
                            
            if not valid_lines:
                stats["Empty labels"] += 1
                
            out_lbl_file = out_lbl_dir / f"{stem}.txt"
            with open(out_lbl_file, 'w', encoding='utf-8') as f:
                if valid_lines:
                    f.write("\n".join(valid_lines) + "\n")
                    
            out_img_file = out_img_dir / img_file.name
            shutil.copy2(img_file, out_img_file)
            
    corrected_yaml = {
        "path": ".",
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(TARGET_CLASSES),
        "names": TARGET_CLASSES
    }
    write_yaml(corrected_yaml, clean_ds_dir / "data.yaml")
    
    return stats

def run_cleaner():
    init_skipped_csvs()
    all_stats = {}
    for alias, dpath in DATASETS.items():
        all_stats[alias] = clean_dataset(alias, dpath)
    return all_stats
    
if __name__ == "__main__":
    run_cleaner()
