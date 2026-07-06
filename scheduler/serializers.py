from rest_framework import serializers

class PatientSerializer(serializers.Serializer):
    id = serializers.CharField()
    operation = serializers.CharField()
    duration = serializers.IntegerField() ## 30 dk'lık slot şeklinde
    priority = serializers.CharField() # Kritik - Yüksek - Orta - Düşük
    required_specialty = serializers.CharField() # Genel Cerrahi - Ortopedi vs.
    

class SurgeonSerializer(serializers.Serializer):
    