from .constraints import is_valid
from .utils import slot_to_time
from .constants import TOTAL_SLOTS

def generate_schedule(data):
    # Heuristic ile önem ve zaman derecelerine göre sıralanır
    patients = sorted(data['patients'], key=lambda x: (
        {"Kritik": 4, "Yüksek": 3, "Orta": 2, "Düşük": 1}.get(x.get('priority', 'Düşük'), 0), 
        x['duration']
    ), reverse=True)
    
    surgeons, rooms, teams = data['surgeons'], data['rooms'], data['teams']
    current_day = data.get('day', '')
    locked_schedules = data.get('locked_schedules', [])
    
    # resourceler için hepsi müsait(true) olacak şekilde
    resource_availability = {
        "rooms": {r['id']: [True] * TOTAL_SLOTS for r in rooms},
        "surgeons": {s['id']: [True] * TOTAL_SLOTS for s in surgeons},
        "teams": {t: [True] * TOTAL_SLOTS for t in teams}
    }
    
    # dinamik re-planlama için locked_schedules mantığını kullanıyoruz
    for locked in locked_schedules:
        
        start, duration = locked['start_slot'], locked['duration']
        r_id = locked['room']
        s_id = locked['surgeon']
        tm = locked['team']
        
        for t in range(start, start + duration):
            if r_id in resource_availability["rooms"]:
                resource_availability["rooms"][r_id][t] = False
            if s_id in resource_availability["surgeons"]:
                resource_availability["surgeons"][s_id][t] = False
            if tm in resource_availability["teams"]:
                resource_availability["teams"][tm][t] = False
            
    # sadece kilitli olmayan hastaları planla
    locked_patient_ids = [ls['patient'] for ls in locked_schedules]
    pending_patients = [p for p in patients if p['id'] not in locked_patient_ids]
    
    valid_solutions = []
    current_schedule = list(locked_schedules) # mevcut planı koru

    def backtrack(patient_index):
        if len(valid_solutions) >= 1: return # ilk uygun çözümü bul ve dur
        if patient_index == len(pending_patients):
            valid_solutions.append(list(current_schedule))
            return
            
        p = pending_patients[patient_index]
        for start in range(TOTAL_SLOTS - p['duration'] + 1):
            for r in rooms:
                for s in surgeons:
                    for tm in teams:
                        if is_valid(p, r, s, tm, start, resource_availability, current_day):
                            # resource'leri kapa (false)
                            for t in range(start, start + p['duration']):
                                resource_availability["rooms"][r['id']][t] = False
                                resource_availability["surgeons"][s['id']][t] = False
                                resource_availability["teams"][tm][t] = False
                            
                            current_schedule.append({
                                "patient": p['id'], "operation": p['operation'], 
                                "room": r['id'], "surgeon": s['id'], 
                                "team": tm, "start_slot": start, "duration": p['duration']
                            })
                            
                            backtrack(patient_index + 1)
                            
                            # eğer uygun çözüm bulunmazsa backtracking ile tekrar geri dön
                            current_schedule.pop()
                            for t in range(start, start + p['duration']):
                                resource_availability["rooms"][r['id']][t] = True
                                resource_availability["surgeons"][s['id']][t] = True
                                resource_availability["teams"][tm][t] = True
    
    backtrack(0)
    
    # çözüm bulunduysa veriyi istediğin formata dönüştür
    if valid_solutions:
        raw_schedule = valid_solutions[0]
        formatted_schedule = []
        
        for item in raw_schedule:
            # zamanı hesapla
            start_str = slot_to_time(item['start_slot'])
            end_str = slot_to_time(item['start_slot'] + item['duration'])
            
            formatted_schedule.append({
                "time": f"{start_str}-{end_str}",
                "room": item['room'],
                "patient": f"{item['patient']} - {item['operation']}",
                "surgeon": item['surgeon'],
                "team": item['team']
            })
        return formatted_schedule
        
    return None
    