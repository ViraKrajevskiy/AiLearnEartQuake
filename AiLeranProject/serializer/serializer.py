from rest_framework import serializers
from AiLeranProject.models import Earthquake, Prediction
from rest_framework import serializers


class EarthquakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Earthquake
        fields = '__all__'

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = '__all__'