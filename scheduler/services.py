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
    
    
    def is_valid(patient,room,surgeon,team, start_slot):
        duration = patient['duration']
        
        # Constraint 1 18.00'dan sonra ameliyat planlanamaz
        if start_slot + duration > TOTAL_SLOTS:
            return False
        
        # Constraint 2 hastaya uyumlu uzmanlığa sahip surgeon ameliyat yapabilir yoksa false dön 
        if patient['required_specialty'] != surgeon['specialty']:
            return False
        
        # Constraint 3 eğer doğru ameliyathane hasta eşleşmesi yoksa false dön
        supported_ops = room.get('supported_operations', [])
        if supported_ops and patient['operation'] not in supported_ops:
            return False
        
        
    
