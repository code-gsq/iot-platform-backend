# models.py —— 把数据库里的 4 张表，翻译成 4 个 Python 类
# 以后你在 Python 里操作数据，是直接操作这些类（比如 Device(name="传感器1")），SQLAlchemy 这个"翻译官"再帮你自动翻成 SQL 存进数据库。要让翻译官会翻，得先告诉它"每张表长什么样"——这就是
#models.py 干的活。
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


# ① 设备类，对应 device 表
class Device(Base):
    __tablename__ = "device"  # 对应数据库里哪张表

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_key: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="offline")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ② 遥测数据类，对应 telemetry 表
class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("device.id"))
    temperature: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))
    humidity: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ③ 告警类，对应 alarm 表
class Alarm(Base):
    __tablename__ = "alarm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("device.id"))
    type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ④ 用户类，对应 sys_user 表
class SysUser(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)