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
    """Loads earthquakes from USGS for the last 30 days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    params = {
        'format': 'geojson',
        'starttime': start_date.isoformat(),
        'endtime': end_date.isoformat(),
        'minmagnitude': 2.5,
        'orderby': 'time',
    }

    print("📡 Fetching earthquake data from USGS...")

    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            count = 0

            for feature in data['features']:
                props = feature['properties']
                coords = feature['geometry']['coordinates']

                timestamp = datetime.fromtimestamp(props['time'] / 1000)
                latitude = coords[1]
                longitude = coords[0]
                depth = coords[2] if len(coords) > 2 else None
                magnitude = props.get('mag')
                location = props.get('place', 'Unknown')

                if magnitude is None or magnitude < 2.5:
                    continue

                earthquake, created = Earthquake.objects.get_or_create(
                    timestamp=timestamp,
                    latitude=latitude,
                    longitude=longitude,
                    defaults={
                        'magnitude': magnitude,
                        'depth': depth,
                        'location': location,
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
    """Trains the model using data from the database with compute_features()"""
    earthquakes = list(Earthquake.objects.all().order_by('timestamp'))

    if len(earthquakes) < 10:
        print(f"⚠️  Need at least 10 earthquakes (have {len(earthquakes)})")
        return False

    print(f"\n🤖 Preparing {len(earthquakes)} samples...")

    X = []
    y = []
    skipped = 0

    # For each earthquake, compute features using compute_features()
    for eq in earthquakes:
        try:
            features = EarthquakePredictor.compute_features(
                eq.latitude,
                eq.longitude,
                eq.depth or 10.0
            )
            X.append(features)
            y.append(eq.magnitude)
        except Exception as e:
            print(f"⚠️  Skip {eq.location}: {e}")
            skipped += 1
            continue

    if len(X) < 10:
        print(f"✗ Not enough valid samples after processing ({len(X)})")
        return False

    X = np.array(X)
    y = np.array(y)

    print(f"✓ Prepared {len(X)} samples (skipped {skipped})")
    print(f"  Feature shape: {X.shape}")
    print(f"  Feature ranges:")
    print(f"    nearby_quakes: {X[:, 0].min():.0f} - {X[:, 0].max():.0f}")
    print(f"    depth: {X[:, 1].min():.1f} - {X[:, 1].max():.1f} km")
    print(f"    time_since_last_big: {X[:, 2].min():.2f} - {X[:, 2].max():.2f} years")
    print(f"    latitude: {X[:, 3].min():.2f} - {X[:, 3].max():.2f}°")
    print(f"    longitude: {X[:, 4].min():.2f} - {X[:, 4].max():.2f}°")
    print(f"  Magnitude range: {y.min():.1f} - {y.max():.1f}")

    # Train the model
    predictor = EarthquakePredictor()
    success = predictor.train(X, y)

    return success


def get_model_stats():
    """Prints statistics about the current model"""
    predictor = EarthquakePredictor()
    print(f"\n📊 Model Statistics:")
    print(f"  Trained: {predictor.is_trained}")
    print(f"  RMSE: {predictor.rmse:.3f}")
    print(f"  Model file: {predictor.model_path}")
    print(f"  Scaler file: {predictor.scaler_path}")

    if predictor.is_trained:
        print(f"  Estimators: {len(predictor.model.estimators_)}")
        print(f"  Feature importance:")
        feature_names = ['nearby_quakes', 'depth', 'time_since_last_big', 'latitude', 'longitude']
        for name, imp in zip(feature_names, predictor.model.feature_importances_):
            print(f"    {name}: {imp:.3f}")


if __name__ == '__main__':
    print("=== Earthquake AI Training System ===\n")

    # Optional: fetch fresh data from USGS
    if len(sys.argv) > 1 and sys.argv[1] == '--fetch':
        fetch_earthquakes()

    # Train the model
    if train_model():
        print("\n✓ Training complete!")
        get_model_stats()
    else:
        print("\n✗ Training failed!")