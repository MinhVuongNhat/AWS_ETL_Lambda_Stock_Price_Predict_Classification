import logging
import os
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Tránh việc add handler nhiều lần nếu logger đã tồn tại
    if not logger.handlers:
        log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        logger.setLevel(log_level)
        
        # Định dạng dòng log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # In log ra standard output (CloudWatch sẽ tự bắt được)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger