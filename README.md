# Akıllı Hastane Ameliyathane Planlama ve Kaynak Optimizasyon Sistemi

Bu proje, bir hastanenin günlük ameliyathane kullanımını, cerrah takvimlerini ve anestezi ekiplerini çakışmaları önleyerek optimize eden bir planlama sistemidir. NP-Hard sınıfındaki "Çoklu Kaynak Planlaması" problemini çözmek amacıyla geliştirilmiştir. 

Aşağıdaki dokümantasyon, proje teslimatında beklenen kriterlere göre hazırlanmıştır.

---

## 1. Kaynak Kod Mimarisi
Proje, In-Memory çalışan "Stateless" bir Django REST API olarak tasarlanmıştır. 
*   **`scheduler/services.py`**: Heuristic sıralama, Backtracking algoritması ve Constraint (Kısıt) motorunun çalıştığı ana algoritma dosyasıdır.
*   **`scheduler/views.py`**: Gelen JSON verisini karşılayan ve Plotly ile Gantt Chart render eden API uç noktalarını (Endpoints) içerir.

---

## 2.  Algoritma Açıklaması
Problem, literatürde NP-hard sınıfına giren "Multi-resource scheduling" (Çoklu kaynak planlaması) problemidir. Çözüm için Heuristic Search (Sezgisel Arama) ve Backtracking (Geri İzleme) hibrit algoritması kullanılmıştır.

1.  **Heuristic Önceliklendirme:** Hastalar rastgele taranmaz. Algoritma başlamadan önce hastalar aciliyet seviyelerine (Kritik, Yüksek, Orta, Düşük) ve operasyon sürelerine göre büyükten küçüğe sıralanır. Bu sayede kritik hastaların en erken zaman slotlarına yerleşmesi garanti altına alınır..
2.  **Backtracking:** Algoritma; oda, cerrah, ekip ve zaman aralıklarını özyinelemeli (recursive) bir fonksiyonla tarar. Kısıtları ihlal eden bir çıkmaz sokağa girildiğinde (örneğin son hastaya boş oda kalmaması), algoritma bir adım geri (undo) atarak kaynakları serbest bırakır ve alternatif dalı denemeye başlar.
3.  **Cost/Penalty (Ceza) Optimizasyonu:** Algoritma bulduğu ilk geçerli planda durmaz. Belirlenen bir limite kadar birden fazla geçerli çözüm üretir ve bu çözümleri "Soft Constraints" (Esnek kısıtlar) açısından cezalandırarak puanlar. En düşük maliyetli (en optimum) plan çıktı olarak seçilir.
---

## 3. Constraint Modeli

###  Hard Constraints (is_valid fonksiyonu)
İhlal edilemez kurallardır, atama anında reddedilir:
*   **Mesai ve İzin Kontrolü:** Operasyonlar 18:00'i aşamaz ve doktorlar izinli günlerinde (Örn: Dr. Ahmet - Çarşamba) çalıştırılamaz.
*   **Kaynak Çakışması:** Bir cerrah, ekip veya oda aynı anda birden fazla operasyona giremez.
*   **Uzmanlık Uyumu:** Sadece ilgili uzman (Örn: Kalp Anjiyo -> Kardiyoloji) ve desteklenen ameliyathane eşleştiğinde atama yapılır.
*   **Dinlenme Zorunluluğu:** 4 slot (2 saat) kesintisiz ameliyata giren cerrah, araya en az 1 slot (30 dk) dinlenme molası almak zorundadır.
*   **Bölünemez Operasyon:** Bir ameliyat başladıktan sonra planlamada parçalanamaz, blok halinde sürer.

### Soft Constraints (calculate_penalty fonksiyonu)
Minimize edilmesi hedeflenen optimizasyon kurallarıdır:
*   Cerrah ve Ameliyathane idle time (boş bekleme süresi) maliyetleri.
*   Anestezi ekipleri arasındaki operasyon sayısı (iş yükü) eşitsizliği maliyeti.
*   Kritik hastaların bekletilme maliyeti.

---

## 4.  Örnek Input (JSON)
Sistemin kısıtlarını (Çarşamba günü doktor izni kısıtı dahil) test etmek için hazırlanan örnek `POST` isteği gövdesi

```json
{
  "day": "Çarşamba",
  "patients": [
    {"id": "P1", "operation": "Apandisit", "required_specialty": "Genel Cerrahi", "duration": 2, "priority": "Yüksek"},
    {"id": "P3", "operation": "Kalp Anjiyo", "required_specialty": "Kardiyoloji", "duration": 3, "priority": "Kritik"},
    {"id": "P5", "operation": "Safra Kesesi", "required_specialty": "Genel Cerrahi", "duration": 2, "priority": "Düşük"}
  ],
  "surgeons": [
    {"id": "Dr. Ahmet", "specialty": "Genel Cerrahi"},
    {"id": "Dr. Can", "specialty": "Genel Cerrahi"},
    {"id": "Dr. Ayşe", "specialty": "Kardiyoloji"}
  ],
  "rooms": [
    {"id": "OR-1", "type": "Genel Cerrahi", "supported_operations": ["Apandisit", "Safra Kesesi"]},
    {"id": "OR-2", "type": "Kardiyoloji", "supported_operations": ["Kalp Anjiyo"]}
  ],
  "teams": ["Team-A", "Team-B"]
} 
```

---

## 5. Üretilmiş Operasyon Planı
Yukarıdaki girdiye karşılık algoritmanın ürettiği, zaman çizelgesine uygun ve Dr. Ahmet'in izinli olduğu tespit edilerek iş yükünün Dr. Can'a kaydırıldığı başarılı çıktı örneği:  

```json
{
        "time": "08:00-09:30",
        "room": "OR-2",
        "patient": "P3 - Kalp Anjiyo",
        "surgeon": "Dr. Ayşe",
        "team": "Team-B"
    },
    {
        "time": "08:00-09:00",
        "room": "OR-1",
        "patient": "P1 - Apandisit",
        "surgeon": "Dr. Can",
        "team": "Team-A"
    },
    {
        "time": "09:00-10:00",
        "room": "OR-1",
        "patient": "P5 - Safra Kesesi",
        "surgeon": "Dr. Can",
        "team": "Team-A"
    }
```

---

## 6. Complexity (Karmaşıklık) Analizi

*   **Time Complexity:** Hastaların sıralanması O(n log n) zaman alır (n: Hasta Sayısı). Kesin kısıt motorumuzun mantıksız atamaları anında budaması (pruning) ve çözümün sabit bir üst limit ile (C=20) sınırlandırılması sayesinde operasyonel çalışma zamanı O(n log n + C x n) civarında lineer performansa yaklaştırılmıştır.

*   **Space Complexity:** Veritabanı I/O maliyetlerini önlemek için kaynak takvimi RAM üzerinde 20 zaman slotluk boolean matrisleriyle yönetilmiştir. Toplam alan karmaşıklığı O(n + (R + S + A) x T) düzeyindedir (R: Oda, S: Cerrah, A: Ekip, T: Zaman Slotu). Sistem, düşük RAM tüketimiyle yüksek ölçeklenebilirlik sunar.


