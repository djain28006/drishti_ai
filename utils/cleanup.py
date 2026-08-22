import os
import shutil
import time
from utils.logger import StageLogger

logger = StageLogger("CLEANUP")

def _remove_path(path: str):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
        # Fallback manual deletion for unlocked files
        if os.path.exists(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception:
                        pass
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except Exception:
                        pass
    else:
        try:
            os.remove(path)
        except Exception:
            pass

def clean_output_directory(output_dir: str = "outputs"):
    """
    Wipes all generated artifacts in outputs directory safely.
    Handles Windows file locking gracefully without throwing crashes.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Cleaning output directory: {output_dir}")
    
    subdirs = ["events", "clips", "debug", "zones", "reports", "capsules"]
    for sub in subdirs:
        _remove_path(os.path.join(output_dir, sub))

    files = [
        "heatmap.png", "heatmap_raw.png", "heatmap_student.png",
        "annotated_frame.png", "timeline.json", "events.db",
        "forensic.db", "incidents.json"
    ]
    for f in files:
        _remove_path(os.path.join(output_dir, f))

    fresh_subdirs = ["clips", "debug", "reports", "zones", "events", "capsules"]
    for sub in fresh_subdirs:
        os.makedirs(os.path.join(output_dir, sub), exist_ok=True)

    logger.info("Output directory cleanup completed.")

if __name__ == "__main__":
    clean_output_directory()
