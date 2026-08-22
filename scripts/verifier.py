import os
from pathlib import Path
from utils import setup_logger
from config import MERGED_DIR, TARGET_CLASSES

logger = setup_logger("verifier")

def verify_dataset():
    logger.info("Starting dataset verification")
    if not MERGED_DIR.exists():
        logger.error(f"Merged dataset not found at {MERGED_DIR}")
        return False
        
    num_classes = len(TARGET_CLASSES)
    
    issues_found = 0
    checked_files = 0
    
    for split in ["train", "valid", "test"]:
        lbl_dir = MERGED_DIR / split / "labels"
        if not lbl_dir.exists():
            continue
            
        for lbl_file in lbl_dir.glob("*.txt"):
            if not lbl_file.is_file():
                continue
                
            checked_files += 1
            try:
                with open(lbl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        parts = line.strip().split()
                        if not parts:
                            continue
                            
                        if len(parts) != 5:
                            logger.error(f"{lbl_file.name}:{line_num} Malformed line (needs 5 values)")
                            issues_found += 1
                            continue
                            
                        try:
                            cls_id = int(parts[0])
                            x = float(parts[1])
                            y = float(parts[2])
                            w = float(parts[3])
                            h = float(parts[4])
                        except ValueError:
                            logger.error(f"{lbl_file.name}:{line_num} Non-numeric values found")
                            issues_found += 1
                            continue
                            
                        if not (0 <= cls_id < num_classes):
                            logger.error(f"{lbl_file.name}:{line_num} Invalid class ID {cls_id}")
                            issues_found += 1
                            
                        if w <= 0 or h <= 0:
                            logger.error(f"{lbl_file.name}:{line_num} Invalid width/height ({w}, {h})")
                            issues_found += 1
                            
                        if x - w/2 < 0 or x + w/2 > 1 or y - h/2 < 0 or y + h/2 > 1:
                            logger.error(f"{lbl_file.name}:{line_num} Box out of bounds (x={x}, y={y}, w={w}, h={h})")
                            issues_found += 1
                            
            except Exception as e:
                logger.error(f"Failed to read {lbl_file.name}: {e}")
                issues_found += 1
                
    if issues_found == 0:
        logger.info(f"Verification successful. Checked {checked_files} label files with 0 issues.")
        return True
    else:
        logger.warning(f"Verification completed with {issues_found} issues across {checked_files} files.")
        return False

if __name__ == "__main__":
    verify_dataset()
