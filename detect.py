import time
import cv2 as cv
from ultralytics import YOLO
import numpy as np
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont

# Türkçe karakter desteği için font dosyasını yükleyin
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Türkçe destekleyen bir .ttf dosyası, örn: "arial.ttf"
font = ImageFont.truetype(font_path, 10)

# YOLOv8 segmentasyon modeli yükleniyor
model = YOLO('yolov8n-seg.pt')
model.overrides['verbose'] = False  # Tüm logları devre dışı bırakır
cap = cv.VideoCapture('http://xxxxxxxxxxxxxxx0101/?action=stream')#'http://xxxxxxxxxxxxxxxxx101/?action=stream'

# MQTT Ayarları
MQTT_BROKER = "192.168.xxx.xxx"
MQTT_PORT = 1883
MQTT_TOPIC_SLOT1 = "slots/slot1/status"
MQTT_TOPIC_SLOT2 = "slots/slot2/status"
MQTT_TOPIC_SLOT3 = "slots/slot3/status"
MQTT_TOPIC_SLOT4 = "slots/slot4/status"
MQTT_TOPIC_SLOT5 = "slots/slot5/status"
MQTT_TOPIC_SLOT6 = "slots/slot6/status"





# Geri çağırma fonksiyonları
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Bağlantısı başarılı.")
    else:
        print(f"MQTT Bağlantı hatası: {rc}")

def on_publish(client, userdata, mid):
    pass

# MQTT İstemcisi Başlatma
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)  # Protokol versiyonunu belirtin
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

# LWT Mesajı Ayarla
mqtt_client.will_set("parking/status/occupied", "unknown", qos=1, retain=True)
mqtt_client.will_set("parking/status/empty", "unknown", qos=1, retain=True)
mqtt_client.will_set("parking/status/empty_slots", "unknown", qos=1, retain=True)

# Türkçe etiketler (Örnek)
turkish_labels = {
    "person": "insan",
    "car": "araba",
    "dog": "köpek",
    "cat": "kedi",
    "bicycle": "bisiklet",
    # Daha fazla sınıf ekleyin
}
# ROI saatleri
roi1_status_time = None
roi1_status_hour = None
roi2_status_time = None
roi2_status_hour = None
roi3_status_time = None
roi3_status_hour = None
roi4_status_time = None
roi4_status_hour = None
roi5_status_time = None
roi5_status_hour = None
roi6_status_time = None
roi6_status_hour = None
# ROI Koordinatları
roi1_points = [(13, 123), (48, 120), (65, 155), (20, 171)] #sol üst--->sağ üst--->sağ alt--->sol alt
roi2_points = [(52, 130), (89, 120), (113, 155), (72, 170)] #sol üst--->sağ üst--->sağ alt--->sol alt
roi3_points = [(95, 130), (126, 120), (159, 155), (123, 168)] #sol üst--->sağ üst--->sağ alt--->sol alt 
roi4_points = [(136, 130), (165, 120), (205, 155), (170, 168)] #sol üst--->sağ üst--->sağ alt--->sol alt
roi5_points = [(174, 130), (207, 120), (252, 156), (221, 170)] #sol üst--->sağ üst--->sağ alt--->sol alt
roi6_points = [(215, 130), (243, 120), (291, 152), (268, 168)] #sol üst--->sağ üst--->sağ alt--->sol alt


# ROI için sol alt köşe koordinatları
roi1_bottom_left = (roi1_points[3][0], roi1_points[3][1] + 10)
roi2_bottom_left = (roi2_points[3][0], roi2_points[3][1] + 10)
roi3_bottom_left = (roi3_points[3][0], roi3_points[3][1] + 10)
roi4_bottom_left = (roi4_points[3][0], roi4_points[3][1] + 10)
roi5_bottom_left = (roi5_points[3][0], roi5_points[3][1] + 10)
roi6_bottom_left = (roi6_points[3][0], roi6_points[3][1] + 10)

