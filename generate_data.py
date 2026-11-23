# generate_data.py —— 造数据：批量造设备 + 海量遥测，把表"撑大"
# 为什么需要它：现在表里只有 31 条遥测，查起来怎么都快，看不出"优化"的效果。
# 真实平台里设备一天就上报几万条，所以要先造出几十万条数据，后面才能演示"加索引提速"。
import random
from datetime import datetime, timedelta
from decimal import Decimal

from database import SessionLocal
from models import Device, Telemetry

DEVICE_COUNT = 1000      # 造 1000 台设备
TELE_PER_DEVICE = 200    # 每台设备 200 条遥测 → 一共 20 万条

db = SessionLocal()
try:
    # ① 批量造设备
    devices = [
        Device(device_key=f"dev_{i:04d}", name=f"设备{i}")
        for i in range(1, DEVICE_COUNT + 1)
    ]
    db.add_all(devices)
    db.flush()   # 让数据库给每台设备分配 id（还不真正提交），这样下面马上能用 device.id
    print(f"① 已生成 {DEVICE_COUNT} 台设备")

    # ② 批量造遥测：每台设备 200 条，时间从"现在"往前推
    batch = []
    total = 0
    for device in devices:
        for j in range(TELE_PER_DEVICE):
            batch.append(Telemetry(
                device_id=device.id,
                temperature=Decimal(f"{random.uniform(20, 100):.2f}"),
                humidity=Decimal(f"{random.uniform(30, 90):.2f}"),
                reported_at=datetime.now() - timedelta(minutes=j),
            ))
        if len(batch) >= 5000:   # 攒够 5000 条就写一次，避免 20 万条全堆内存里卡死
            db.add_all(batch)
            db.commit()
            total += len(batch)
            batch = []
            print(f"  已插入 {total} 条遥测...")
    if batch:
        db.add_all(batch)
        db.commit()
        total += len(batch)

    print(f"② 完成！共 {DEVICE_COUNT} 台设备、{total} 条遥测")
finally:
    db.close()
