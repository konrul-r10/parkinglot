


📶 Canlı Kamera Akışı ve Görüntü İşleme <br>
✔️ IP Kamera bağlantısı kuruluyor ve görüntü alınıyor.<br>
✔️ Kamera bağlantısı kesildiğinde otomatik yeniden bağlanma mekanizması var.<br>
✔️ Gece ve gündüz koşullarına göre parlaklık ve kontrast ayarı yapıyor.<br>
✔️ Görüntü işleme için CLAHE (Kontrast iyileştirme) ve keskinleştirme filtresi uygulanıyor.<br>
✔️ Parlaklık ve kontrast dinamik olarak ayarlanabiliyor.<br>

🤖 Yapay Zeka Tabanlı Nesne Tespiti (YOLOv8)<br>
✔️ YOLOv8 segmentasyon modeli kullanılarak araç, insan, bisiklet gibi nesneler tespit ediliyor.<br>
✔️ Sadece belirlenen nesneleri (araba, kamyon, motosiklet, bisiklet vb.) algılıyor.<br>
✔️ Segmentasyon maskeleri kullanılarak otoparktaki nesneler belirleniyor.<br>
✔️ Her park alanı için tespit edilen nesnelerin koordinatları kontrol ediliyor.<br>
✔️ Minimum %35 doğruluk seviyesine ulaşan nesneler geçerli kabul ediliyor.<br>

🅿️ Park Alanı Takibi (ROI - Region of Interest)<br>
✔️ Otoparktaki 6 farklı park alanı (ROI) ayrı ayrı takip ediliyor.<br>
✔️ Belirlenen bölgelerde nesne olup olmadığı tespit ediliyor.<br>
✔️ Şeffaf renkler kullanılarak dolu ve boş alanlar işaretleniyor.<br>
✔️ Her park alanı için ayrı sayaçlar kullanılarak doluluk durumları hassas bir şekilde belirleniyor.<br>

🚦 Debouncing / Stabil Sayım Mekanizması<br>
✔️ Her bir park alanı (ROI) için ayrı bir sayaç bulunur.<br>
✔️ Bir alanın dolu veya boş olduğu belirli bir süre boyunca sabit kalırsa değişiklik kabul edilir.<br>
✔️ Ani değişiklikler (örneğin birinin park alanından hızlıca geçmesi) yanlış algılanmaz.<br>
✔️ Her ROI için bir önceki durum kaydedilir ve sadece belirlenen ardışık kare sayısından sonra güncellenir.<br>

🌞 Gece ve Gündüz Tespiti<br>
✔️ Çorlu’nun gün doğumu ve gün batımı saatleri hesaplanıyor.<br>
✔️ Güneş battığında veya doğmadan önce tespit devre dışı bırakılıyor.<br>
✔️ Gece modunda "Akşam olduğu için tespit yapılamıyor." mesajı görüntüleniyor ve MQTT ile bildirim gönderiliyor.<br>
✔️ Gece tespit yapılmazken görüntü parlaklaştırılarak görünürlük artırılıyor.<br>

📡 MQTT ile Anlık Veri Paylaşımı<br>
✔️ Tespit edilen dolu ve boş park alanları MQTT üzerinden gönderiliyor.<br>
✔️ Her bir park alanı için ayrı ayrı MQTT mesajları yayınlanıyor:<br>

Slot 1 Dolu / Boş<br>
Slot 2 Dolu / Boş<br>
Slot 3 Dolu / Boş<br>
Slot 4 Dolu / Boş<br>
Slot 5 Dolu / Boş<br>
Slot 6 Dolu / Boş<br>
✔️ Toplam dolu ve boş park yeri sayısı MQTT ile gönderiliyor.<br>
✔️ Gece modunda "Akşam olduğu için tespit yapılamıyor." mesajı MQTT’ye yayınlanıyor.<br>
📊 JSON Formatında Veri Paylaşımı<br>
✔️ Otoparktaki doluluk verileri başka sistemlerle entegrasyon için JSON formatında sunulabilir.<br>
✔️ Harici uygulamalar park yeri doluluk durumunu anlık olarak takip edebilir.<br>

⚡ Hata ve Bağlantı Yönetimi<br>
✔️ Kamera bağlantısı düştüğünde 3 dakika bekleyip tekrar bağlanmayı dener.<br>
✔️ Maksimum 20 bağlantı denemesi yapılır, eğer bağlantı sağlanamazsa işlem durdurulur.<br>
✔️ Görüntü alınamazsa sistem otomatik olarak kendini yenileyerek tekrar başlatılır.<br>

🎯 Sonuç<br>
Sistem, otopark alanlarını sürekli izleyerek dolu ve boş alanları tespit eder.<br>
Gece ve gündüz değişimlerine göre çalışma modunu otomatik ayarlar.<br>
MQTT ile tüm verileri paylaşarak uzaktan takip imkanı sunar.<br>
Kullanıcılar, otoparkın doluluk durumunu anlık olarak görebilir.<br>
Kamera bağlantı sorunlarına karşı dayanıklı bir yapıya sahiptir.<br>
👉 Bu sistem, otopark yönetimi ve park yeri izleme için akıllı, dinamik ve uzaktan kontrol edilebilir bir çözüm sunar. 🚗🅿️<br>
<br>

Not:Ubuntu versiyonda çalıştırılmak üzere yapılmıştır. Kamera açısı değişirse, lot yerleri değişir, ROI kodları güncellenir.
