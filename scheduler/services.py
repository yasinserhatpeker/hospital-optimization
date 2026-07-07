import pandas as pd
import plotly.express as px
from datetime import datetime

def slot_to_time(slot): ## 0-19 arası slot'u gerçek zamana çevirir
    hours = 8 + (slot // 2)
    mins = "30" if slot % 2 != 0 else "00"
    return f"{hours:02d}:{mins}"

def calculate_penalty(schedule, patients_data): # Soft constraintleri hesaplar düşük penalty skoru sağlamak amaç
    penalty = 0
    
    # Hastaların öncelik verisine hızlı erişim için bir dictionary
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

        # Soft Constraint 1 Kritik hastaların bekleme süresi cezası
        # Kritik hasta ne kadar geç başlarsa o kadar yüksek ceza alır.
        if priority_map[assignment['patient']] == "Kritik":
            penalty += start * 10 

    # Soft Constraint 2 Cerrah idle kalma süresi ve parçalı plan
    for surgeon, times in surgeon_schedules.items():
        min_start = min([t[0] for t in times])
        max_end = max([t[1] for t in times])
        total_active = sum([t[1] - t[0] for t in times])
        
        idle_time = (max_end - min_start) - total_active
        penalty += idle_time * 5  # Her 30 dk boşluk için 5 ceza puanı

    # Soft Constraint 3 Ameliyathane idle kalma süresi
    for room, times in room_schedules.items():
        min_start = min([t[0] for t in times])
        max_end = max([t[1] for t in times])
        total_active = sum([t[1] - t[0] for t in times])
        
        room_idle = (max_end - min_start) - total_active
        penalty += room_idle * 3  # Her 30 dk boşluk için 3 ceza puanı

    # Soft Constraint 4 Anestezi ekiplerinin dengesiz kullanımı
    if team_usage:
        max_ops = max(team_usage.values())
        min_ops = min(team_usage.values())
        imbalance = max_ops - min_ops
        penalty += imbalance * 15  # Ekipler arası her 1 ameliyat farkı için 15 ceza puanı

    return penalty


def generate_schedule(data):
    patients = data['patients']
    surgeons = data['surgeons']
    rooms = data['rooms']
    teams = data['teams']

    # JSON isteğinden gelen işlem gününü al
    current_day = data.get('day', '')

    # PDF'te belirtilen doktor izin günleri tablosu
    SURGEON_DAYS_OFF = {
        "Dr. Ahmet": "Çarşamba",
        "Dr. Ayşe": "Pazartesi",
        "Dr. Mehmet": "Salı",
        "Dr. Elif": "Perşembe",
        "Dr. Can": "Cuma"
    }

    # 1. HEURISTIC Hastaları önceliğe göre sıralama
    priority_weights = {"Kritik": 4, "Yüksek": 3, "Orta": 2, "Düşük": 1}
    patients.sort(key=lambda x: (priority_weights.get(x['priority'], 0), x['duration']), reverse=True)

    TOTAL_SLOTS = 20
    
    resource_availability = {
        "rooms": {r['id']: [True] * TOTAL_SLOTS for r in rooms},
        "surgeons": {s['id']: [True] * TOTAL_SLOTS for s in surgeons},
        "teams": {t: [True] * TOTAL_SLOTS for t in teams}
    }
    
    current_schedule = []
    valid_solutions = []
    MAX_SOLUTIONS = 20 # Performans için algoritmayı 20 geçerli çözümle sınırlıyoruz

    # Hard constraints fonksiyonu
    def is_valid(patient, room, surgeon, team, start_slot):
        duration = patient['duration']
        
        # Doktor İzin Günü Kontrolü
        # Eğer planlanan gün, cerrahın izin günüyle eşleşiyorsa atamayı reddeder
        if current_day and SURGEON_DAYS_OFF.get(surgeon['id']) == current_day:
            return False
            
        if start_slot + duration > TOTAL_SLOTS:
            return False
            
        if patient['required_specialty'] != surgeon['specialty']:
            return False
            
        supported_ops = room.get('supported_operations', [])
        if supported_ops and patient['operation'] not in supported_ops:
            return False

        for t in range(start_slot, start_slot + duration):
            if not (resource_availability["rooms"][room['id']][t] and
                    resource_availability["surgeons"][surgeon['id']][t] and
                    resource_availability["teams"][team][t]):
                return False

        # Cerrah Dinlenme Constrainti
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

    # Backtracking algoritma fonksiyonu
    def backtrack(patient_index):
        # Yeterli sayıda çözüm bulduysak aramayı durdur
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
                        
                        if is_valid(patient, room, surgeon, team, start_slot):
                            # Yerleştir
                            for t in range(start_slot, start_slot + duration):
                                resource_availability["rooms"][room['id']][t] = False
                                resource_availability["surgeons"][surgeon['id']][t] = False
                                resource_availability["teams"][team][t] = False
                            
                            current_assignment = {
                                "patient": patient['id'],
                                "operation": patient['operation'],
                                "room": room['id'],
                                "surgeon": surgeon['id'],
                                "team": team,
                                "start_slot": start_slot,
                                "duration": duration
                            }
                            current_schedule.append(current_assignment)
                            
                            # İleri Git recursive şeklinde
                            backtrack(patient_index + 1)
                                
                            # Geri Al
                            current_schedule.pop()
                            for t in range(start_slot, start_slot + duration):
                                resource_availability["rooms"][room['id']][t] = True
                                resource_availability["surgeons"][surgeon['id']][t] = True
                                resource_availability["teams"][team][t] = True

    # Algoritma başlar
    backtrack(0)
    
    # Çözüm bulunamadıysa boş dön
    if not valid_solutions:
        return []

    # Soft Constraint değerlendirmesi
    # Bulunan tüm geçerli planları ceza puanlarına göre hesapla
    best_schedule = None
    min_penalty = float('inf')

    for sol in valid_solutions:
        penalty = calculate_penalty(sol, patients)
        if penalty < min_penalty:
            min_penalty = penalty
            best_schedule = sol

    # API çıktısını formatlama
    # Seçilen en iyi planın zaman aralıklarını okunabilir saatlere çevir
    formatted_schedule = []
    for item in best_schedule:
        start_time = slot_to_time(item['start_slot'])
        end_time = slot_to_time(item['start_slot'] + item['duration'])
        
        formatted_schedule.append({
            "time": f"{start_time}-{end_time}",
            "room": item['room'],
            "patient": f"{item['patient']} - {item['operation']}",
            "surgeon": item['surgeon'],
            "team": item['team']
        })

    # Planı zaman çizelgesine göre (saat sırasına) dizerek döndür
    return sorted(formatted_schedule, key=lambda x: x['time'])


def generate_gantt_html(schedule_data):
    
    if not schedule_data:
        return "<h2>Gösterilecek plan bulunamadı. Lütfen geçerli bir takvim oluşturun.</h2>"

    df_list = []
    
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
    
    # Plotly Timeline (Gantt) Grafiğini Oluşturur
    fig = px.timeline(
        df, 
        x_start="Başlangıç", 
        x_end="Bitiş", 
        y="Ameliyathane", 
        color="Cerrah",
        hover_name="Operasyon",
        hover_data=["Ekip"],
        title="🏥 Günlük Ameliyathane Gantt Çizelgesi"
    )
    
    
    fig.update_yaxes(autorange="reversed") # OR-1'in en üstte görünmesi için
    fig.update_layout(
        xaxis=dict(
            tickformat='%H:%M', # Alt eksende sadece saatleri göster
            title='Saat'
        ),
        font=dict(family="Arial", size=12)
    )
    
    # Grafiği interaktif bir HTML yapısına dönüştürüp döndür
    return fig.to_html(full_html=False)