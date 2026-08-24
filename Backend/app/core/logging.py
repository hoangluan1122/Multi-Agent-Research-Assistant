"""
Module cấu hình ghi log (logging) cho toàn bộ hệ thống PaperFlow.
Thiết lập định dạng log chuẩn và mức log cho các thư viện phụ thuộc.
"""

import logging
import sys

def setup_logging():
    """
    Khởi tạo cấu hình logging hệ thống:
    - Định dạng timestamp, level, tên module và nội dung log.
    - Xuất log ra console (stdout).
    - Giảm bớt log chi tiết từ các thư viện mạng bên ngoài như httpx, httpcore, urllib3.
    """
    log_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Ẩn bớt các log quá chi tiết từ thư viện bên ngoài
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Logger chính cho ứng dụng paperflow
logger = logging.getLogger("paperflow")

