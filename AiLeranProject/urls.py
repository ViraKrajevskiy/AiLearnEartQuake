from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'earthquakes', views.EarthquakeViewSet)

urlpatterns = [
    # 📄 Pages
    path('about/', views.about_page, name='about'),
    path('', views.index, name='index'),
    path('statistics/', views.stats_page, name='statistics'),

    # 🌍 Earthquake Prediction API
    path('api/vibration/', views.VibrationAPIView.as_view(), name='vibration'),
    path('api/', include(router.urls)),
]