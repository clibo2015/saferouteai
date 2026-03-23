#!/usr/bin/env python3
"""
Retrain SafeRoute model locally with current scikit-learn version
This ensures compatibility with the local environment
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import sklearn

print(f"Using scikit-learn version: {sklearn.__version__}")
print("=" * 60)

# Load training data
import os
processed_data_path = 'data/real_crime_hotspots_analysis.csv'

if os.path.exists(processed_data_path):
    print(f"Loading real-world 2025/2026 crime data from: {processed_data_path}")
    real_df = pd.read_csv(processed_data_path)
    
    # Map real data to feature format
    # The CSV has: province, station, quarterly_carjackings, quarterly_robberies, risk_level, is_carjacking_hotspot, is_robbery_hotspot, notable_trend, data_source, year, data_type, latitude, longitude
    
    data = {
        'lat': real_df['latitude'].values,
        'lng': real_df['longitude'].values,
        'hour': np.random.randint(0, 24, len(real_df)), # Approximate distribution
        'day_of_week': np.random.randint(0, 7, len(real_df)),
        'month': np.random.randint(1, 13, len(real_df)),
        'is_weekend': np.random.choice([0, 1], len(real_df)),
        'is_night': np.random.choice([0, 1], len(real_df)),
        'num_risk_factors': (real_df['is_carjacking_hotspot'].astype(int) + real_df['is_robbery_hotspot'].astype(int)),
        'has_gang_activity': real_df['is_carjacking_hotspot'].astype(int),
        'has_poor_lighting': real_df['is_robbery_hotspot'].astype(int),
        'has_theft_reports': (real_df['is_carjacking_hotspot'] | real_df['is_robbery_hotspot']).astype(int),
        'risk_level': real_df['quarterly_carjackings'].rank(pct=True).values # Target variable normalized
    }
    df = pd.DataFrame(data)
    print(f"Loaded {len(df)} real-world training samples")
else:
    print("Processed crime data not found. Using synthetic data for training...")
    data = {
        'lat': np.random.uniform(-35, -22, 1000),  # SA latitude range
        'lng': np.random.uniform(16, 33, 1000),    # SA longitude range
        'hour': np.random.randint(0, 24, 1000),
        'day_of_week': np.random.randint(0, 7, 1000),
        'month': np.random.randint(1, 13, 1000),
        'is_weekend': np.random.choice([0, 1], 1000),
        'is_night': np.random.choice([0, 1], 1000),
        'num_risk_factors': np.random.randint(0, 5, 1000),
        'has_gang_activity': np.random.choice([0, 1], 1000),
        'has_poor_lighting': np.random.choice([0, 1], 1000),
        'has_theft_reports': np.random.choice([0, 1], 1000),
        'risk_level': np.random.uniform(0, 1, 1000)  # Target variable
    }
    df = pd.DataFrame(data)
    print(f"Generated {len(df)} synthetic training samples")

# Prepare features and target
feature_columns = [
    'lat', 'lng', 'hour', 'day_of_week', 'month',
    'is_weekend', 'is_night', 'num_risk_factors',
    'has_gang_activity', 'has_poor_lighting', 'has_theft_reports'
]

X = df[feature_columns].values
y = df['risk_level'].values

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Random Forest model
print("Training model...")
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train_scaled, y_train)

# Evaluate model
y_pred = model.predict(X_test_scaled)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\nModel training completed:")
print(f"  R² Score: {r2:.4f}")
print(f"  MSE: {mse:.4f}")
print(f"  Training samples: {len(X_train)}")
print(f"  Test samples: {len(X_test)}")

# Create model artifacts
model_artifacts = {
    'model': model,
    'scaler': scaler,
    'feature_columns': feature_columns,
    'metrics': {"r2_score": r2, "mse": mse},
    'model_version': '1.0.1',
    'framework': 'sklearn',
    'sklearn_version': sklearn.__version__
}

# Save model
model_path = 'saferoute_model.pkl'
joblib.dump(model_artifacts, model_path)

print(f"\n✅ Model saved to: {model_path}")
print(f"   scikit-learn version: {sklearn.__version__}")
print("=" * 60)
