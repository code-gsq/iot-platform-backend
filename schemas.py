# schemas.py —— 定义接口"收什么、发什么"的格式
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


# 注册设备时，前端传来的数据
class DeviceCreate(BaseModel):
    device_key: str
    name: str


# 返回给前端的设备数据
class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 允许直接从 ORM 对象读数据
    id: int
    device_key: str
    name: str
    status: str
    created_at: datetime


# 上报遥测数据时，传来的数据
class TelemetryCreate(BaseModel):
    temperature: Decimal
    humidity: Decimal


# 返回的遥测数据
class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int
    temperature: Decimal
    humidity: Decimal
    reported_at: datetime