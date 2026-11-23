# mqtt_device.py —— 设备端模拟器：像真实设备一样，通过 MQTT 往 broker 上报温湿度
import json
import random
import time

import paho.mqtt.client as mqtt

BROKER = "127.0.0.1"     # 本地 Docker 里的 Mosquitto（不再用公共 broker）
PORT = 1884             # 1883 被 ThingsBoard 容器占了，改用 1884
DEVICE_KEY = "dev_0001"     # 要上报的设备（必须是库里已注册的 device_key）
COUNT = 20                  # 上报 20 次

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)
client.loop_start()   # 启动后台线程，负责真正把消息发出去（不加这行，消息可能发不出去）

for i in range(COUNT):
    temperature = round(random.uniform(20, 100), 2)
    humidity = round(random.uniform(30, 90), 2)
    topic = f"gsq/iot/{DEVICE_KEY}/telemetry"
    payload = json.dumps({"temperature": temperature, "humidity": humidity})
    info = client.publish(topic, payload, qos=1)   # qos=1 保证至少送达一次
    info.wait_for_publish(timeout=5)                # 等这条消息真正发到 broker 再发下一条
    print(f"第{i+1:2d}次发布: {DEVICE_KEY} 温度 {temperature:5.2f}°C / 湿度 {humidity:5.2f}%")
    time.sleep(1)

client.loop_stop()
client.disconnect()
print(f"\n完成！共通过 MQTT 发布了 {COUNT} 条")
