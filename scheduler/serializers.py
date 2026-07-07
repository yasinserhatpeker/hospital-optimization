from rest_framework import serializers

class PatientSerializer(serializers.Serializer):
    id = serializers.CharField()
    operation = serializers.CharField()
    duration = serializers.IntegerField() ## 30 dk'lık slot şeklinde
    priority = serializers.CharField() # Kritik - Yüksek - Orta - Düşük
    required_specialty = serializers.CharField() # Genel Cerrahi - Ortopedi vs.
    

class SurgeonSerializer(serializers.Serializer):
    id = serializers.CharField()
    specialty = serializers.CharField() # Profesyonel alanı
    day_off = serializers.CharField(required = False, allow_blank = True, allow_null=True) ## İzinli Gün
    
class RoomSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    supported_operations = serializers.ListField(child=serializers.CharField(),required=False) ## Genel Cerrahi - Kardiyoloji vs.
    
    
class LockedScheduleSerializer(serializers.Serializer):
    patient = serializers.CharField()
    operation = serializers.CharField(required=False, allow_blank=True, default="continious operation")
    room = serializers.CharField()
    surgeon = serializers.CharField()
    team = serializers.CharField()
    start_slot = serializers.IntegerField()
    duration = serializers.IntegerField()
    

class OperationPlanRequestSerializer(serializers.Serializer):
    
    patients = PatientSerializer(many=True)
    surgeons = SurgeonSerializer(many=True)
    rooms = RoomSerializer(many=True)
    teams = serializers.ListField(child=serializers.CharField()) # Team A Team B şeklinde vs.
    day = serializers.CharField(required=False, allow_null = True, allow_blank = True) # Doktor izinli mi değil mi öğrenmek için
    locked_schedules = LockedScheduleSerializer(many=True, required=False)

    
    