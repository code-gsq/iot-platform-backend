# mqtt_subscriber.py —— 后端 MQTT 订阅服务：监听设备上报的消息，落库 + 超温告警
# 为什么要单独一个脚本：真实物联网后端里，"收设备数据"和"提供查询接口"常常分开——
# 一个走 MQTT（收数据），一个走 HTTP（给人查）。
import json
from decimal import Decimal

import paho.mqtt.client as mqtt

from database import SessionLocal
from models import Device, Telemetry, Alarm

BROKER = "127.0.0.1"     # 本地 Docker 里的 Mosquitto（不再用公共 broker）
PORT = 1884             # 1883 被 ThingsBoard 容器占了，改用 1884
TOPIC = "gsq/iot/+/telemetry"      # + 是通配符，匹配任意设备 key


def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(TOPIC, qos=1)
    print(f"已连接 broker（rc={reason_code}），正在监听主题：{TOPIC}")


def on_message(client, userdata, msg):
    # 收到的 topic 形如 gsq/iot/dev_0001/telemetry，中间那截就是 device_key
    device_key = msg.topic.split("/")[2]
    try:
        data = json.loads(msg.payload.decode())
        temperature = Decimal(str(data["temperature"]))
        humidity = Decimal(str(data["humidity"]))
    except Exception as e:
        print(f"收到无法解析的消息，忽略：{e}")
        return

    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.device_key == device_key).first()
        if not device:
            print(f"[MQTT] 收到未知设备 {device_key} 的数据，忽略")
            return

        tele = Telemetry(device_id=device.id, temperature=temperature, humidity=humidity)
        db.add(tele)
        if temperature > 80:
            db.add(Alarm(device_id=device.id, type="high_temperature",
                         content=f"温度 {temperature}°C 超过 80°C"))
        db.commit()
        print(f"[MQTT] {device_key}: {temperature}°C / {humidity}% -> 已落库")
    finally:
        db.close()


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"⚠️ 与 broker 断开（rc={reason_code}），自动重连中...")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                     client_id="iot-backend-001",   # 固定 client_id + 持久会话：断线重连后 broker 会把断线期间的消息补发回来
                     clean_session=False)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect(BROKER, PORT, 60)
client.loop_forever()   # 一直监听，直到 Ctrl+C 停止
