# benchmark.py —— 测速脚本：查"某台设备的历史数据"，看 MySQL 怎么执行、到底多慢
# 用法：优化前跑一次，加索引后再跑一次，对比"平均耗时"这个数字。
from time import perf_counter

from sqlalchemy import func, text

from database import SessionLocal
from models import Telemetry

db = SessionLocal()

# 找一台"遥测数据最多"的设备来测（新造的 1000 台设备，每台 200 条）
target = (
    db.query(Telemetry.device_id, func.count(Telemetry.id).label("cnt"))
    .group_by(Telemetry.device_id)
    .order_by(func.count(Telemetry.id).desc())
    .first()
)
device_id = target.device_id
print(f"待测设备 id = {device_id}（它有 {target.cnt} 条遥测）\n")

# ① EXPLAIN：问 MySQL"这条查询你怎么执行的"
print("① EXPLAIN（看是'全表扫描'还是'走索引'）")
print("-" * 60)
rows = db.execute(
    text(f"EXPLAIN SELECT * FROM telemetry WHERE device_id = {device_id}")
).all()
for r in rows:
    m = r._mapping
    print(f"  type(扫描方式)      = {m['type']}   <- ALL=全表扫描(慢), ref=走索引(快)")
    print(f"  possible_keys(可用) = {m['possible_keys']}")
    print(f"  key(实际用的索引)   = {m['key']}")
    print(f"  rows(预计扫几行)    = {m['rows']}")

# ② 反复查 10 次，取平均耗时
print("\n② 反复查 10 次，看平均耗时")
print("-" * 60)
times = []
for i in range(10):
    start = perf_counter()
    result = db.query(Telemetry).filter(Telemetry.device_id == device_id).all()
    end = perf_counter()
    ms = (end - start) * 1000
    times.append(ms)
    print(f"  第{i+1:2d}次: {ms:7.2f} 毫秒，查到 {len(result)} 条")
avg = sum(times) / len(times)
print(f"\n>>> 平均耗时：{avg:.2f} 毫秒")

db.close()
