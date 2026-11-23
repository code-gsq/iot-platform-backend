# IoT 设备管理平台后端

一个用 **FastAPI + MySQL** 实现的物联网设备管理后端，支持设备注册、遥测上报、自动告警与历史数据查询，并完成了一次真实的**慢查询定位与索引优化**：查询耗时 **248ms → 1.75ms，提升约 142 倍**。

## 技术栈

Python 3.11 · FastAPI · Uvicorn · SQLAlchemy 2.0 · PyMySQL · MySQL · Pydantic v2

## 功能特性

- **设备注册** `POST /devices`：重复 `device_key` 返回 `409`，不落库并给出友好提示
- **遥测上报** `POST /devices/{id}/telemetry`：写入温湿度，温度 > 80°C 自动生成告警
- **历史查询** `GET /devices/{id}/telemetry`：按时间倒序 + `limit` 分页（默认 100 条）
- **设备列表** `GET /devices`

## 核心亮点：慢查询定位与优化

不是"照着教程写完"，而是真实跑了一轮压测与优化闭环：

1. **造数据**：批量构造 1000 台设备、约 40 万条遥测（含一台 20 万条的高频设备），模拟真实上报场景；
2. **定位瓶颈**：用 `EXPLAIN` 分析，发现 `ORDER BY reported_at` 触发了 `Using filesort`（手工排序），查询耗时 **248ms**；
3. **加复合索引**：`ALTER TABLE telemetry ADD INDEX idx_device_time (device_id, reported_at);`
4. **对比验证**：同一句查询优化到 **1.75ms**，`Extra` 从 `Using filesort` 变为 `Backward index scan`。

| 指标 | 优化前 | 优化后 |
|---|---|---|
| 执行计划 Extra | `Using filesort` | `Backward index scan` |
| 平均耗时 | 248.44 ms | 1.75 ms |
| 提速 | — | **约 142 倍** |

## 项目结构

```
iot_platform_backend/
├── main.py                  # FastAPI 入口 + 4 个接口
├── models.py                # SQLAlchemy ORM 模型（device/telemetry/alarm/sys_user）
├── schemas.py               # Pydantic 请求/响应模型
├── database.py              # 数据库连接（从 .env 读配置，不硬编码密码）
├── fake_device.py           # 假设备：模拟单台设备定时上报
├── generate_data.py         # 造数：批量构造设备与遥测
├── generate_big_device.py   # 造数：高频设备 20 万条
├── benchmark.py             # 测速：普通查询
├── benchmark2.py            # 测速：排序查询（优化前后对比）
└── .env.example             # 环境变量模板
```

## 快速开始

**1. 建库建表**：在 MySQL 中创建 `iot_platform` 库及 `device` / `telemetry` / `alarm` / `sys_user` 四张表。

**2. 安装依赖**

```bash
python -m pip install fastapi uvicorn sqlalchemy pymysql python-dotenv
```

**3. 配置数据库**

复制 `.env.example` 为 `.env`，填入你自己的密码：

```bash
cp .env.example .env
```

编辑 `.env`：`DATABASE_URL=mysql+pymysql://root:你的密码@localhost:3306/iot_platform`

**4. 启动**

```bash
uvicorn main:app --reload
```

浏览器打开 `http://127.0.0.1:8000/docs` 查看 Swagger 接口文档。

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/devices` | 注册设备（重复返回 409） |
| POST | `/devices/{device_id}/telemetry` | 上报温湿度（>80°C 自动告警） |
| GET | `/devices/{device_id}/telemetry` | 查历史（倒序 + limit，默认 100） |
| GET | `/devices` | 设备列表 |
