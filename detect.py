import time
import cv2 as cv
from ultralytics import YOLO
import numpy as np
import paho.mqtt.client as mqtt

# YOLOv8 segmentasyon modeli yükleniyor
model = YOLO('yolov8n-seg.pt')
model.overrides['verbose'] = False  # Tüm logları devre dışı bırakır
cap = cv.VideoCapture('http://************:10101/?action=stream')

# MQTT Ayarları
MQTT_BROKER = "192.168.1.***"
MQTT_PORT = 1883
MQTT_TOPIC_SLOT1 = "slots/slot1/status"
MQTT_TOPIC_SLOT2 = "slots/slot2/status"

# Geri çağırma fonksiyonları
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Bağlantısı başarılı.")
    else:
        print(f"MQTT Bağlantı hatası: {rc}")

def on_publish(client, userdata, mid):
    print(f"MQTT Mesaj yayınlandı. MID: {mid}")

# MQTT İstemcisi Başlatma
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)  # Protokol versiyonunu belirtin
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

# Türkçe etiketler (Örnek)
turkish_labels = {
    "person": "insan",
    "car": "araba",
    "dog": "köpek",
    "cat": "kedi",
    "bicycle": "bisiklet",
    # Daha fazla sınıf ekleyin
}

# ROI Koordinatları
roi1_points = [(44, 153), (81, 143), (106, 182), (63, 197)]
roi2_points = [(172, 154), (199, 143), (243, 181), (218, 193)]

# ROI için sol alt köşe koordinatları
roi1_bottom_left = (roi1_points[3][0], roi1_points[3][1] + 10)
roi2_bottom_left = (roi2_points[3][0], roi2_points[3][1] + 10)

# Özel piksel kontrol koordinatları
specific_pixel_roi1 = (67, 146)
specific_pixel_roi2 = (187, 147)

try:
    while cap.isOpened():
        ret, image = cap.read()
        if not ret or image is None:
            print('Görüntü kaynağı yok, geç...')
            continue

        # Model tahmini (confidence %40 olarak ayarlanır)
        results = model(image, conf=0.4)
        if not results:
            print("nesne yok, atla...")
            continue

        # Görüntü kopyası al
        segments = image.copy()

        # Tespit edilen nesnelerin maskelerini ve etiketlerini çiz
        roi1_occupied = False  # ROI1'de nesne olup olmadığını kontrol etmek için bayrak
        roi2_occupied = False  # ROI2'de nesne olup olmadığını kontrol etmek için bayrak

        specific_pixel_occupied_roi1 = False  # ROI1 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak
        specific_pixel_occupied_roi2 = False  # ROI2 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak

        for r in results:
            if r.masks is not None:  # 'masks' özelliği None değilse işleme devam et
                try:
                    masks = r.masks.data.cpu().numpy()  # Segmentasyon maskelerini al
                    boxes = r.boxes.xyxy.cpu().numpy()  # Nesne kutularını al
                    classes = r.boxes.cls.cpu().numpy()  # Nesne sınıflarını al
                    confidences = r.boxes.conf.cpu().numpy()  # Confidence değerlerini al
                except AttributeError:
                    print("maske yada kutu yok, atla...")
                    continue

                for i, mask in enumerate(masks):
                    # Yalnızca confidence %40 üzerindeyse işleme devam et
                    if confidences[i] < 0.4:
                        continue

                    # Maskeyi görüntü boyutlarına yeniden boyutlandır
                    mask_resized = cv.resize(mask, (segments.shape[1], segments.shape[0]))
                    mask_resized = (mask_resized > 0.5).astype("uint8")  # Binary hale getir

                    # Maske sınırlarını çiz
                    contours, _ = cv.findContours(mask_resized, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
                    cv.drawContours(segments, contours, -1, (0, 255, 255), 2)  # Sarı renkli sınırlar

                    # Şeffaf maske ekle
                    colored_mask = np.zeros_like(segments, dtype=np.uint8)
                    colored_mask[mask_resized == 1] = [0, 255, 0]  # Yeşil renk
                    segments = cv.addWeighted(segments, 0.95, colored_mask, 0.05, 0)  # Şeffaflık

                    # Belirli bir pikselde nesne kontrolü (ROI 1)
                    if mask_resized[specific_pixel_roi1[1], specific_pixel_roi1[0]] == 1:
                        specific_pixel_occupied_roi1 = True

                    # Belirli bir pikselde nesne kontrolü (ROI 2)
                    if mask_resized[specific_pixel_roi2[1], specific_pixel_roi2[0]] == 1:
                        specific_pixel_occupied_roi2 = True
                        
                    # Etiket ve confidence değerini kutunun üstüne ekle
                    x1, y1, x2, y2 = map(int, boxes[i])  # Kutunun koordinatları
                    original_label = model.names[int(classes[i])]  # Orijinal sınıf adı
                    label = turkish_labels.get(original_label, original_label)  # Türkçe karşılığını al
                    confidence_text = f"{label} ({confidences[i]:.2f})"  # Etiket ve confidence
                    cv.putText(segments, confidence_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # ROI1 çiz (çokgen)
        cv.polylines(
            segments, [np.array(roi1_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
        )
        # ROI2 çiz (çokgen)
        cv.polylines(
            segments, [np.array(roi2_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
        )

        # ROI1'in durumunu kontrol et ve yazı yaz
        if specific_pixel_occupied_roi1:
            cv.putText(segments, "DOLU", roi1_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            result = mqtt_client.publish(MQTT_TOPIC_SLOT1, "Slot 1 dolu")
            if result.rc == 0:
                print("MQTT Mesaj yayınlandı: Slot 1 dolu")

        else:
            cv.putText(segments, "BOS", roi1_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
            result = mqtt_client.publish(MQTT_TOPIC_SLOT1, "Slot 1 boş")
            if result.rc == 0:
                print("MQTT Mesaj yayınlandı: Slot 1 boş")

        # ROI2'nin durumunu kontrol et ve yazı yaz
        if specific_pixel_occupied_roi2:
            cv.putText(segments, "DOLU", roi2_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            result = mqtt_client.publish(MQTT_TOPIC_SLOT2, "Slot 2 dolu")
            if result.rc == 0:
                print("MQTT Mesaj yayınlandı: Slot 2 dolu")
        else:
            cv.putText(segments, "BOS", roi2_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
            result = mqtt_client.publish(MQTT_TOPIC_SLOT2, "Slot 2 boş")
            if result.rc == 0:
                print("MQTT Mesaj yayınlandı: Slot 2 boş")

        # Görüntüyü ekranda göster
        cv.imshow('Image Segmentation', segments)

        # Çıkış için 'q' tuşuna basılması gerekiyor
        key = cv.waitKey(1)
        if key & 0xFF == ord('q'):
            print('Çıkış işlemi başlatıldı.')
            break

finally:
    cap.release()
    cv.destroyAllWindows()
