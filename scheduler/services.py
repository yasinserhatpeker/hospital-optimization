

def generate_schedule(data):
    patients = data['patients']
    surgeons = data['surgeons']
    rooms = data['rooms']
    teams = data['teams']
    
    priority_weights = {"Kritik":4, "Yüksek":3, "Orta":2, "Düşük":1}
    
    patients.sort(key=lambda x: (priority_weights.get(x['priority'], 0), x['duration']), reverse=True)  # hastalar öncelik ağırlığına göre büyükten küçüğe zamana göre uzundan kısaya sıralanır
    
    schedule = [] # şimdilik boş veri dönüyoruz temel rest api tasarımı bittikten sonra hard-constraint'ler yazılacak
    
    return schedule