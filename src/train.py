#!/usr/bin/env python3
"""
ModelArts Training Script for SafeRoute AI Risk Prediction Model
This script is executed on ModelArts training instances
"""
import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import argparse

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='SafeRoute AI Model Training')
    
    # Support both ModelArts naming conventions
    parser.add_argument('--data_url', type=str, help='Training data URL (OBS path)')
    parser.add_argument('--train_url', type=str, help='Output model URL (OBS path)')
    
    # ModelArts console passes these names (with hyphens)
    parser.add_argument('--crime-data', dest='data_url', type=str, help='Training data URL (ModelArts format)')
    parser.add_argument('--models', dest='train_url', type=str, help='Output model URL (ModelArts format)')
    
    # Training hyperparameters
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--n_estimators', type=int, default=100, help='Number of trees in Random Forest')
    parser.add_argument('--max_depth', type=int, default=10, help='Maximum depth of trees')
    
    args = parser.parse_args()
    
    # Ensure we have the required paths
    if not args.data_url:
        args.data_url = '/tmp/data'
    if not args.train_url:
        args.train_url = '/tmp/model'
    
    return args

def load_training_data(data_path):
    """Load and prepare training data"""
    print(f"Loading training data from: {data_path}")
    
    # Try to load actual CSV files from the data path
    import glob
    csv_files = glob.glob(os.path.join(data_path, '*.csv'))
    
    if csv_files:
        print(f"Found {len(csv_files)} CSV file(s)")
        # Load the first CSV file
        df = pd.read_csv(csv_files[0])
        print(f"Loaded {len(df)} samples from {csv_files[0]}")
        
        # If the CSV has the expected columns, use it directly
        expected_cols = ['lat', 'lng', 'hour', 'day_of_week', 'month', 
                        'is_weekend', 'is_night', 'risk_level']
        
        if all(col in df.columns for col in expected_cols):
            print("Using real crime data from CSV")
            return df
        else:
            print(f"CSV columns: {list(df.columns)}")
            print("CSV doesn't have expected format, using synthetic data")
    else:
        print("No CSV files found, using synthetic data")
    
    # Fallback: Create synthetic data
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
    return df

def train_model(df, args):
    """Train the SafeRoute risk prediction model"""
    print("Starting model training...")
    
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
    model = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test_scaled)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model training completed:")
    print(f"  R² Score: {r2:.4f}")
    print(f"  MSE: {mse:.4f}")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")
    
    return model, scaler, feature_columns, {"r2_score": r2, "mse": mse}

def save_model(model, scaler, feature_columns, metrics, output_path):
    """Save trained model and artifacts"""
    print(f"Saving model to: {output_path}")
    
    # Create model artifacts
    model_artifacts = {
        'model': model,
        'scaler': scaler,
        'feature_columns': feature_columns,
        'metrics': metrics,
        'model_version': '1.0.0',
        'framework': 'sklearn'
    }
    
    # Save to ModelArts output path (will be uploaded to OBS automatically)
    import os
    os.makedirs(output_path, exist_ok=True)
    model_path = os.path.join(output_path, 'saferoute_model.pkl')
    
    joblib.dump(model_artifacts, model_path)
    
    print(f"Model saved to: {model_path}")
    print("ModelArts will automatically upload this to OBS")
    
    return model_path

def main():
    """Main training function"""
    print("SafeRoute AI ModelArts Training Started")
    print("=" * 50)
    
    # Parse arguments
    args = parse_args()
    print(f"Training arguments: {vars(args)}")
    
    try:
        # Load training data
        df = load_training_data(args.data_url)
        
        # Train model
        model, scaler, feature_columns, metrics = train_model(df, args)
        
        # Save model
        model_path = save_model(model, scaler, feature_columns, metrics, args.train_url)
        
        print("=" * 50)
        print("Training completed successfully!")
        print(f"Model performance: R² = {metrics['r2_score']:.4f}")
        print(f"Model saved to: {model_path}")
        
    except Exception as e:
        print(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()