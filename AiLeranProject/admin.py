from django.contrib import admin
from .models import VibrationLog, Prediction, IoTSensorData, Earthquake

admin.site.register(VibrationLog)
admin.site.register(Prediction)
admin.site.register(IoTSensorData)
admin.site.register(Earthquake)