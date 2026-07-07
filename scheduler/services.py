import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def slot_to_time(slot): # 0-19 arası slot'u gerçek zamana çevirir örn -> slot 5 -> 10.30'a denk gelir
    hours = 8 + (slot // 2) # kalansız bölme(floor division)
    mins = "30" if slot % 2 != 0 else "00" #eğer slot tek sayı ise dakika kısmı 30 çift ise 00 alınır
    return f"{hours:02d}:{mins}" # dijital saate çeviriyoruz

def time_to_slot(time_str): # zamanı tekrar slot numarasına çevirir
    h, m = map(int, time_str.split(':'))
    return (h - 8) * 2 + (1 if m == 30 else 0)



def calculate_penalty_score(schedule, patients_data): # Soft constraintleri hesaplar düşük penalty skoru sağlamak amaç
    penalty = 0
    
    # hastaların öncelik verisine hızlı erişim için bir dictionary
    priority_map = {p['id']: p['priority'] for p in patients_data}
    
    surgeon_schedules = {}
    team_usage = {}
    room_schedules = {}

    for assignment in schedule:
        surgeon = assignment['surgeon']
        team = assignment['team']
        room = assignment['room']
        start = assignment['start_slot']
        end = start + assignment['duration']

        # Verileri gruplama
        surgeon_schedules.setdefault(surgeon, []).append((start, end))
        room_schedules.setdefault(room, []).append((start, end))
        team_usage[team] = team_usage.get(team, 0) + 1

        # soft constraint 1 kritik hastaların bekleme süresi cezası
        # kritik hasta ne kadar geç başlarsa o kadar yüksek ceza alır.
        if priority_map[assignment['patient']] == "Kritik":
            penalty += start * 10 

    # soft constraint 2 cerrah idle kalma süresi ve mesailer parçalı mı değil mi ona bakma
    for surgeon, times in surgeon_schedules.items():
        min_start = min([t[0] for t in times])
        max_end = max([t[1] for t in times])
        total_active = sum([t[1] - t[0] for t in times])
        
        idle_time = (max_end - min_start) - total_active
        penalty += idle_time * 5  # her 30 dk boşluk için 5 ceza puanı

    # soft sonstraint 3 ameliyathane idle kalma süresi
    for room, times in room_schedules.items():
        min_start = min([t[0] for t in times])
        max_end = max([t[1] for t in times])
        total_active = sum([t[1] - t[0] for t in times])
        
        room_idle = (max_end - min_start) - total_active
        penalty += room_idle * 3  # her 30 dk boşluk için 3 ceza puanı

    # soft constraint 4 anestezi takımlarının dengesiz kullanımı
    if team_usage:
        max_ops = max(team_usage.values())
        min_ops = min(team_usage.values())
        imbalance = max_ops - min_ops
        penalty += imbalance * 15  # ekipler arası her 1 ameliyat farkı için 15 ceza puanı

    return penalty


def generate_schedule(data):
    all_patients = data['patients']
    surgeons = data['surgeons']
    rooms = data['rooms']
    teams = data['teams']

    # JSON requestinden gelen işlem gününü al
    current_day = data.get('day', '')
    
    # Kilitli (geçmiş/devam eden) planları JSON'dan çekiyoruz
    locked_schedules = data.get('locked_schedules', [])

    # doktor izin günleri tablosu
    SURGEON_DAYS_OFF = {
        "Dr. Ahmet": "Çarşamba",
        "Dr. Ayşe": "Pazartesi",
        "Dr. Mehmet": "Salı",
        "Dr. Elif": "Perşembe",
        "Dr. Can": "Cuma"
    }

    TOTAL_SLOTS = 20
    
    # in-memory database kullandım projenin stateless olması için
    resource_availability = {
        "rooms": {r['id']: [True] * TOTAL_SLOTS for r in rooms},
        "surgeons": {s['id']: [True] * TOTAL_SLOTS for s in surgeons},
        "teams": {t: [True] * TOTAL_SLOTS for t in teams}
    }
    
    current_schedule = []
    valid_solutions = []
    MAX_SOLUTIONS = 20 # Performans için algoritmayı 20 valid çözümle sınırlıyoruz

   
    locked_patient_ids = set() # hangi hastaların atanıp atanmadığını takip etmek için
    
    for locked in locked_schedules:
        start = locked['start_slot']
        dur = locked['duration']
        patient_id = locked['patient']
        
        locked_patient_ids.add(patient_id)
        
        # Odanın, doktorun ve ekibin kilitli saatlerini dolu(false) hale getirdik
        for t in range(start, start + dur):
            if t < TOTAL_SLOTS: # 18:00'ı aşmamamız lazım
                resource_availability["rooms"][locked['room']][t] = False
                resource_availability["surgeons"][locked['surgeon']][t] = False
                resource_availability["teams"][locked['team']][t] = False
                
        # kitlendiği(locked) olduğu için doğrudan schedule'a append ettik
        current_schedule.append({
            "patient": patient_id,
            "operation": locked.get('operation', 'Tamamlanan/Devam Eden Operasyon'),
            "room": locked['room'],
            "surgeon": locked['surgeon'],
            "team": locked['team'],
            "start_slot": start,
            "duration": dur
        })

    # kilitli olmayan hastalar için patients değişkeni hazırlandı
    patients = [p for p in all_patients if p['id'] not in locked_patient_ids]
    

    # 1. Heuristic algoritma hastaları önem ve zaman derecelerine göre sıralar
    priority_weights = {"Kritik": 4, "Yüksek": 3, "Orta": 2, "Düşük": 1}
    patients.sort(key=lambda x: (priority_weights.get(x['priority'], 0), x['duration']), reverse=True)


    # Hard constraints fonksiyonu
    def is_valid(patient, room, surgeon, team, start_slot):
        duration = patient['duration']
        
        # Doktor izin günü kontrolü
        if current_day and SURGEON_DAYS_OFF.get(surgeon['id']) == current_day:
            return False
        
        # 18.00'dan sonra ameliyat olmayacak   
        if start_slot + duration > TOTAL_SLOTS:
            return False
            
        # eğer doktorun alanı değilse false döndür    
        if patient['required_specialty'] != surgeon['specialty']:
            return False
         
        # oda ameliyatı desteklemiyorsa ameliyat olmaz   
        supported_ops = room.get('supported_operations', [])
        if supported_ops and patient['operation'] not in supported_ops:
            return False
        
        # ameliyat boyunca tutulan oda tamamen boş olması lazım
        for t in range(start_slot, start_slot + duration):
            if not (resource_availability["rooms"][room['id']][t] and
                    resource_availability["surgeons"][surgeon['id']][t] and
                    resource_availability["teams"][team][t]):
                return False

        #  cerrah dinlenme constrainti
        busy_before = 0
        t_before = start_slot - 1
        while t_before >= 0 and not resource_availability["surgeons"][surgeon['id']][t_before]:
            busy_before += 1
            t_before -= 1
            
        busy_after = 0
        t_after = start_slot + duration
        while t_after < TOTAL_SLOTS and not resource_availability["surgeons"][surgeon['id']][t_after]:
            busy_after += 1
            t_after += 1
            
        if busy_before + duration + busy_after > 4:
            return False

        return True

        

    # backtracking algoritma fonksiyonu (recursive çalışır)
    def backtrack(patient_index):
        # Yeterli sayıda çözüm bulduysak aramayı durdur (MAX SOLUTIONS = 20)
        if len(valid_solutions) >= MAX_SOLUTIONS:
            return

        # Tüm hastalar yerleştiyse mevcut planın kopyasını kaydet return ile direkt çık
        if patient_index == len(patients):
            valid_solutions.append(list(current_schedule))
            return
            
        patient = patients[patient_index]
        duration = patient['duration']
        
        for start_slot in range(TOTAL_SLOTS):
            for room in rooms:
                for surgeon in surgeons:
                    for team in teams:
                        # hard constraintler çağrılır 
                        if is_valid(patient, room, surgeon, team, start_slot):
                            # yerleştir (doldurduğumuz zaman resource availability false yapılır)
                            for t in range(start_slot, start_slot + duration):
                                resource_availability["rooms"][room['id']][t] = False
                                resource_availability["surgeons"][surgeon['id']][t] = False
                                resource_availability["teams"][team][t] = False
                            # mevcut atamalar gösterilir
                            current_assignment = {
                                "patient": patient['id'],
                                "operation": patient['operation'],
                                "room": room['id'],
                                "surgeon": surgeon['id'],
                                "team": team,
                                "start_slot": start_slot,
                                "duration": duration
                            }
                            # en son olarak güncel schedule'e append ettik
                            current_schedule.append(current_assignment)
                            
                            # ileri git recursive şeklinde
                            backtrack(patient_index + 1)
                                
                            # sistem patlarsa schedule'den çıkart(pop et) ve resource'ları tekrar true(kullanılabilir) yap
                            current_schedule.pop()
                            for t in range(start_slot, start_slot + duration):
                                resource_availability["rooms"][room['id']][t] = True
                                resource_availability["surgeons"][surgeon['id']][t] = True
                                resource_availability["teams"][team][t] = True

    # algoritma başlar
    backtrack(0)
    
    # çözüm bulunamadıysa boş dön
    if not valid_solutions:
        return []

    # soft constraint değerlendirmesi
    # bulunan tüm geçerli planları ceza puanlarına göre hesapla
    best_schedule = None
    min_penalty = float('inf')
    # valid çözümleri bulduk ama soft contraintlere göre en optimal olanlarını seçmek istiyoruz
    for sol in valid_solutions:
        penalty = calculate_penalty_score(sol, patients)
        if penalty < min_penalty:
            min_penalty = penalty
            best_schedule = sol

    # API çıktısını formatlama
    # seçilen en iyi planın zaman aralıklarını okunabilir saatlere çevir
    formatted_schedule = []
    for item in best_schedule:
        start_time = slot_to_time(item['start_slot'])
        end_time = slot_to_time(item['start_slot'] + item['duration'])
        
        # API'ye döneceğimiz formatlanmış output
        formatted_schedule.append({
            "time": f"{start_time}-{end_time}",
            "room": item['room'],
            "patient": f"{item['patient']} - {item['operation']}",
            "surgeon": item['surgeon'],
            "team": item['team']
        })

    # Planı zaman çizelgesine göre (saat sırasına) dizerek döndür
    return sorted(formatted_schedule, key=lambda x: x['time'])

# Gantt chart oluşturma visualize endpointi ile
def generate_gantt_html(schedule_data):
    
    if not schedule_data:
        return "<h2>Gösterilecek plan bulunamadı. Lütfen geçerli bir takvim oluşturun.</h2>"

    df_list = []
    # gantt için rastgele bir date tarihi oluşturduk
    dummy_date = "2026-01-01 " 
    
    for item in schedule_data:
        # "08:00-09:30" formatını parçalayıp datetime objesine çeviriyoruz
        start_str, end_str = item['time'].split('-')
        start_time = datetime.strptime(dummy_date + start_str, "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(dummy_date + end_str, "%Y-%m-%d %H:%M")
        
        df_list.append({
            "Ameliyathane": item['room'],
            "Başlangıç": start_time,
            "Bitiş": end_time,
            "Operasyon": item['patient'],
            "Cerrah": item['surgeon'],
            "Ekip": item['team']
        })
        
    df = pd.DataFrame(df_list)
    
    # Plotly timeline (Gantt) grafiğini oluşturur
    fig = px.timeline(
        df, 
        x_start="Başlangıç", 
        x_end="Bitiş", 
        y="Ameliyathane", 
        color="Cerrah",
        hover_name="Operasyon",
        hover_data=["Ekip"],
        title="Günlük Ameliyathane Gantt Çizelgesi"
    )
    
    
    fig.update_yaxes(autorange="reversed") # OR-1'in en üstte görünmesi için
    fig.update_layout(
        xaxis=dict(
            tickformat='%H:%M', # alt eksende sadece saatleri göster
            title='Saat'
        ),
        font=dict(family="Arial", size=12)
    )
    
    # grafiği interaktif bir HTML yapısına dönüştürüp döndür
    return fig.to_html(full_html=False)

def generate_heatmap_html(schedule_data):
    if not schedule_data:
        return "<h2>Gösterilecek plan bulunamadı. Lütfen geçerli bir takvim oluşturun.</h2>"

    #  saat etiketlerini (X Ekseni) oluşturur (08:00, 08:30 ... 17:30)
    slots_labels = [slot_to_time(i) for i in range(20)]
    
    # takvimdeki benzersiz odaları bul ve alfabetik sırala (Y Ekseni)
    unique_rooms = list(set([item['room'] for item in schedule_data]))
    unique_rooms.sort()

    # odalar ve saatler için boş bir matris (0'lardan oluşan) matris yaratır
    matrix = {room: [0] * 20 for room in unique_rooms}
    
    hover_text = {room: ["Boş"] * 20 for room in unique_rooms}

    
    for item in schedule_data:
        room = item['room']
        start_str, end_str = item['time'].split('-')
        
        start_slot = time_to_slot(start_str)
        end_slot = time_to_slot(end_str)
        
        for t in range(start_slot, end_slot):
            matrix[room][t] = 1 # 1 = Dolu
            hover_text[room][t] = f"Dolu: {item['patient']}<br>Cerrah: {item['surgeon']}"

    
    z_data = [matrix[room] for room in unique_rooms]
    text_data = [hover_text[room] for room in unique_rooms]

    # plotly heatmap grafiğini oluşturur
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=slots_labels,
        y=unique_rooms,
        colorscale=[[0, 'rgb(46, 204, 113)'], [1, 'rgb(231, 76, 60)']], # 0: Yeşil, 1: Kırmızı
        showscale=False, 
        xgap=3,
        ygap=3,
        hoverinfo='text',
        text=text_data
    ))
    
    
    fig.update_layout(
        title="🌡️ Ameliyathane Kullanım Yoğunluğu (Heatmap)",
        xaxis_title="Mesai Saatleri",
        yaxis_title="Ameliyathaneler",
        font=dict(family="Arial", size=12),
        xaxis=dict(tickangle=-45) 
    )
    
    return fig.to_html(full_html=False)