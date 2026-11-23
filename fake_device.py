# fake_device.py —— 假设备：自动模拟设备，往平台上报温湿度数据
import random
import time
import requests

BASE_URL = "http://127.0.0.1:8000"
DEVICE_ID = 1            # 发给哪台设备（你已注册的 id=1）
REPORT_COUNT = 30        # 总共上报 30 次

high_temp_count = 0      # 记录有几次温度 > 80（这些会触发告警）

for i in range(REPORT_COUNT):
    temperature = round(random.uniform(20, 100), 2)   # 随机温度 20~100
    humidity = round(random.uniform(30, 90), 2)       # 随机湿度 30~90

    if temperature > 80:
        high_temp_count += 1

    resp = requests.post(
        f"{BASE_URL}/devices/{DEVICE_ID}/telemetry",
        json={"temperature": temperature, "humidity": humidity},
    )
    print(f"第{i+1:2d}次上报: 温度 {temperature:5.2f}°C, 湿度 {humidity:5.2f}% -> {resp.status_code}")
    time.sleep(0.5)   # 每 0.5 秒上报一次

print(f"\n完成！共上报 {REPORT_COUNT} 次，其中温度>80 的有 {high_temp_count} 次（会触发告警）")
