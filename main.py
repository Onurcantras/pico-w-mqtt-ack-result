import time
import ujson
import network
from machine import Pin
import storage
from mqtt_client import ResilientMQTTClient

# Donanım ve Konfigürasyon
config = storage.load_config()
WIFI_SSID = config.get("wifi_ssid")
WIFI_PASS = config.get("wifi_pass")
BROKER = config.get("mqtt_broker", "broker.hivemq.com")
STUDENT_ID = config.get("student_id", "onurcan")
DEVICE_ID = config.get("device_id", "pico-w-pump-01")

PUMP_RELAY_PIN = 21
pump_relay = Pin(PUMP_RELAY_PIN, Pin.OUT, value=0)

# Topic Ağacı
TOPIC_BASE = f"internship/{STUDENT_ID}/{DEVICE_ID}"
TOPIC_COMMAND = f"{TOPIC_BASE}/command"
TOPIC_ACK = f"{TOPIC_BASE}/command-ack"
TOPIC_RESULT = f"{TOPIC_BASE}/command-result"

# Son İşlenen İstek Kimlikleri (Duplicate Komut Engelleme)
processed_requests = []
MAX_HISTORY = 10

def send_ack(mqtt_client, req_id, status, reason=""):
    """Komutun alındığını ve işleme konduğunu/reddedildiğini bildiren ACK mesajı."""
    ack_payload = {
        "clientRequestId": req_id,
        "status": status,  # "accepted" veya "rejected"
        "reason": reason,
        "timestamp": time.time()
    }
    mqtt_client.publish(TOPIC_ACK, ujson.dumps(ack_payload))
    print(f"[ACK] Status: {status} | RequestId: {req_id}")

def send_result(mqtt_client, req_id, command, result, error_details=None):
    """İşlemin fiziksel olarak başarıyla tamamlandığını veya başarısız olduğunu bildiren RESULT mesajı."""
    result_payload = {
        "clientRequestId": req_id,
        "command": command,
        "result": result,  # "success" veya "failure"
        "errorDetails": error_details,
        "timestamp": time.time()
    }
    mqtt_client.publish(TOPIC_RESULT, ujson.dumps(result_payload))
    print(f"[RESULT] Command: {command} | Result: {result}")

def handle_incoming_command(topic, message, mqtt_client):
    global processed_requests
    
    try:
        data = ujson.loads(message)
        req_id = data.get("clientRequestId")
        command = data.get("command")

        # 1. İstek Kimliği (clientRequestId) Kontrolü
        if not req_id:
            send_ack(mqtt_client, "unknown", "rejected", "Zorunlu 'clientRequestId' parametresi eksik.")
            return

        # 2. Mükerrer (Duplicate) Komut Kontrolü
        if req_id in processed_requests:
            send_ack(mqtt_client, req_id, "rejected", "Bu komut daha önce işlendi (Duplicate).")
            return

        # 3. Komut Tipi Kontrolü ve İşleme
        if command == "StartPump":
            duration = data.get("durationSec", 0)
            if duration <= 0 or duration > 300:
                send_ack(mqtt_client, req_id, "rejected", "Geçersiz çalışma süresi.")
                send_result(mqtt_client, req_id, command, "failure", "Süre sınırı ihlal edildi.")
                return

            # Komut Kabul Edildi (ACK)
            send_ack(mqtt_client, req_id, "accepted", "StartPump komutu kuyruğa alındı.")
            
            # Donanım İşlemi Uygula
            pump_relay.value(1)
            processed_requests.append(req_id)
            if len(processed_requests) > MAX_HISTORY:
                processed_requests.pop(0)

            # İşlem Tamamlandı (RESULT)
            send_result(mqtt_client, req_id, command, "success")

        elif command == "StopPump":
            send_ack(mqtt_client, req_id, "accepted", "StopPump komutu alındı.")
            pump_relay.value(0)
            
            processed_requests.append(req_id)
            if len(processed_requests) > MAX_HISTORY:
                processed_requests.pop(0)

            send_result(mqtt_client, req_id, command, "success")

        else:
            send_ack(mqtt_client, req_id, "rejected", f"Bilinmeyen komut: '{command}'")

    except Exception as e:
        print(f"[HATA] Mesaj işleme hatası: {e}")

print("=== PICO W COMMAND ACK & RESULT ARCHITECTURE ===")