import argparse
import sys
from utils import setup_logger
from cleaner import run_cleaner
from merger import merge_datasets
from verifier import verify_dataset
from visualizer import visualize_samples
from statistics import generate_statistics

logger = setup_logger("main")

def main():
    parser = argparse.ArgumentParser(description="Exam Cheating Dataset Preparation Pipeline")
    parser.add_argument("--clean", action="store_true", help="Run the dataset cleaner stage")
    parser.add_argument("--merge", action="store_true", help="Run the dataset merger stage (deduplication & merging)")
    parser.add_argument("--verify", action="store_true", help="Run bounding box and integrity verification")
    parser.add_argument("--stats", action="store_true", help="Generate statistics.json and dataset_report.csv")
    parser.add_argument("--visualize", action="store_true", help="Generate random sample visualizations")
    parser.add_argument("--all", action="store_true", help="Run all stages sequentially")

    args = parser.parse_args()
    
    # If no flags are provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    clean_stats = None
    merge_stats = None

    if args.all or args.clean:
        logger.info("=== STAGE 1: CLEAN ===")
        clean_stats = run_cleaner()
        
    if args.all or args.merge:
        logger.info("=== STAGE 2: MERGE ===")
        merge_stats = merge_datasets()
        
    if args.all or args.verify:
        logger.info("=== STAGE 3: VERIFY ===")
        verify_dataset()
        
    if args.all or args.stats:
        logger.info("=== STAGE 4: STATISTICS ===")
        generate_statistics(clean_stats, merge_stats)
        
    if args.all or args.visualize:
        logger.info("=== STAGE 5: VISUALIZE ===")
        visualize_samples()

if __name__ == "__main__":
    main()
