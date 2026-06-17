import os
import sys
import django
from datetime import datetime, timedelta
import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
django.setup()

from AiLeranProject.models import Earthquake
from AiLeranProject.ml_model import EarthquakePredictor


def fetch_earthquakes():
    """Загружает землетрясения с USGS за последние 30 дней"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    params = {
        'format': 'geojson',
        'starttime': start_date.isoformat(),
        'endtime': end_date.isoformat(),
        'minmagnitude': 2.5
    }

    print("📡 Fetching earthquake data from USGS...")

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            count = 0

            for feature in data['features']:
                props = feature['properties']
                coords = feature['geometry']['coordinates']

                earthquake, created = Earthquake.objects.get_or_create(
                    timestamp=datetime.fromtimestamp(props['time'] / 1000),
                    latitude=coords[1],
                    longitude=coords[0],
                    magnitude=props['mag'],
                    defaults={
                        'depth': coords[2] if len(coords) > 2 else None,
                        'location': props.get('place', 'Unknown')
                    }
                )

                if created:
                    count += 1
                    print(f"✓ {earthquake.location} - M{earthquake.magnitude}")

            print(f"\n✓ Loaded {count} new earthquakes!")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def train_model():
    """Обучает модель на данных из БД, используя compute_features()"""

    earthquakes = list(Earthquake.objects.all().order_by('timestamp'))

    if len(earthquakes) < 10:
        print(f"⚠️  Need at least 10 earthquakes (have {len(earthquakes)})")
        return False

    print(f"\n🤖 Preparing {len(earthquakes)} samples...")

    X = []
    y = []

    # Для каждого землетрясения вычисляем признаки используя compute_features()
    for eq in earthquakes:
        try:
            features = EarthquakePredictor.compute_features(
                eq.latitude,
                eq.longitude,
                eq.depth or 10.0  # Default depth если не указана
            )
            X.append(features)
            y.append(eq.magnitude)
        except Exception as e:
            print(f"⚠️  Skip {eq.location}: {e}")
            continue

    if len(X) < 10:
        print(f"✗ Not enough valid samples after processing ({len(X)})")
        return False

    X = np.array(X)
    y = np.array(y)

    print(f"✓ Prepared {len(X)} samples")
    print(f"  Feature shape: {X.shape}")
    print(f"  Magnitude range: {y.min():.1f} - {y.max():.1f}")

    # Обучаем модель
    predictor = EarthquakePredictor()
    success = predictor.train(X, y)

    return success


if __name__ == '__main__':
    print("=== Earthquake AI Training System ===\n")

    # Опционально: загрузить свежие данные с USGS
    # fetch_earthquakes()

    # Обучить модель
    if train_model():
        print("\n✓ Training complete!")
    else:
        print("\n✗ Training failed!")