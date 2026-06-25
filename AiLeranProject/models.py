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

