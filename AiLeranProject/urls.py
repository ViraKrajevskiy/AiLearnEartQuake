from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_iot

router = DefaultRouter()
router.register(r'earthquakes', views.EarthquakeViewSet)

urlpatterns = [
    # 📄 Pages
    path('about/', views.about_page, name='about'),
    path('', views.index, name='index'),
    path('statistics/', views.stats_page, name='statistics'),

    # 🚨 IoT Alerts (SSE)
    path('api/iot/alerts/', views_iot.iot_alerts_stream, name='iot_alerts'),

    # 📡 IoT Data Endpoints
    path('api/iot/sensor/', views_iot.iot_sensor_endpoint, name='iot_sensor'),
    path('api/iot/latest/', views_iot.iot_latest_data, name='iot_latest'),
    path('api/iot/stats/', views_iot.iot_sensor_stats, name='iot_stats'),
    path('api/iot/stats/<str:sensor_id>/', views_iot.iot_sensor_stats, name='iot_stats_sensor'),

    # 🌍 Earthquake Prediction API
    path('api/vibration/', views.VibrationAPIView.as_view(), name='vibration'),
    path('api/', include(router.urls)),
]