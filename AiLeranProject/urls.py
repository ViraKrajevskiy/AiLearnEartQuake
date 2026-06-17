from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VibrationAPIView, EarthquakeViewSet, index

router = DefaultRouter()
router.register(r'earthquakes', EarthquakeViewSet)

urlpatterns = [
    path('', index, name='index'),
    path('api/vibration/', VibrationAPIView.as_view()),
    path('api/', include(router.urls)),
]