from .constants import SURGEON_DAYS_OFF, TOTAL_SLOTS

def is_valid(patient, room, surgeon, team, start_slot, resource_availability, current_day):
    duration = patient['duration']
    
    # uzmanlık oda uyumu ve izin günleri
    if current_day and SURGEON_DAYS_OFF.get(surgeon['id']) == current_day:
        return False
    if patient['required_specialty'] != surgeon['specialty']:
        return False
    
    supported_ops = room.get('supported_operations', [])
    if supported_ops and patient['operation'] not in supported_ops:
        return False
    
    # mesai saati kontrolü
    if start_slot + duration > TOTAL_SLOTS:
        return False
        
    # kaynak çakışma kontrolü
    for t in range(start_slot, start_slot + duration):
        if not (resource_availability["rooms"][room['id']][t] and
                resource_availability["surgeons"][surgeon['id']][t] and
                resource_availability["teams"][team][t]):
            return False

    # cerrah dinlenme kuralı
    busy_before = sum(1 for t in range(start_slot - 1, -1, -1) if not resource_availability["surgeons"][surgeon['id']][t])
    busy_after = sum(1 for t in range(start_slot + duration, TOTAL_SLOTS) if not resource_availability["surgeons"][surgeon['id']][t])
    
    if duration >= 4:
        return not (busy_before > 0 or busy_after > 0)
    return (busy_before + duration + busy_after) <= 4