# Özel piksel kontrol koordinatları
specific_pixel_roi1 = (34, 128)
specific_pixel_roi2 = (75, 126)
specific_pixel_roi3 = (121, 133)
specific_pixel_roi4 = (165, 133)
specific_pixel_roi5 = (209, 132)
specific_pixel_roi6 = (257, 132)

# ROI'nin önceki durumlarını saklayan değişkenler
roi1_prev_status = None
roi2_prev_status = None
roi3_prev_status = None
roi4_prev_status = None
roi5_prev_status = None
roi6_prev_status = None

def apply_transparent_color(image, points, color, opacity):
    overlay = image.copy()
    points = np.array(points, dtype=np.int32)
    cv.fillPoly(overlay, [points], color)
    cv.addWeighted(overlay, opacity, image, 1 - opacity, 0, image)

# ROI çizgilerini şeffaf çizmek için bir fonksiyon
def draw_transparent_lines(image, points, color, opacity):
    overlay = image.copy()  # Görüntü kopyası
    points = np.array(points, dtype=np.int32)
    cv.polylines(overlay, [points], isClosed=True, color=color, thickness=1)  # Çizgileri overlay'e çiz
    cv.addWeighted(overlay, opacity, image, 1 - opacity, 0, image)  # Overlay'i ana görüntüye ekle


# Önceki durumları saklamak için değişkenler
prev_occupied_count = None
prev_empty_count = None
prev_empty_slots = []

# Kamera yeniden bağlanma fonksiyonu
retry_count = 0
max_retries = 20

def reconnect_camera():
    global cap, retry_count
    cap.release()  # Mevcut kamerayı serbest bırak
    print(f"Kamera bağlantısı kesildi, {retry_count}/{max_retries} deneme yapılıyor... 3 dakika bekleniyor.")
    time.sleep(180)  # 3 dakika bekle
    cap = cv.VideoCapture('http://xxxxxxxxxxxxxxxxion=stream')  # Kamerayı yeniden bağla
    if cap.isOpened():  # Kamera başarılı bir şekilde bağlanırsa
        print(f"Kamera bağlantısı {retry_count}. denemede başarıyla kuruldu!")
        retry_count = 0  # Deneme sayısını sıfırla
        return True
    if retry_count >= max_retries:
        print(f"Kamera bağlantısı {max_retries} deneme sonrası başarısız oldu. Çıkılıyor...")
        return False
    return True


