from rest_framework import serializers

from AiLeranProject.models import Earthquake, Prediction, IoTSensorData


class EarthquakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Earthquake
        fields = '__all__'


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = '__all__'


# ✅ НОВЫЙ СЕРИАЛИЗАТОР
class IoTSensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = IoTSensorData
        fields = [
            'id',
            'sensor_id',
            'latitude',
            'longitude',
            'location_name',
            'temperature',
            'humidity',
            'vibration_count',
            'vibration_intensity',
            'signal_strength',
            'battery_level',
            'sensor_timestamp',
            'received_at',
        ]
        read_only_fields = ['id', 'received_at']