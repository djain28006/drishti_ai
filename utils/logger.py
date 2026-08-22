import logging
import sys

def get_stage_logger(stage_name: str) -> logging.Logger:
    """
    Creates and returns a logger configured for a specific stage.
    Output format: [STAGE X] <message>
    """
    logger = logging.getLogger(stage_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        class FlushingStreamHandler(logging.StreamHandler):
            def emit(self, record):
                super().emit(record)
                self.flush()

        handler = FlushingStreamHandler(sys.stdout)
        formatter = logging.Formatter(f'[{stage_name}] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False
        
    return logger

class StageLogger:
    """
    Helper wrapper around the standard logger to specifically format
    the required completion and error messages per stage.
    """
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.logger = get_stage_logger(stage_name)
        
    def info(self, msg: str):
        self.logger.info(msg)
        
    def warning(self, msg: str):
        self.logger.warning(f"[WARNING] {msg}")

    def debug(self, msg: str):
        self.logger.debug(msg)
        
    def error(self, msg: str):
        self.logger.error(f"[ERROR] {msg}")
