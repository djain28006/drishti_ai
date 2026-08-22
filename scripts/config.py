import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
CLEANED_DIR = BASE_DIR / "cleaned_datasets"
MERGED_DIR = BASE_DIR / "merged_dataset"
LOGS_DIR = BASE_DIR / "logs"
SKIPPED_DIR = BASE_DIR / "skipped"
VERIFICATION_DIR = BASE_DIR / "verification_samples"
REPORTS_DIR = BASE_DIR / "reports"

# Dataset Mappings (Alias -> Original Roboflow Folder)
DATASETS = {
    "cheating_dataset": DATASETS_DIR / "cheating dataset.v1i.yolov8",
    "cheating_actions": DATASETS_DIR / "Cheating.v1i.yolov8",
    "phone_dataset": DATASETS_DIR / "phone.v1i.yolov8",
    "exam_dataset": DATASETS_DIR / "exam cheating.v2-examdatasetv2.yolov8",
}

# Final Target Classes
TARGET_CLASSES = [
    "person",
    "phone",
    "chit",
    "hand",
    "peeking",
    "supplement-passing"
]

# Generate TARGET_CLASS_TO_ID mapping dynamically
TARGET_CLASS_TO_ID = {cls_name: idx for idx, cls_name in enumerate(TARGET_CLASSES)}

# Class Mappings (Original Class Name -> Target Class Name or 'REMOVE')
CLASS_MAPPINGS = {
    "cheating_dataset": {
        "chits": "chit",
        "hand": "hand",
        "peeking": "peeking",
        "phone": "phone",
        "supplement-passing": "supplement-passing"
    },
    "cheating_actions": {
        "calculator": "REMOVE",
        "paper": "chit",
        "person": "person",
        "phone": "phone",
        "student cheating": "REMOVE"
    },
    "phone_dataset": {
        "phone": "phone",
        "undefined": "REMOVE"
    },
    "exam_dataset": {
        "person": "person",
        "students_cheating": "REMOVE",
        "students_not_cheating": "REMOVE"
    }
}
