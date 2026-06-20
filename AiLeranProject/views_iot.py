from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework import status
from datetime import datetime
import json
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response

from .models import IoTSensorData
from .ml_model import EarthquakePredictor

predictor = EarthquakePredictor()

@api_view(['GET'])
def iot_latest_data(request):
    # Берём последние записи, сортируем по времени датчика (новые сверху)
    latest = IoTSensorData.objects.order_by('-sensor_timestamp').first()
    is_online = False
    if latest:
        is_online = (timezone.now() - latest.sensor_timestamp) < timedelta(seconds=30)

    # Берём до 10 последних записей
    recent_sensors = IoTSensorData.objects.order_by('-sensor_timestamp')[:10]

    data = []
    for d in recent_sensors:
        # Определяем значение вибрации: предпочитаем vibration_intensity (баллы),
        # если оно не задано — используем vibration_count (старые записи)
        vib_value = d.vibration_intensity if d.vibration_intensity is not None else d.vibration_count
        data.append({
            'sensor_id': d.sensor_id,
            'vibration': vib_value,            # теперь это баллы 0-20
            'location': d.location_name,
            'timestamp': d.sensor_timestamp.isoformat(),
            'battery': d.battery_level,
        })

    return Response({
        "status": "online" if is_online else "offline",
        "sensors": data,
        "last_vibration": latest.vibration_intensity if latest and latest.vibration_intensity is not None else (latest.vibration_count if latest else 0),
        "location": latest.location_name if latest else "N/A"
    })

@csrf_exempt
@api_view(['POST'])
def iot_sensor_endpoint(request):
    """
    Endpoint для приема данных с ESP32 (только вибрация и статус)
    """
    try:
        data = request.data if isinstance(request.data, dict) else json.loads(request.body)

        # Парсинг timestamp (или текущее время сервера)
        try:
            sensor_timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        except:
            sensor_timestamp = timezone.now()

        # Создаём запись без температуры и влажности
        sensor_data = IoTSensorData.objects.create(
            sensor_id=data.get('sensor_id', 'ESP32-01'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            location_name=data.get('location_name'),
            vibration_count=int(data.get('vibration_count', 0)),
            vibration_intensity=data.get('vibration_intensity'),
            signal_strength=data.get('signal_strength'),
            battery_level=data.get('battery_level'),
            sensor_timestamp=sensor_timestamp,
        )

        response_data = {
            'status': 'success',
            'sensor_id': sensor_data.sensor_id,
            'vibration': sensor_data.vibration_count,
        }

        # Логика предсказания при высокой вибрации
        if sensor_data.vibration_count > 10 and sensor_data.latitude and sensor_data.longitude:
            try:
                features = EarthquakePredictor.compute_features(
                    sensor_data.latitude, sensor_data.longitude, 10.0
                )
                predicted_mag, confidence, lower_mag, upper_mag = predictor.predict(features)

                response_data['prediction'] = {
                    'magnitude': predicted_mag,
                    'confidence': confidence
                }
            except Exception as e:
                print(f"⚠️  Prediction error: {e}")

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
def iot_sensor_stats(request, sensor_id=None):
    """
    Статистика только по вибрации и заряду батареи
    """
    qs = IoTSensorData.objects.filter(sensor_id=sensor_id) if sensor_id else IoTSensorData.objects.all()

    if not qs.exists():
        return Response({'status': 'error', 'message': 'No data'}, status=404)

    vibs = [d.vibration_count for d in qs if d.vibration_count is not None]

    stats = {
        'count': qs.count(),
        'vibration': {
            'min': min(vibs) if vibs else 0,
            'max': max(vibs) if vibs else 0,
            'avg': sum(vibs) / len(vibs) if vibs else 0,
            'total_high_events': len([v for v in vibs if v > 10]),
        }
    }

    return Response(stats, status=status.HTTP_200_OK)