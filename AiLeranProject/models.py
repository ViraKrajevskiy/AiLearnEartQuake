from django.db import models
from django.utils import timezone


class VibrationLog(models.Model):
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vibration: {self.score} at {self.created_at}"


class Earthquake(models.Model):
    timestamp = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    magnitude = models.FloatField()
    depth = models.FloatField(null=True, blank=True)
    location = models.CharField(max_length=255)

    vibration_count = models.IntegerField(null=True, blank=True)
    predicted_magnitude = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.location} - {self.magnitude}"


class Prediction(models.Model):
    vibration_count = models.IntegerField()
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    predicted_magnitude = models.FloatField()
    confidence = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pred: {self.predicted_magnitude} (confidence: {self.confidence})"


# НОВАЯ МОДЕЛЬ ДЛЯ IOT ДАТЧИКОВ (ОБНОВЛЕННАЯ)
class IoTSensorData(models.Model):
    sensor_id = models.CharField(max_length=50, default="ESP32-01")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    depth = models.FloatField(default=10.0, null=True, blank=True)  # ✅ ДОБАВЛЕНО

    vibration_intensity = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, null=True, blank=True)

    vibration_count = models.IntegerField(default=0)
    signal_strength = models.IntegerField(null=True, blank=True)
    battery_level = models.IntegerField(null=True, blank=True)

    # НОВЫЕ ПОЛЯ ДЛЯ GEO-INFORMATION
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)  # ISO 3166-1 alpha-2

    sensor_timestamp = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sensor_timestamp']
        indexes = [models.Index(fields=['-sensor_timestamp'])]

    def __str__(self):
        return f"{self.sensor_id} - {self.country or 'Unknown'} ({self.vibration_intensity})"