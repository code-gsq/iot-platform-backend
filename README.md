# IoT 设备管理平台后端

一个用 **FastAPI + MySQL** 实现的物联网设备管理后端，支持设备注册、遥测上报（**HTTP + MQTT 双通道**）、超温自动告警、历史查询、**JWT 登录认证**，并完成了一次真实的**慢查询定位与索引优化**：查询耗时 **248ms → 1.75ms，提升约 142 倍**。

## 技术栈

Python 3.11 · FastAPI · Uvicorn · SQLAlchemy 2.0 · PyMySQL · MySQL · Pydantic v2 · paho-mqtt · PyJWT · Docker（Mosquitto）

## 功能特性

- **设备注册** `POST /devices`：重复 `device_key` 返回 `409`，并给出友好提示
- **HTTP 遥测上报** `POST /devices/{id}/telemetry`：写入温湿度，温度 > 80°C 自动生成告警
- **MQTT 设备接入**：设备通过 MQTT 协议上报，订阅服务自动落库 + 超温告警（QoS 1 + 持久会话，消息不丢）
- **历史查询** `GET /devices/{id}/telemetry`：按时间倒序 + `limit` 分页
- **设备列表** `GET /devices`
- **JWT 登录认证** `POST /auth/login`：登录签发 token，其余接口均需携带 token

## 核心亮点

### 1. 慢查询定位与索引优化（248ms → 1.75ms）

不是"照着教程写完"，而是真实跑了一轮压测与优化闭环：

1. **造数据**：批量构造 1000 台设备、约 40 万条遥测（含一台 20 万条的高频设备）；
2. **定位瓶颈**：用 `EXPLAIN` 分析，发现 `ORDER BY reported_at` 触发 `Using filesort`（手工排序），耗时 **248ms**；
3. **加复合索引**：`ALTER TABLE telemetry ADD INDEX idx_device_time (device_id, reported_at);`
4. **对比验证**：同一句查询优化到 **1.75ms**，`Extra` 从 `Using filesort` 变为 `Backward index scan`。

| 指标 | 优化前 | 优化后 |
|---|---|---|
| 执行计划 Extra | `Using filesort` | `Backward index scan` |
| 平均耗时 | 248.44 ms | 1.75 ms |
| 提速 | — | **约 142 倍** |

### 2. MQTT 设备接入（自建 broker，消息不丢）

```
设备(mqtt_device.py) --发布--> Mosquitto(Docker 本地 broker) --订阅--> 订阅服务(mqtt_subscriber.py) --落库--> MySQL
                                                                             └─ 温度>80°C 自动写告警
```

- **自建 broker**：用 Docker 起本地 Eclipse Mosquitto，不依赖公共免费 broker（后者不稳、会断线丢消息）；
- **QoS 1**：消息"至少送达一次"，保证不丢；
- **持久会话**：固定 client_id + `clean_session=False`，断线重连后 broker 会把断线期间的消息补发回来。

### 3. JWT 登录认证

- **密码哈希**：PBKDF2 + 随机盐，数据库只存 `盐$哈希`，不存明文；
- **签发/校验**：登录成功后签发 JWT（HS256，有效期 1 小时），签名密钥放 `.env`；
- **接口鉴权**：除登录外所有接口都挂 `Depends(get_current_user)`，无 token 返回 401。

## 项目结构

```
iot_platform_backend/
├── main.py                  # FastAPI 入口 + 5 个接口
├── models.py                # SQLAlchemy ORM 模型（device/telemetry/alarm/sys_user）
├── schemas.py               # Pydantic 请求/响应模型
├── database.py              # 数据库连接（从 .env 读配置，不硬编码密码）
├── auth.py                  # JWT 认证：密码哈希 + 签发/校验 token
├── mqtt_subscriber.py       # MQTT 订阅服务：收数据落库 + 超温告警
├── mqtt_device.py           # 模拟设备：通过 MQTT 定时上报温湿度
├── create_user.py           # 建登录账号（密码哈希后入库）
├── test_auth_flow.py        # 验证登录 + 鉴权流程
├── mosquitto.conf           # 本地 MQTT broker 配置（Docker 用）
├── fake_device.py           # 假设备：HTTP 定时上报
├── generate_data.py         # 造数：批量构造设备与遥测
├── generate_big_device.py   # 造数：高频设备 20 万条
├── benchmark.py / benchmark2.py  # 测速脚本
└── .env.example             # 环境变量模板
```

## 快速开始

**1. 建库建表**：在 MySQL 中创建 `iot_platform` 库及 `device` / `telemetry` / `alarm` / `sys_user` 四张表。

**2. 安装依赖**

```bash
python -m pip install fastapi uvicorn sqlalchemy pymysql python-dotenv paho-mqtt pyjwt
```

**3. 配置环境变量**

复制 `.env.example` 为 `.env`，填入数据库密码和 JWT 密钥：

```bash
cp .env.example .env
```

`.env` 内容：`DATABASE_URL=...`、`JWT_SECRET=一串随机字符串`（可用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成）。

**4. 启动本地 MQTT broker（Docker）**

```bash
docker run -d --name mosquitto-iot --restart unless-stopped -p 1884:1884 -v <项目绝对路径>/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto
```

> 端口用 1884 是因为本机 1883 已被 ThingsBoard 容器占用；`-v` 在 Windows 下要写绝对路径。

**5. 建一个登录账号**

```bash
python create_user.py   # 默认创建 admin / admin123
```

**6. 启动后端 + MQTT 订阅服务**

```bash
uvicorn main:app --reload          # 终端 1：HTTP 服务
python mqtt_subscriber.py          # 终端 2：MQTT 订阅服务
```

浏览器打开 `http://127.0.0.1:8000/docs` 查看 Swagger 接口文档。

## API 一览

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/auth/login` | 登录，返回 token | 不需要 |
| POST | `/devices` | 注册设备（重复返回 409） | 需要 token |
| POST | `/devices/{device_id}/telemetry` | 上报温湿度（>80°C 自动告警） | 需要 token |
| GET | `/devices/{device_id}/telemetry` | 查历史（倒序 + limit） | 需要 token |
| GET | `/devices` | 设备列表 | 需要 token |

## MQTT 使用说明

1. 先按上面步骤启动 broker（第 4 步）和订阅服务（第 6 步）；
2. 另开一个终端跑设备端，模拟设备通过 MQTT 上报 20 条数据：

```bash
python mqtt_device.py
```

3. 订阅服务会实时打印 `[MQTT] dev_0001: xx°C / xx% -> 已落库`，超温（>80°C）自动写告警；去数据库 `SELECT * FROM telemetry ORDER BY id DESC LIMIT 20;` 就能看到刚上报的数据。

## JWT 登录说明

1. 登录拿 token（Swagger 里点 `POST /auth/login`，或）：

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

2. 拿到 `access_token` 后，请求其他接口时带上请求头 `Authorization: Bearer <token>`（Swagger 里点右上角 **Authorize** 按钮粘贴 token）。

3. 快速验证整条链路：`python test_auth_flow.py`