try:
    while True:  # Döngü sürekli çalışmalı
        # Kamera bağlantısını kontrol et
        if not cap.isOpened():
            if not reconnect_camera():
                break  # Maksimum deneme sayısına ulaşıldıysa çıkış yap

        ret, image = cap.read()
        if not ret or image is None:
            print('Görüntü alınamadı, kamera yeniden bağlanıyor...')
            if not reconnect_camera():
                break  # Maksimum deneme sayısına ulaşıldıysa çıkış yap
            continue  # Yeniden bağlanma sonrası döngüye devam et
            print(f"Kamera bağlantısı {retry_count} defa yeniden denendi ve bağlandı  ...")
        
        
        # Doluluk ve boş sayısını sıfırla
        occupied_count = 0
        empty_count = 0
        empty_slots = []
        
        # Model tahmini (confidence %35 olarak ayarlanır)
        results = model(image, conf=0.30)#----------------> Model Tahmini
        if not results:
            print("nesne yok, atla...")
            continue

        # Görüntü kopyası al
        segments = image.copy()

        # Tespit edilen nesnelerin maskelerini ve etiketlerini çiz
        roi1_occupied = False  # roi1'de nesne olup olmadığını kontrol etmek için bayrak
        roi2_occupied = False  # roi2'de nesne olup olmadığını kontrol etmek için bayrak
        roi3_occupied = False  # roi3'de nesne olup olmadığını kontrol etmek için bayrak
        roi4_occupied = False  # roi4'de nesne olup olmadığını kontrol etmek için bayrak
        roi5_occupied = False  # roi5'de nesne olup olmadığını kontrol etmek için bayrak
        roi6_occupied = False  # roi6'de nesne olup olmadığını kontrol etmek için bayrak
        
        specific_pixel_occupied_roi1 = False  # roi1 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak
        specific_pixel_occupied_roi2 = False  # roi2 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak
        specific_pixel_occupied_roi3 = False  # roi3 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak
        specific_pixel_occupied_roi4 = False  # roi4 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak
        specific_pixel_occupied_roi5 = False  # roi5 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak
        specific_pixel_occupied_roi6 = False  # roi6 için belirtilen pikselde nesne olup olmadığını kontrol için bayrak

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
                    # Yalnızca confidence %25 üzerindeyse işleme devam et
                    if confidences[i] < 0.25:
                        continue

                    # Maskeyi görüntü boyutlarına yeniden boyutlandır
                    mask_resized = cv.resize(mask, (segments.shape[1], segments.shape[0]))
                    mask_resized = (mask_resized > 0.5).astype("uint8")  # Binary hale getir


                    if mask_resized[specific_pixel_roi1[1], specific_pixel_roi1[0]] == 1:
                        specific_pixel_occupied_roi1 = True
                    if mask_resized[specific_pixel_roi2[1], specific_pixel_roi2[0]] == 1:
                        specific_pixel_occupied_roi2 = True
                    if mask_resized[specific_pixel_roi3[1], specific_pixel_roi3[0]] == 1:
                        specific_pixel_occupied_roi3 = True
                    if mask_resized[specific_pixel_roi4[1], specific_pixel_roi4[0]] == 1:
                        specific_pixel_occupied_roi4 = True
                    if mask_resized[specific_pixel_roi5[1], specific_pixel_roi5[0]] == 1:
                        specific_pixel_occupied_roi5 = True
                    if mask_resized[specific_pixel_roi6[1], specific_pixel_roi6[0]] == 1:
                        specific_pixel_occupied_roi6 = True



                    # Maske sınırlarını çiz
                    contours, _ = cv.findContours(mask_resized, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
                    cv.drawContours(segments, contours, -1, (0, 255, 0), 1)  # Sarı renkli sınırlar

#                     Şeffaf maske ekle
#                    colored_mask = np.zeros_like(segments, dtype=np.uint8)
#                    colored_mask[mask_resized == 1] = [0, 0, 255]  # Yeşil renk
#                    segments = cv.addWeighted(segments, 0.98, colored_mask, 0.02, 1)  # Şeffaflık

                    # Belirli bir pikselde nesne kontrolü (ROI 1)
                    if mask_resized[specific_pixel_roi1[1], specific_pixel_roi1[0]] == 1:
                        specific_pixel_occupied_roi1 = True

                    # Belirli bir pikselde nesne kontrolü (ROI 2)
                    if mask_resized[specific_pixel_roi2[1], specific_pixel_roi2[0]] == 1:
                        specific_pixel_occupied_roi2 = True

                    # Belirli bir pikselde nesne kontrolü (ROI 3)
                    if mask_resized[specific_pixel_roi3[1], specific_pixel_roi3[0]] == 1:
                        specific_pixel_occupied_roi3 = True
                        
                        
                    # Belirli bir pikselde nesne kontrolü (ROI 4)
                    if mask_resized[specific_pixel_roi4[1], specific_pixel_roi4[0]] == 1:
                        specific_pixel_occupied_roi4 = True
                                                
                    # Belirli bir pikselde nesne kontrolü (ROI 5)
                    if mask_resized[specific_pixel_roi5[1], specific_pixel_roi5[0]] == 1:
                        specific_pixel_occupied_roi5 = True

                    # Belirli bir pikselde nesne kontrolü (ROI 6)
                    if mask_resized[specific_pixel_roi6[1], specific_pixel_roi6[0]] == 1:
                        specific_pixel_occupied_roi6 = True
                        
#                     Etiket ve confidence değerini kutunun üstüne ekle
#                    x1, y1, x2, y2 = map(int, boxes[i])  # Kutunun koordinatları
#                    original_label = model.names[int(classes[i])]  # Orijinal sınıf adı
#                    label = turkish_labels.get(original_label, original_label)  # Türkçe karşılığını al
#                    confidence_text = f"{label} ({confidences[i]:.2f})"  # Etiket ve confidence
#                    cv.putText(segments, confidence_text, (x1, y1 - 3), cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)


        # roi1 çiz (şeffaf çizgi)
        draw_transparent_lines(segments, roi1_points, (0, 255, 255), 0.25)

        # roi2 çiz (şeffaf çizgi)
        draw_transparent_lines(segments, roi2_points, (0, 255, 255), 0.25)

        # roi3 çiz (şeffaf çizgi)
        draw_transparent_lines(segments, roi3_points, (0, 255, 255), 0.25)

        # roi4 çiz (şeffaf çizgi)
        draw_transparent_lines(segments, roi4_points, (0, 255, 255), 0.25)

        # roi5 çiz (şeffaf çizgi)
        draw_transparent_lines(segments, roi5_points, (0, 255, 255), 0.25)

        # roi6 çiz (şeffaf çizgi)
        draw_transparent_lines(segments, roi6_points, (0, 255, 255), 0.25)

#         roi1 çiz (çokgen)
#        cv.polylines(
#            segments, [np.array(roi1_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
#        )

#         roi2 çiz (çokgen)
#        cv.polylines(
#            segments, [np.array(roi2_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
#        )
#         roi3 çiz (çokgen)
#        cv.polylines(
#            segments, [np.array(roi3_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
#        )
#                 roi4 çiz (çokgen)
#        cv.polylines(
#            segments, [np.array(roi4_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
#        )
#         roi5 çiz (çokgen)
#        cv.polylines(
#            segments, [np.array(roi5_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
#        )
#         roi6 çiz (çokgen)
#        cv.polylines(
#            segments, [np.array(roi6_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=1
#        )

        # Belirli bir koordinatın BGR değerlerini kontrol et --------> Gece kontrol noktası
        coordinate = (35, 15)  # x=35, y=15
        b, g, r = segments[coordinate[1], coordinate[0]]  # OpenCV'de sıra (y, x)
        
        # Terminalde yazdır
        #print(f"Koordinat ({coordinate[0]}, {coordinate[1]}) için BGR değeri: B={b}, G={g}, R={r}")
        
        aksam = b < 10 and g < 10 and r < 10
        
        # Eğer B, G, R değerleri 10'dan küçükse
        if b < 10 and g < 10 and r < 10:
            # OpenCV görüntüsünü Pillow formatına dönüştür
            pil_image = Image.fromarray(cv.cvtColor(segments, cv.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            # Yazı pozisyonu ve yazı
            text_position = (coordinate[0] + 10, coordinate[1])
            draw.text(text_position, "Akşam olduğu için tespit yapılamıyor.", font=font, fill=(255, 255, 0))  # Sarı renk
            
            # Pillow görüntüsünü tekrar OpenCV formatına dönüştür
            segments = cv.cvtColor(np.array(pil_image), cv.COLOR_RGB2BGR)  
                 
        # ROI 1'nin durumunu kontrol et ve yazı yaz
        if aksam:
            # Akşam durumu varsa ekrana yazma, sadece MQTT mesajı gönder
            result = mqtt_client.publish(MQTT_TOPIC_SLOT1, "Akşam tespit edilmiyor.")
            if result.rc == 0:
                pass #print("MQTT Mesaj yayınlandı: Akşam oldu")
        else:
            # Akşam değilse, ROI durumunu kontrol et ve yaz
            current_time = time.localtime()
            if specific_pixel_occupied_roi1:
                cv.putText(segments, "DOLU", roi1_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                apply_transparent_color(segments, roi1_points, (0, 0, 255), 0.10)  # BGR: kırmızı
                
                # Durum değiştiğinde saati kaydet
                if roi1_prev_status != specific_pixel_occupied_roi1:
                    roi1_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                # Park etme saatini göster
                if roi1_status_hour:
                    time_position = (roi1_bottom_left[0], roi1_bottom_left[1] + 10)
                    cv.putText(segments, f"Park: {roi1_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)

                if specific_pixel_occupied_roi1 != roi1_prev_status:
                    if specific_pixel_occupied_roi1:
                        result = mqtt_client.publish(MQTT_TOPIC_SLOT1, "Slot 1 dolu")
                        if result.rc == 0:
                            print("MQTT Mesaj yayınlandı: Slot 1 dolu")
            else:
                cv.putText(segments, "BOS", roi1_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                apply_transparent_color(segments, roi1_points, (0, 255, 0), 0.25)  # BGR: yeşil
                if roi1_prev_status != specific_pixel_occupied_roi1:
                    roi1_status_time = current_time

                # Durum değiştiğinde saati kaydet
                if roi1_prev_status != specific_pixel_occupied_roi1:
                    roi1_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                # Boşalma saatini göster
                if roi1_status_hour:
                    time_position = (roi1_bottom_left[0], roi1_bottom_left[1] + 10)
                    cv.putText(segments, f"Bos: {roi1_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                if specific_pixel_occupied_roi1 != roi1_prev_status:
                  result = mqtt_client.publish(MQTT_TOPIC_SLOT1, "Slot 1 boş")
                  if result.rc == 0:
                    print("MQTT Mesaj yayınlandı: Slot 1 boş")
        
        # roi 1'nin önceki durumunu güncelle
        roi1_prev_status = specific_pixel_occupied_roi1

        # ROI 2'nin durumunu kontrol et ve yazı yaz
        if aksam:
            # Akşam durumu varsa ekrana yazma, sadece MQTT mesajı gönder
            result = mqtt_client.publish(MQTT_TOPIC_SLOT2, "Akşam tespit edilmiyor.")
            if result.rc == 0:
               pass #print("MQTT Mesaj yayınlandı: Akşam oldu")
        else:
            # Akşam değilse, ROI durumunu kontrol et ve yaz
            current_time = time.localtime()
            if specific_pixel_occupied_roi2:
                cv.putText(segments, "DOLU", roi2_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                apply_transparent_color(segments, roi2_points, (0, 0, 255), 0.10)  # BGR: kırmızı
                # Durum değiştiğinde saati kaydet
                if roi2_prev_status != specific_pixel_occupied_roi2:
                    roi2_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Park etme saatini göster
                if roi2_status_hour:
                    time_position = (roi2_bottom_left[0], roi2_bottom_left[1] + 20)
                    cv.putText(segments, f"Park: {roi2_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                             
                if specific_pixel_occupied_roi2 != roi2_prev_status:
                    if specific_pixel_occupied_roi2:
                        result = mqtt_client.publish(MQTT_TOPIC_SLOT2, "Slot 2 dolu")
                        if result.rc == 0:
                            print("MQTT Mesaj yayınlandı: Slot 2 dolu")
            else:
                cv.putText(segments, "BOS", roi2_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                apply_transparent_color(segments, roi2_points, (0, 255, 0), 0.15)  # BGR: yeşil
                # Durum değiştiğinde saati kaydet
                if roi2_prev_status != specific_pixel_occupied_roi2:
                    roi2_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Boşalma saatini göster
                if roi2_status_hour:
                    time_position = (roi2_bottom_left[0], roi2_bottom_left[1] + 20)
                    cv.putText(segments, f"Bos: {roi2_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                if specific_pixel_occupied_roi2 != roi2_prev_status:
                  result = mqtt_client.publish(MQTT_TOPIC_SLOT2, "Slot 2 boş")
                  if result.rc == 0:
                    print("MQTT Mesaj yayınlandı: Slot 2 boş")
        
        # ROI 2'nin önceki durumunu güncelle
        roi2_prev_status = specific_pixel_occupied_roi2
        
        # roi 3'nin durumunu kontrol et ve yazı yaz
        if aksam:
            # Akşam durumu varsa ekrana yazma, sadece MQTT mesajı gönder
            result = mqtt_client.publish(MQTT_TOPIC_SLOT3, "Akşam oldu")
            if result.rc == 0:
                pass #print("MQTT Mesaj yayınlandı: Akşam oldu")
        else:
            current_time = time.localtime()
            # Akşam değilse, ROI durumunu kontrol et ve yaz
            if specific_pixel_occupied_roi3:
                cv.putText(segments, "DOLU", roi3_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                apply_transparent_color(segments, roi3_points, (0, 0, 255), 0.10)  # BGR: kırmızı
                # Durum değiştiğinde saati kaydet
                if roi3_prev_status != specific_pixel_occupied_roi3:
                    roi3_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Park etme saatini göster
                if roi3_status_hour:
                    time_position = (roi3_bottom_left[0], roi3_bottom_left[1] + 10)
                    cv.putText(segments, f"Park: {roi3_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                if specific_pixel_occupied_roi3 != roi3_prev_status:
                    if specific_pixel_occupied_roi3:
                        result = mqtt_client.publish(MQTT_TOPIC_SLOT3, "Slot 3 dolu")
                        if result.rc == 0:
                            print("MQTT Mesaj yayınlandı: Slot 3 dolu")
            else:
                cv.putText(segments, "BOS", roi3_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                apply_transparent_color(segments, roi3_points, (0, 255, 0), 0.15)  # BGR: yeşil
                # Durum değiştiğinde saati kaydet
                if roi3_prev_status != specific_pixel_occupied_roi3:
                    roi3_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Boşalma saatini göster
                if roi3_status_hour:
                    time_position = (roi3_bottom_left[0], roi3_bottom_left[1] + 10)
                    cv.putText(segments, f"Bos: {roi3_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                if specific_pixel_occupied_roi3 != roi3_prev_status:
                  result = mqtt_client.publish(MQTT_TOPIC_SLOT3, "Slot 3 boş")
                  if result.rc == 0:
                    print("MQTT Mesaj yayınlandı: Slot 3 boş")
        
        # roi 3'nin önceki durumunu güncelle
        roi3_prev_status = specific_pixel_occupied_roi3

        
        # roi 4'nin durumunu kontrol et ve yazı yaz
        if aksam:
            # Akşam durumu varsa ekrana yazma, sadece MQTT mesajı gönder
            result = mqtt_client.publish(MQTT_TOPIC_SLOT4, "Akşam oldu")
            if result.rc == 0:
                pass #print("MQTT Mesaj yayınlandı: Akşam oldu")
        else:
            current_time = time.localtime()
            # Akşam değilse, ROI durumunu kontrol et ve yaz
            if specific_pixel_occupied_roi4:
                cv.putText(segments, "DOLU", roi4_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                apply_transparent_color(segments, roi4_points, (0, 0, 255), 0.10)  # BGR: kırmızı
                # Durum değiştiğinde saati kaydet
                if roi4_prev_status != specific_pixel_occupied_roi4:
                    roi4_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Park etme saatini göster
                if roi4_status_hour:
                    time_position = (roi4_bottom_left[0], roi4_bottom_left[1] + 20)
                    cv.putText(segments, f"Park: {roi4_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                if specific_pixel_occupied_roi4 != roi4_prev_status:
                    if specific_pixel_occupied_roi3:
                        result = mqtt_client.publish(MQTT_TOPIC_SLOT4, "Slot 4 dolu")
                        if result.rc == 0:
                            print("MQTT Mesaj yayınlandı: Slot 4 dolu")
            else:
                cv.putText(segments, "BOS", roi4_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                apply_transparent_color(segments, roi4_points, (0, 255, 0), 0.15)  # BGR: yeşil
                # Durum değiştiğinde saati kaydet
                if roi4_prev_status != specific_pixel_occupied_roi4:
                    roi4_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Boşalma saatini göster
                if roi4_status_hour:
                    time_position = (roi4_bottom_left[0], roi4_bottom_left[1] + 20)
                    cv.putText(segments, f"Bos: {roi4_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                if specific_pixel_occupied_roi4 != roi4_prev_status:
                  result = mqtt_client.publish(MQTT_TOPIC_SLOT4, "Slot 4 boş")
                  if result.rc == 0:
                    print("MQTT Mesaj yayınlandı: Slot 4 boş")
        
        # roi 4'nin önceki durumunu güncelle
        roi4_prev_status = specific_pixel_occupied_roi4


        # roi 5'nin durumunu kontrol et ve yazı yaz
        if aksam:
            # Akşam durumu varsa ekrana yazma, sadece MQTT mesajı gönder
            result = mqtt_client.publish(MQTT_TOPIC_SLOT5, "Akşam oldu")
            if result.rc == 0:
                pass #print("MQTT Mesaj yayınlandı: Akşam oldu")
        else:
            current_time = time.localtime()
            # Akşam değilse, ROI durumunu kontrol et ve yaz
            if specific_pixel_occupied_roi5:
                cv.putText(segments, "DOLU", roi5_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                apply_transparent_color(segments, roi5_points, (0, 0, 255), 0.10)  # BGR: kırmızı
                # Durum değiştiğinde saati kaydet
                if roi5_prev_status != specific_pixel_occupied_roi5:
                    roi5_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Park etme saatini göster
                if roi5_status_hour:
                    time_position = (roi5_bottom_left[0], roi5_bottom_left[1] + 10)
                    cv.putText(segments, f"Park: {roi5_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                if specific_pixel_occupied_roi5 != roi5_prev_status:
                    if specific_pixel_occupied_roi5:
                        result = mqtt_client.publish(MQTT_TOPIC_SLOT5, "Slot 5 dolu")
                        if result.rc == 0:
                            print("MQTT Mesaj yayınlandı: Slot 5 dolu")
            else:
                cv.putText(segments, "BOS", roi5_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                apply_transparent_color(segments, roi5_points, (0, 255, 0), 0.15)  # BGR: yeşil
                # Durum değiştiğinde saati kaydet
                if roi5_prev_status != specific_pixel_occupied_roi5:
                    roi5_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Boşalma saatini göster
                if roi5_status_hour:
                    time_position = (roi5_bottom_left[0], roi5_bottom_left[1] + 10)
                    cv.putText(segments, f"Bos: {roi5_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                if specific_pixel_occupied_roi5 != roi5_prev_status:
                  result = mqtt_client.publish(MQTT_TOPIC_SLOT5, "Slot 5 boş")
                  if result.rc == 0:
                    print("MQTT Mesaj yayınlandı: Slot 5 boş")
        
        # roi 5'nin önceki durumunu güncelle
        roi5_prev_status = specific_pixel_occupied_roi5

        # roi 6'nin durumunu kontrol et ve yazı yaz
        if aksam:
            # Akşam durumu varsa ekrana yazma, sadece MQTT mesajı gönder
            result = mqtt_client.publish(MQTT_TOPIC_SLOT6, "Akşam oldu")
            if result.rc == 0:
               pass #print("MQTT Mesaj yayınlandı: Akşam oldu")
        else:
            # Akşam değilse, ROI durumunu kontrol et ve yaz
            current_time = time.localtime()
            if specific_pixel_occupied_roi6:
                cv.putText(segments, "DOLU", roi6_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                apply_transparent_color(segments, roi6_points, (0, 0, 255), 0.10)  # BGR: kırmızı
                # Durum değiştiğinde saati kaydet
                if roi6_prev_status != specific_pixel_occupied_roi6:
                    roi6_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Park etme saatini göster
                if roi6_status_hour:
                    time_position = (roi6_bottom_left[0], roi6_bottom_left[1] + 20)
                    cv.putText(segments, f"Park: {roi6_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                if specific_pixel_occupied_roi6 != roi6_prev_status:
                    if specific_pixel_occupied_roi6:
                        result = mqtt_client.publish(MQTT_TOPIC_SLOT6, "Slot 6 dolu")
                        if result.rc == 0:
                            print("MQTT Mesaj yayınlandı: Slot 6 dolu")
            else:
                cv.putText(segments, "BOS", roi6_bottom_left, cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                apply_transparent_color(segments, roi6_points, (0, 255, 0), 0.15)  # BGR: yeşil
                # Durum değiştiğinde saati kaydet
                if roi6_prev_status != specific_pixel_occupied_roi6:
                    roi6_status_hour = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                
                # Boşalma saatini göster
                if roi6_status_hour:
                    time_position = (roi6_bottom_left[0], roi6_bottom_left[1] + 20)
                    cv.putText(segments, f"Bos: {roi6_status_hour}", time_position, 
                             cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                if specific_pixel_occupied_roi6 != roi6_prev_status:
                  result = mqtt_client.publish(MQTT_TOPIC_SLOT6, "Slot 6 boş")
                  if result.rc == 0:
                      print("MQTT Mesaj yayınlandı: Slot 6 boş")
        
        # roi 6'nin önceki durumunu güncelle
        roi6_prev_status = specific_pixel_occupied_roi6
        
        
        
        # ROI durumlarını kontrol et
        if specific_pixel_occupied_roi1:
            occupied_count += 1
        else:
            empty_count += 1
            empty_slots.append(1)

        if specific_pixel_occupied_roi2:
            occupied_count += 1
        else:
            empty_count += 1
            empty_slots.append(2)

        if specific_pixel_occupied_roi3:
            occupied_count += 1
        else:
            empty_count += 1
            empty_slots.append(3)

        if specific_pixel_occupied_roi4:
            occupied_count += 1
        else:
            empty_count += 1
            empty_slots.append(4)

        if specific_pixel_occupied_roi5:
            occupied_count += 1
        else:
            empty_count += 1
            empty_slots.append(5)

        if specific_pixel_occupied_roi6:
            occupied_count += 1
        else:
            empty_count += 1
            empty_slots.append(6)
            
            
            
        # Durum değişmişse güncelle ve MQTT ile yayınla
        if (occupied_count != prev_occupied_count or 
            empty_count != prev_empty_count or 
            empty_slots != prev_empty_slots):
            
            if aksam:
                print("Akşam tespit yapılamıyor")
                mqtt_client.publish("parking/status/empty_slots", "Akşam tespit yapılamıyor", retain=True)
                mqtt_client.publish("parking/status/occupied", "Akşam tespit yapılamıyor", retain=True)
                mqtt_client.publish("parking/status/empty", "Akşam tespit yapılamıyor", retain=True)
            else:
                print(f"Dolu park yerleri: {occupied_count}, Boş park yerleri: {empty_count}")
                if empty_slots:
                    print(f"Boş park yerleri: {', '.join(map(str, empty_slots))}")
                    mqtt_client.publish("parking/status/empty_slots", ','.join(map(str, empty_slots)), retain=True)
                else:
                    print("Boş park yeri yok")
                    mqtt_client.publish("parking/status/empty_slots", "none", retain=True)
                
                mqtt_client.publish("parking/status/occupied", str(occupied_count), retain=True)
                mqtt_client.publish("parking/status/empty", str(empty_count), retain=True)
            
            prev_occupied_count = occupied_count
            prev_empty_count = empty_count
            prev_empty_slots = empty_slots      
        
        
        
        # Görüntüyü ekranda göster
        cv.imshow('Otopark Kontrol', segments)

        # Çıkış için 'q' tuşuna basılması gerekiyor
        key = cv.waitKey(1)
        if key & 0xFF == ord('q'):
            print('Çıkış işlemi başlatıldı.')
            break

finally:
    cap.release()
    cv.destroyAllWindows()
