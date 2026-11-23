# create_user.py —— 建一个登录账号（密码会哈希后存库，绝不存明文）
# 用法：.venv/Scripts/python.exe create_user.py
# 想改账号密码，改下面两个常量再跑一次即可
from database import SessionLocal
from models import SysUser
from auth import hash_password

USERNAME = "admin"
PASSWORD = "admin123"

db = SessionLocal()
try:
    exists = db.query(SysUser).filter(SysUser.username == USERNAME).first()
    if exists:
        print(f"用户 {USERNAME} 已存在，跳过（想换密码请先去数据库删掉这条再跑）")
    else:
        db.add(SysUser(username=USERNAME, password=hash_password(PASSWORD), role="admin"))
        db.commit()
        print(f"✅ 已创建用户：{USERNAME} / {PASSWORD}（role=admin，密码已哈希入库，不存明文）")
finally:
    db.close()
