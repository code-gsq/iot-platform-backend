# benchmark2.py —— 测"排序查询"的速度：WHERE device_id=X ORDER BY reported_at DESC LIMIT 100
# 用法：加复合索引前跑一次、加完再跑一次，对比"平均耗时"和 EXPLAIN 的 Extra 字段。
from time import perf_counter

from sqlalchemy import func, text

from database import SessionLocal
from models import Telemetry

db = SessionLocal()

# 找"遥测最多"的设备（就是刚造的高频设备，20 万条）
target = (
    db.query(Telemetry.device_id, func.count(Telemetry.id).label("cnt"))
    .group_by(Telemetry.device_id)
    .order_by(func.count(Telemetry.id).desc())
    .first()
)
device_id = target.device_id
print(f"待测设备 id = {device_id}（它有 {target.cnt} 条遥测）\n")

SQL = f"SELECT * FROM telemetry WHERE device_id = {device_id} ORDER BY reported_at DESC LIMIT 100"

# ① EXPLAIN：重点看 Extra 有没有 "Using filesort"
print("① EXPLAIN（重点看 Extra 有没有 'Using filesort'）")
print("-" * 60)
rows = db.execute(text(f"EXPLAIN {SQL}")).all()
for r in rows:
    m = r._mapping
    print(f"  type            = {m['type']}")
    print(f"  key(用的索引)   = {m['key']}")
    print(f"  rows(预计扫几行)= {m['rows']}")
    print(f"  Extra           = {m['Extra']}   <- 出现 'Using filesort' = 要手工排序(慢)")

# ② 反复查 10 次，看平均耗时
print("\n② 反复查 10 次，看平均耗时")
print("-" * 60)
times = []
for i in range(10):
    start = perf_counter()
    result = (
        db.query(Telemetry)
        .filter(Telemetry.device_id == device_id)
        .order_by(Telemetry.reported_at.desc())
        .limit(100)
        .all()
    )
    end = perf_counter()
    ms = (end - start) * 1000
    times.append(ms)
    print(f"  第{i+1:2d}次: {ms:7.2f} 毫秒，查到 {len(result)} 条")
avg = sum(times) / len(times)
print(f"\n>>> 平均耗时：{avg:.2f} 毫秒")

db.close()
