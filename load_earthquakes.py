import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
django.setup()

from AiLeranProject.models import Earthquake


def load_earthquakes_from_usgs():
    """Загружает последние землетрясения с USGS"""


    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    params = {
        'format': 'geojson',
        'starttime': start_date.isoformat(),
        'endtime': end_date.isoformat(),
        'minmagnitude': 2.5
    }

    print(f"Fetching earthquakes from {start_date} to {end_date}...")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']

            earthquake = Earthquake(
                timestamp=datetime.fromtimestamp(props['time'] / 1000),
                latitude=coords[1],
                longitude=coords[0],
                magnitude=props['mag'],
                depth=coords[2],
                location=props.get('place', 'Unknown')
            )

            try:
                earthquake.save()
                print(f"✓ {earthquake.location} - Magnitude: {earthquake.magnitude}")
            except:
                pass  # Duplicate

        print(f"\n✓ Loaded {len(data['features'])} earthquakes!")
    else:
        print(f"✗ Error: {response.status_code}")


if __name__ == '__main__':
    load_earthquakes_from_usgs()