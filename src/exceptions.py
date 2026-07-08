class ETLBaseException(Exception):
    """Lớp Exception cơ sở cho toàn bộ dự án ETL."""
    pass

class DataValidationError(ETLBaseException):
    """Lỗi khi dữ liệu không vượt qua Schema hoặc Business Rules."""
    pass

class DataCleaningError(ETLBaseException):
    """Lỗi trong quá trình làm sạch dữ liệu."""
    pass