from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

from .models import Earthquake, Prediction
from .serializer.serializer import EarthquakeSerializer
from AiLeranProject.ml_model import EarthquakePredictor

from django.shortcuts import render

logger = logging.getLogger(__name__)
predictor = EarthquakePredictor()


class EarthquakeViewSet(viewsets.ModelViewSet):
    queryset = Earthquake.objects.all()
    serializer_class = EarthquakeSerializer


@method_decorator(csrf_exempt, name='dispatch')
class VibrationAPIView(APIView):
    """
    POST /api/vibration/
    Endpoint for predicting earthquake magnitude
    """

    def post(self, request):
        try:
            latitude = float(request.data.get('latitude'))
            longitude = float(request.data.get('longitude'))

            # Handle depth
            try:
                depth = float(request.data.get('depth', 10.0))
            except (ValueError, TypeError):
                depth = 10.0

            # Validate coordinates
            if latitude < -90 or latitude > 90:
                return Response(
                    {'error': 'Latitude must be between -90 and 90'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if longitude < -180 or longitude > 180:
                return Response(
                    {'error': 'Longitude must be between -180 and 180'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate depth
            if depth < 0 or depth > 700:
                return Response(
                    {'error': 'Depth must be between 0 and 700 km'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Compute features with correct depth
            features = EarthquakePredictor.compute_features(latitude, longitude, depth)

            # Predict
            predicted_magnitude, confidence, lower_mag, upper_mag = predictor.predict(features)

            # Location uncertainty (in degrees)
            location_uncertainty = 0.2

            # Save prediction to database
            prediction = Prediction.objects.create(
                vibration_count=features[0],  # nearby_quakes_count
                latitude=latitude,
                longitude=longitude,
                predicted_magnitude=predicted_magnitude,
                confidence=confidence
            )

            return Response({
                'predicted_magnitude': predicted_magnitude,
                'confidence': confidence,
                'lower_magnitude': lower_mag,
                'upper_magnitude': upper_mag,
                'location_uncertainty': location_uncertainty,
                'nearby_quakes_count': features[0],
                'depth': depth,
                'time_since_last_big': features[2],
                'is_model_trained': predictor.is_trained
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': f'Invalid input: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return Response(
                {'error': f'Prediction error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def stats_page(request):
    return render(request, 'statistics.html')


def index(request):
    return render(request, 'index.html')


def about_page(request):
    return render(request, 'about.html')