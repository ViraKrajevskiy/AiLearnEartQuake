import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
from django.db.models import Q


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
        """Создаёт пустую модель (без обучения)"""
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            random_state=42
        )
        self.is_trained = False

    def train(self, X_train, y_train):
        """
        Обучает модель на данных.
        X_train: [nearby_quakes, depth, time_since_last_big, latitude, longitude]
        y_train: величина землетрясения (magnitude)
        """
        if len(X_train) < 10:
            print(f"⚠️  Need at least 10 samples (have {len(X_train)})")
            return False

        print(f"🤖 Training on {len(X_train)} samples...")

        try:
            X_scaled = self.scaler.fit_transform(X_train)
            self.model.fit(X_scaled, y_train)

            # Оцениваем ошибку
            from sklearn.model_selection import cross_val_predict
            from sklearn.metrics import mean_squared_error
            y_pred = cross_val_predict(self.model, X_scaled, y_train, cv=5)
            self.rmse = np.sqrt(mean_squared_error(y_train, y_pred))

            print(f"✓ Model trained!")
            print(f"  Samples: {len(X_train)}")
            print(f"  RMSE: {self.rmse:.3f}")
            print(f"  Mean magnitude: {y_train.mean():.2f}")
            print(f"  Std: {y_train.std():.2f}")

            self.save_model()
            self.is_trained = True
            return True

        except Exception as e:
            print(f"✗ Training error: {e}")
            return False

    def predict(self, features):
        if self.model is None or not self.is_trained:
            return 0.0, 0.0, 0.0, 0.0

        try:
            features_array = np.array(features).reshape(1, -1)
            features_scaled = self.scaler.transform(features_array)

            # Получаем предсказание от каждого из 150 деревьев
            preds = [tree.predict(features_scaled)[0] for tree in self.model.estimators_]
            magnitude = np.mean(preds)

            # Вычисляем стандартное отклонение "мнений" деревьев
            std_dev = np.std(preds)

            # Уверенность: чем выше разброс (std_dev), тем ниже confidence
            # Если деревья сильно спорят, мы менее уверены
            confidence = max(0.6, 1.0 - (std_dev / 2.0))

            magnitude = max(0.0, min(magnitude, 10.0))
            margin = 1.96 * std_dev  # Используем текущий разброс вместо RMSE

            return float(magnitude), float(confidence), float(magnitude - margin), float(magnitude + margin)

        except Exception as e:
            print(f"✗ Prediction error: {e}")
            return 0.0, 0.0, 0.0, 0.0

    def save_model(self):
        """Сохраняет модель и скейлер"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            print(f"💾 Model saved to {self.model_path}")
        except Exception as e:
            print(f"✗ Save error: {e}")

    def load_model(self):
        """Загружает модель и скейлер"""
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
        Вычисляет признаки для предсказания.
        Returns: [nearby_quakes_count, depth, time_since_last_big, latitude, longitude]
        """
        from AiLeranProject.models import Earthquake

        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        # Радиус поиска (~100 км ≈ 0.9 градуса)
        lat_range = 0.9
        lon_range = 0.9 / np.cos(np.radians(latitude)) if latitude != 90 else 0.9

        # Количество землетрясений >2.0 за 7 дней в радиусе
        nearby_quakes = Earthquake.objects.filter(
            timestamp__gte=seven_days_ago,
            magnitude__gt=2.0,
            latitude__gte=latitude - lat_range,
            latitude__lte=latitude + lat_range,
            longitude__gte=longitude - lon_range,
            longitude__lte=longitude + lon_range
        ).count()

        # Время с последнего крупного землетрясения (≥4.0)
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
            nearby_quakes,  # feature 0
            depth,  # feature 1
            time_since_last_big,  # feature 2
            latitude,  # feature 3
            longitude  # feature 4
        ]