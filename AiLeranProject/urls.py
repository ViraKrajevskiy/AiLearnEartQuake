from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, views_iot
from .views_iot import iot_sensor_endpoint, iot_sensor_stats, iot_latest_data

router = DefaultRouter()
router.register(r'earthquakes', views.EarthquakeViewSet)

urlpatterns = [

    path('about/', views.about_page, name='about'),
    path('api/iot/latest/', views_iot.iot_latest_data, name='iot_latest'),

    # Основные страницы
    path('', views.index, name='index'),
    path('statistics/', views.stats_page, name='statistics'),

    # IoT Endpoints ✅ НОВЫЕ
    path('api/iot/sensor/', iot_sensor_endpoint, name='iot_sensor'),
    path('api/iot/latest/', iot_latest_data, name='iot_latest'),
    path('api/iot/stats/', iot_sensor_stats, name='iot_stats'),
    path('api/iot/stats/<str:sensor_id>/', iot_sensor_stats, name='iot_stats_sensor'),

    # Существующие endpoints
    path('api/vibration/', views.VibrationAPIView.as_view()),
    path('api/', include(router.urls)),
]