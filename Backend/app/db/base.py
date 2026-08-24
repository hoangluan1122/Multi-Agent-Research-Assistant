"""
Module định nghĩa lớp cơ sở DeclarativeBase cho SQLAlchemy ORM.
Tất cả các Model cơ sở dữ liệu trong hệ thống sẽ kế thừa từ lớp Base này.
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Lớp cơ sở ORM chứa metadata và quản lý khai báo các bảng dữ liệu."""
    pass

