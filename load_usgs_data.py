import os
import sys
import django
from datetime import datetime, timedelta
import requests
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
django.setup()

from AiLeranProject.models import Earthquake
from AiLeranProject.ml_model import EarthquakePredictor


def fetch_earthquakes():
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
    """Обучает модель на данных"""

    earthquakes = Earthquake.objects.all().order_by('timestamp')

    if len(earthquakes) < 20:
        print(f"⚠️  Need at least 20 earthquakes (have {len(earthquakes)})")
        return

    print(f"\n🤖 Training model on {len(earthquakes)} earthquakes...")

    X = []
    y = []

    for eq in earthquakes:
        X.append([
            eq.vibration_count or 0,
            eq.latitude,
            eq.longitude
        ])
        y.append(eq.magnitude)

    X = np.array(X)
    y = np.array(y)

    predictor = EarthquakePredictor()
    predictor.train(X, y)

    print("✓ Model trained and saved!")


if __name__ == '__main__':
    print("=== Earthquake AI Training System ===\n")

    if fetch_earthquakes():
        train_model()

    print("\n✓ Done!")