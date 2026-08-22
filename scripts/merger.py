import os
import shutil
import hashlib
from pathlib import Path
from utils import setup_logger, write_yaml
from config import CLEANED_DIR, MERGED_DIR, TARGET_CLASSES, DATASETS

logger = setup_logger("merger")

def compute_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def merge_datasets():
    logger.info("Starting dataset merge")
    
    stats = {}
    for alias in DATASETS.keys():
        stats[alias] = {
            "Duplicate images removed": 0,
            "Final images": 0,
            "Final annotations": 0
        }
        
    if not CLEANED_DIR.exists():
        logger.error(f"Cleaned datasets directory not found: {CLEANED_DIR}")
        return stats
        
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    
    seen_hashes = set()
    
    for split in ["train", "valid", "test"]:
        out_img_dir = MERGED_DIR / split / "images"
        out_lbl_dir = MERGED_DIR / split / "labels"
        out_img_dir.mkdir(parents=True, exist_ok=True)
        out_lbl_dir.mkdir(parents=True, exist_ok=True)
        
        for alias in DATASETS.keys():
            clean_ds_dir = CLEANED_DIR / alias
            img_dir = clean_ds_dir / split / "images"
            lbl_dir = clean_ds_dir / split / "labels"
            
            if not img_dir.exists():
                continue
                
            for img_file in img_dir.glob("*.*"):
                if not img_file.is_file():
                    continue
                    
                lbl_file = lbl_dir / f"{img_file.stem}.txt"
                if not lbl_file.exists():
                    continue
                    
                img_hash = compute_hash(img_file)
                if img_hash in seen_hashes:
                    logger.debug(f"Duplicate image found, skipping: {img_file.name}")
                    stats[alias]["Duplicate images removed"] += 1
                    continue
                    
                seen_hashes.add(img_hash)
                
                new_stem = f"{alias}_{img_file.stem}"
                out_img_file = out_img_dir / f"{new_stem}{img_file.suffix}"
                out_lbl_file = out_lbl_dir / f"{new_stem}.txt"
                
                shutil.copy2(img_file, out_img_file)
                shutil.copy2(lbl_file, out_lbl_file)
                
                stats[alias]["Final images"] += 1
                
                with open(lbl_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    stats[alias]["Final annotations"] += len(lines)

    total_copied = sum(s["Final images"] for s in stats.values())
    total_dups = sum(s["Duplicate images removed"] for s in stats.values())
    logger.info(f"Merge complete. Copied {total_copied} images. Skipped {total_dups} duplicates.")
    
    final_yaml = {
        "path": ".",
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(TARGET_CLASSES),
        "names": TARGET_CLASSES
    }
    write_yaml(final_yaml, MERGED_DIR / "data.yaml")
    
    return stats

if __name__ == "__main__":
    merge_datasets()
