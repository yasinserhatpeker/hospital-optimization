from .constraints import is_valid
from .constants import TOTAL_SLOTS

def generate_schedule(data):
   
    patients = sorted(data['patients'], key=lambda x: ({"Kritik": 4, "Yüksek": 3, "Orta": 2, "Düşük": 1}.get(x['priority'], 0), x['duration']), reverse=True)
    surgeons, rooms, teams = data['surgeons'], data['rooms'], data['teams']
    current_day = data.get('day', '')
    
    resource_availability = {
        "rooms": {r['id']: [True] * TOTAL_SLOTS for r in rooms},
        "surgeons": {s['id']: [True] * TOTAL_SLOTS for s in surgeons},
        "teams": {t: [True] * TOTAL_SLOTS for t in teams}
    }
    
    valid_solutions = []
    current_schedule = []

    def backtrack(patient_index):
        if len(valid_solutions) >= 20: return
        if patient_index == len(patients):
            valid_solutions.append(list(current_schedule))
            return
            
        p = patients[patient_index]
        for start in range(TOTAL_SLOTS - p['duration'] + 1):
            for r in rooms:
                for s in surgeons:
                    for tm in teams:
                        if is_valid(p, r, s, tm, start, resource_availability, current_day):
                            # resource'ları güncelliyoruz false -> dolu
                            for t in range(start, start + p['duration']):
                                resource_availability["rooms"][r['id']][t] = resource_availability["surgeons"][s['id']][t] = resource_availability["teams"][tm][t] = False
                            
                            current_schedule.append({"patient": p['id'], "operation": p['operation'], "room": r['id'], "surgeon": s['id'], "team": tm, "start_slot": start, "duration": p['duration']})
                            backtrack(patient_index + 1)
                            
                            # backtracking ile eğer optimal çözüm bulamazsa true ile tekrar resource'ları boşaltıyoruz
                            current_schedule.pop()
                            for t in range(start, start + p['duration']):
                                resource_availability["rooms"][r['id']][t] = resource_availability["surgeons"][s['id']][t] = resource_availability["teams"][tm][t] = True
    
    backtrack(0)
    
    return valid_solutions[0] if valid_solutions else None