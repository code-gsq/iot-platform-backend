# test_auth_flow.py —— 手动验证登录 + 鉴权流程（跑一遍看结果）
# 用法：.venv/Scripts/python.exe test_auth_flow.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ① 不带 token 访问受保护接口 → 期望 401
r = client.get("/devices")
print(f"① 无 token 访问 /devices → {r.status_code}（期望 401）")

# ② 错误密码登录 → 期望 401
r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
print(f"② 错误密码登录 → {r.status_code}（期望 401）")

# ③ 正确登录 → 期望 200，拿到 token
r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
print(f"③ 正确登录 → {r.status_code}（期望 200）")
token = r.json()["access_token"]
print(f"   拿到 token（前 40 字符）：{token[:40]}...")

# ④ 带 token 访问受保护接口 → 期望 200
r = client.get("/devices", headers={"Authorization": f"Bearer {token}"})
print(f"④ 带 token 访问 /devices → {r.status_code}（期望 200），返回 {len(r.json())} 台设备")
