import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
from django.db.models import Q
import math


class EarthquakePredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'earthquake_model_v2.pkl'
        self.scaler_path = 'scaler_model_v2.pkl'
        self.rmse = 0.45
        self.is_trained = False

        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.load_model()
            self.is_trained = True
        else:
            self.build_model()

    def build_model(self):
        """Creates an empty model (without training)"""
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False

    def train(self, X_train, y_train):
        """
        Trains the model on data.
        X_train: [nearby_quakes, depth, time_since_last_big, latitude, longitude]
        y_train: earthquake magnitude
        """
        if len(X_train) < 10:
            print(f"⚠️  Need at least 10 samples (have {len(X_train)})")
            return False

        print(f"🤖 Training on {len(X_train)} samples...")

        try:
            X_scaled = self.scaler.fit_transform(X_train)
            self.model.fit(X_scaled, y_train)

            # Evaluate error using cross-validation
            from sklearn.model_selection import cross_val_predict
            from sklearn.metrics import mean_squared_error
            y_pred = cross_val_predict(self.model, X_scaled, y_train, cv=min(5, len(X_train)))
            self.rmse = np.sqrt(mean_squared_error(y_train, y_pred))

            print(f"✓ Model trained!")
            print(f"  Samples: {len(X_train)}")
            print(f"  RMSE: {self.rmse:.3f}")
            print(f"  Mean magnitude: {y_train.mean():.2f}")
            print(f"  Std: {y_train.std():.2f}")

            self.is_trained = True
            self.save_model()
            return True

        except Exception as e:
            print(f"✗ Training error: {e}")
            self.is_trained = False
            return False

    def predict(self, features):
        """
        Predicts magnitude from features.
        Returns: (magnitude, confidence, lower_bound, upper_bound)
        """
        if self.model is None or not self.is_trained:
            return 0.0, 0.0, 0.0, 0.0

        try:
            features_array = np.array(features).reshape(1, -1)
            features_scaled = self.scaler.transform(features_array)

            # Get predictions from all trees
            preds = [tree.predict(features_scaled)[0] for tree in self.model.estimators_]
            magnitude = np.mean(preds)

            # Calculate standard deviation of tree predictions
            std_dev = np.std(preds)

            # Confidence: higher std_dev = lower confidence
            confidence = max(0.6, 1.0 - (std_dev / 2.0))
            confidence = min(0.99, confidence)

            # Clamp magnitude
            magnitude = max(0.0, min(magnitude, 10.0))

            # 95% confidence interval using tree std_dev
            margin = 1.96 * std_dev

            return float(magnitude), float(confidence), float(max(0, magnitude - margin)), float(magnitude + margin)

        except Exception as e:
            print(f"✗ Prediction error: {e}")
            return 0.0, 0.0, 0.0, 0.0

    def predict_batch(self, features_list):
        """Predicts magnitudes for multiple feature sets"""
        if self.model is None or not self.is_trained:
            return [(0.0, 0.0, 0.0, 0.0)] * len(features_list)

        results = []
        for features in features_list:
            results.append(self.predict(features))
        return results

    def save_model(self):
        """Saves model and scaler"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            print(f"💾 Model saved to {self.model_path}")
        except Exception as e:
            print(f"✗ Save error: {e}")

    def load_model(self):
        """Loads model and scaler"""
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.is_trained = True
            print(f"✓ Model loaded from {self.model_path}")
        except Exception as e:
            print(f"✗ Load error: {e}")
            self.is_trained = False

    @staticmethod
    def compute_features(latitude, longitude, depth):
        """
        Computes features for prediction.
        Returns: [nearby_quakes_count, depth, time_since_last_big, latitude, longitude]
        """
        from AiLeranProject.models import Earthquake

        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        # Search radius (~100 km ≈ 0.9 degrees)
        lat_range = 0.9
        cos_lat = math.cos(math.radians(latitude))
        lon_range = 0.9 / cos_lat if cos_lat > 0.01 else 0.9

        # Number of earthquakes >2.0 in the last 7 days within radius
        nearby_quakes = Earthquake.objects.filter(
            timestamp__gte=seven_days_ago,
            magnitude__gt=2.0,
            latitude__gte=latitude - lat_range,
            latitude__lte=latitude + lat_range,
            longitude__gte=longitude - lon_range,
            longitude__lte=longitude + lon_range
        ).count()

        # Time since last big earthquake (≥4.0)
        last_big = Earthquake.objects.filter(
            magnitude__gte=4.0,
            latitude__gte=latitude - lat_range,
            latitude__lte=latitude + lat_range,
            longitude__gte=longitude - lon_range,
            longitude__lte=longitude + lon_range
        ).order_by('-timestamp').first()

        if last_big:
            time_since_last_big = (now - last_big.timestamp).days / 365.25
        else:
            time_since_last_big = 10.0

        return [
            float(nearby_quakes),
            float(depth),
            float(time_since_last_big),
            float(latitude),
            float(longitude)
        ]