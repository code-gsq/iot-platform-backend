# generate_big_device.py —— 再造一台"高频设备"，单独塞 20 万条数据
# 为什么：前面 1000 台设备每台才 200 条，排序的差距看不出来。
# 真实场景里，一台高频设备（比如每秒上报一次）一天就 86400 条。
# 我们用这一台 20 万条的设备，来演示"没复合索引 vs 有复合索引"的明显差距。
import random
from datetime import datetime, timedelta
from decimal import Decimal

from database import SessionLocal
from models import Device, Telemetry

TOTAL = 200000   # 塞 20 万条

db = SessionLocal()
try:
    big = Device(device_key="dev_high_freq", name="高频设备")
    db.add(big)
    db.flush()
    device_id = big.id
    print(f"高频设备 id = {device_id}")

    batch = []
    total = 0
    for i in range(TOTAL):
        batch.append(Telemetry(
            device_id=device_id,
            temperature=Decimal(f"{random.uniform(20, 100):.2f}"),
            humidity=Decimal(f"{random.uniform(30, 90):.2f}"),
            reported_at=datetime.now() - timedelta(seconds=i),  # 每秒上报一条，时间往前推
        ))
        if len(batch) >= 10000:   # 每攒 1 万条提交一次
            db.add_all(batch)
            db.commit()
            total += len(batch)
            batch = []
            print(f"  已插入 {total} 条...")
    if batch:
        db.add_all(batch)
        db.commit()
        total += len(batch)

    print(f"完成！高频设备 id={device_id}，共 {total} 条遥测")
finally:
    db.close()
