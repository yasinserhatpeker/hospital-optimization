
## KULLANILAN YAPI HEURISTIC + BACKTRACKING ALGORİTMASI

def generate_schedule(data):
    patients = data['patients']
    surgeons = data['surgeons']
    rooms = data['rooms']
    teams = data['teams']
    # Heuristic bir ağırlık ortalaması kullanılır
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
        
        # Constraint 4 ameliyat süresi boyunca kaynaklar boş mu diye bakıyoruz
        for t in range(start_slot, start_slot + duration):
            if not (resource_availability["rooms"][room['id']][t] and
                    resource_availability["surgeons"][surgeon['id']][t] and
                    resource_availability["teams"][team][t]):
                return False # slotlardan biri bile doluysa false dön
            
      # Constraint 5    
      # 1. Geriye doğru say: Atama yapılmak istenen slottan önce doktor ne kadar süredir ameliyatta?
        busy_before = 0
        t_before = start_slot - 1
        while t_before >= 0 and not resource_availability["surgeons"][surgeon['id']][t_before]:
            busy_before += 1
            t_before -= 1

        # 2. İleriye doğru say  Atama yapılacak ameliyat bittikten hemen sonra doktorun başka ameliyatı var mı
        busy_after = 0
        t_after = start_slot + duration
        while t_after < TOTAL_SLOTS and not resource_availability["surgeons"][surgeon['id']][t_after]:
            busy_after += 1
            t_after += 1

        # 3. Toplam kesintisiz çalışma süresini kontrol et
        # Eğer geçmişteki ameliyatlar + şu anki ameliyat + gelecekteki ameliyatlar 4 slotu aşıyorsa reddet
        if busy_before + duration + busy_after > 4:
            return False
            
        
        return True # Tüm constraintlerden geçtiyse true dön
            
        
    # BACKTRACKING Algoritması   
    def back_tracking(patient_index):
        
        #Base case tüm hastalar başarıyla yerleştiyse
        if patient_index == len(patients):
            return True
        
        
        patient = patients[patient_index]
        duration = patients['duration']
        
        
         
    
