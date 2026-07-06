def generate_schedule(data):
    patients = data['patients']
    surgeons = data['surgeons']
    rooms = data['rooms']
    teams = data['teams']
    
    priority_weights = {"Kritik":4, "Yüksek":3, "Orta":2, "Düşük":1}
    
    patients.sort(key=lambda x: (priority_weights.get(x['priority'], 0), x['duration']), reverse=True)  # hastalar öncelik ağırlığına göre büyükten küçüğe zamana göre uzundan kısaya sıralanır
    
    schedule = [] 
    
    TOTAL_SLOTS = 20 # 08-18 arası 10 saat için 30 dk'dan toplamda 20 tane slot
    
    
    # resource allocation in-memory veritabanımız
    # True = Müsait , False = Ameliyatta
    # her odanın, cerrahın ve takımın 20 slotluk (10 saatlik) günlüğü 
    
    resource_availability = {
        "rooms": {r['id'] :[True] * TOTAL_SLOTS for r in rooms},
        "surgeons": {s['id']: [True] * TOTAL_SLOTS for s in surgeons},
        "teams": {t['id']: [True] * TOTAL_SLOTS for t in teams}    
    }
    
    
    
