from django.contrib import admin
from .models import VibrationLog, Prediction,  Earthquake

admin.site.register(VibrationLog)
admin.site.register(Prediction)
admin.site.register(Earthquake)