import json
import csv
from collections import defaultdict
from pathlib import Path
from utils import setup_logger
from config import MERGED_DIR, REPORTS_DIR, TARGET_CLASSES, DATASETS

logger = setup_logger("statistics")

def generate_statistics(clean_stats=None, merge_stats=None):
    logger.info("Generating dataset statistics and reports")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate statistics.json (Class counts from final merged dataset)
    class_counts = {cls: 0 for cls in TARGET_CLASSES}
    
    if MERGED_DIR.exists():
        for split in ["train", "valid", "test"]:
            lbl_dir = MERGED_DIR / split / "labels"
            if not lbl_dir.exists():
                continue
            for lbl_file in lbl_dir.glob("*.txt"):
                if not lbl_file.is_file():
                    continue
                with open(lbl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            try:
                                cls_id = int(parts[0])
                                if 0 <= cls_id < len(TARGET_CLASSES):
                                    class_counts[TARGET_CLASSES[cls_id]] += 1
                            except ValueError:
                                pass
                                
        stats_path = REPORTS_DIR / "statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(class_counts, f, indent=4)
        logger.info(f"Saved class statistics to {stats_path}")
    else:
        logger.warning(f"Merged directory {MERGED_DIR} not found. Cannot compute class counts.")

    # 2. Generate dataset_report.csv
    report_path = REPORTS_DIR / "dataset_report.csv"
    
    # Ensure stats are populated, even if empty
    if not clean_stats:
        clean_stats = {alias: {"Images": 0, "Annotations": 0, "Removed annotations": 0, "Empty labels": 0, "Skipped labels": 0} for alias in DATASETS}
    if not merge_stats:
        merge_stats = {alias: {"Duplicate images removed": 0, "Final images": 0, "Final annotations": 0} for alias in DATASETS}

    headers = [
        "Dataset", "Images", "Annotations", "Removed annotations", 
        "Empty labels", "Skipped labels", "Duplicate images removed", 
        "Final images", "Final annotations"
    ]
    
    with open(report_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for alias in DATASETS:
            c_s = clean_stats.get(alias, {})
            m_s = merge_stats.get(alias, {})
            row = [
                alias,
                c_s.get("Images", 0),
                c_s.get("Annotations", 0),
                c_s.get("Removed annotations", 0),
                c_s.get("Empty labels", 0),
                c_s.get("Skipped labels", 0),
                m_s.get("Duplicate images removed", 0),
                m_s.get("Final images", 0),
                m_s.get("Final annotations", 0)
            ]
            writer.writerow(row)
            
    logger.info(f"Saved dataset report to {report_path}")

if __name__ == "__main__":
    generate_statistics()
