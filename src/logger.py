import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Tránh việc add handler nhiều lần nếu logger đã tồn tại
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Định dạng dòng log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # In log ra standard output (CloudWatch sẽ tự bắt được)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger