import json
import paho.mqtt.client as mqtt
from app.core.config import get_settings

settings = get_settings()


class MQTTService:
    def __init__(self) -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if settings.mqtt_username:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(settings.mqtt_topic_detect, qos=1)
            print(f"[MQTT] Connected and subscribed: {settings.mqtt_topic_detect}")
        else:
            print(f"[MQTT] Connection failed, code={reason_code}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            payload = {"raw": msg.payload.decode(errors='ignore')}

        print(f"[MQTT] Message from {msg.topic}: {payload}")

    def start(self) -> None:
        self.client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
