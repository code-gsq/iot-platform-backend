from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Device, Telemetry, Alarm
from schemas import DeviceCreate, DeviceOut, TelemetryCreate, TelemetryOut

app = FastAPI(title="IoT 设备管理平台")

# 依赖：每次请求，开一个数据库会话，用完自动关掉
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ① 注册设备（改后：先查重，重复给友好提示）
@app.post("/devices", response_model=DeviceOut)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    # 查重：这个 device_key 是否已经被注册过
    exists = db.query(Device).filter(Device.device_key == device.device_key).first()
    if exists:
        raise HTTPException(status_code=409, detail="这个 device_key 已被注册")

    db_device = Device(device_key=device.device_key, name=device.name)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

# ② 设备上报温湿度（温度 > 80 自动记告警）
@app.post("/devices/{device_id}/telemetry", response_model=TelemetryOut)
def report_telemetry(device_id: int, data: TelemetryCreate, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    tele = Telemetry(device_id=device_id, temperature=data.temperature, humidity=data.humidity)
    db.add(tele)

    if data.temperature > 80:
        alarm = Alarm(
            device_id=device_id,
            type="high_temperature",
            content=f"温度 {data.temperature}°C 超过 80°C",
        )
        db.add(alarm)

    db.commit()
    db.refresh(tele)
    return tele

# ③ 查某设备的历史数据（按时间倒序，只取最近 limit 条，默认 100）
@app.get("/devices/{device_id}/telemetry", response_model=list[TelemetryOut])
def list_telemetry(device_id: int, limit: int = 100, db: Session = Depends(get_db)):
    # 不写 limit 的话，设备数据多了会把几十万条全吐出来，慢且浪费
    return (
        db.query(Telemetry)
        .filter(Telemetry.device_id == device_id)
        .order_by(Telemetry.reported_at.desc())
        .limit(limit)
        .all()
    )

# ④ 设备列表
@app.get("/devices", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()
