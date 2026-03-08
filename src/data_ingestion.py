"""
Module 2: Data Ingestion and Storage (GaussDB & DataArts)
Handles crime data, load shedding schedules, and road network information
"""
import logging
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import random
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class RiskDataPoint:
    """Represents a single risk data point"""
    lat: float
    lng: float
    timestamp: datetime
    risk_level: float  # 0.0 to 1.0
    risk_factors: List[str]
    data_source: str

@dataclass
class LoadSheddingSchedule:
    """Load shedding schedule information"""
    area_id: str
    area_name: str
    stage: int
    start_time: datetime
    end_time: datetime
    affected_coordinates: List[Dict[str, float]]

class DataIngestionEngine:
    """Handles all data ingestion and preparation for SafeRoute AI"""
    
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self.crime_data: List[RiskDataPoint] = []
        self.load_shedding_data: List[LoadSheddingSchedule] = []
        self.road_network_data: Dict[str, Any] = {}
        
        # Initialize data containers
        self.crime_data: List[RiskDataPoint] = []
        self.load_shedding_data: List[LoadSheddingSchedule] = []
        self.road_network_data: Dict[str, Any] = {}
        
        # In production, data is loaded via trigger or schedule, not at init to save startup time
        logger.info("Data Ingestion Engine Initialized (Strict Production Mode)")
    

    
    def get_risk_score(self, lat: float, lng: float, timestamp: datetime = None) -> Dict[str, Any]:
        """
        Calculate risk score for a specific location and time
        This simulates the ModelArts prediction endpoint
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Find nearby crime data points (within ~5km radius)
        nearby_crimes = []
        for crime in self.crime_data:
            distance = self._calculate_distance(lat, lng, crime.lat, crime.lng)
            if distance < 5.0:  # 5km radius
                nearby_crimes.append((crime, distance))
        
        # Calculate base risk from crime data
        if nearby_crimes:
            # Weight by inverse distance
            weighted_risk = 0
            total_weight = 0
            for crime, distance in nearby_crimes:
                weight = 1 / (distance + 0.1)  # Avoid division by zero
                weighted_risk += crime.risk_level * weight
                total_weight += weight
            base_risk = weighted_risk / total_weight if total_weight > 0 else 0.3
        else:
            base_risk = 0.3  # Default risk for areas without data
        
        # Check load shedding impact
        load_shedding_risk = self._get_load_shedding_risk(lat, lng, timestamp)
        
        # Time-based risk adjustment
        hour = timestamp.hour
        time_multiplier = 1.5 if 18 <= hour <= 6 else 1.0  # Higher risk at night
        
        # Combine all risk factors
        final_risk = min(1.0, (base_risk * time_multiplier) + (load_shedding_risk * 0.3))
        
        return {
            "risk_score": round(final_risk, 3),
            "base_crime_risk": round(base_risk, 3),
            "load_shedding_risk": round(load_shedding_risk, 3),
            "time_multiplier": time_multiplier,
            "nearby_incidents": len(nearby_crimes),
            "risk_factors": self._get_active_risk_factors(lat, lng, timestamp)
        }
    
    def _get_load_shedding_risk(self, lat: float, lng: float, timestamp: datetime) -> float:
        """Check if location is affected by load shedding at given time"""
        for schedule in self.load_shedding_data:
            if schedule.start_time <= timestamp <= schedule.end_time:
                # Check if coordinates are in affected area
                for coord in schedule.affected_coordinates:
                    distance = self._calculate_distance(lat, lng, coord["lat"], coord["lng"])
                    if distance < 10.0:  # 10km radius for load shedding zones
                        return min(1.0, schedule.stage * 0.2)  # Stage 2 = 0.4, Stage 4 = 0.8
        return 0.0
    
    def _get_active_risk_factors(self, lat: float, lng: float, timestamp: datetime) -> List[str]:
        """Get list of active risk factors for location"""
        factors = []
        
        # Check time-based factors
        hour = timestamp.hour
        if 18 <= hour <= 6:
            factors.append("nighttime_hours")
        
        # Check load shedding
        if self._get_load_shedding_risk(lat, lng, timestamp) > 0:
            factors.append("load_shedding_active")
        
        # Check nearby crime patterns
        nearby_crimes = [c for c in self.crime_data 
                        if self._calculate_distance(lat, lng, c.lat, c.lng) < 2.0]
        
        if len(nearby_crimes) > 5:
            factors.append("high_crime_density")
        
        # Add common factors from nearby incidents
        all_factors = []
        for crime in nearby_crimes:
            all_factors.extend(crime.risk_factors)
        
        # Get most common factors
        factor_counts = {}
        for factor in all_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        common_factors = [f for f, count in factor_counts.items() if count >= 2]
        factors.extend(common_factors[:3])  # Top 3 most common
        
        return list(set(factors))  # Remove duplicates
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        return 2 * asin(sqrt(a)) * 6371  # Earth radius in km
    
    def store_risk_score(self, lat: float, lng: float, timestamp: datetime, risk_level: float) -> bool:
        """
        Store risk score in GaussDB (simulated for MVP)
        In production, this would use the GaussDB SDK
        """
        if self.demo_mode:
            logger.info(f"[DEMO] Storing risk score for ({lat:.4f}, {lng:.4f}) at {timestamp}: {risk_level}")
            return True
        
        # Real GaussDB implementation would go here
        try:
            # gaussdb_client.execute_sql(...)
            logger.info(f"Stored risk score in GaussDB: ({lat}, {lng}) = {risk_level}")
            return True
        except Exception as e:
            logger.error(f"Failed to store risk score: {e}")
            return False
    
    def get_training_data(self) -> pd.DataFrame:
        """
        Prepare training data for ModelArts
        Returns structured data for the risk prediction model
        """
        training_data = []
        
        for crime in self.crime_data:
            # Create features for ML model
            features = {
                "lat": crime.lat,
                "lng": crime.lng,
                "hour": crime.timestamp.hour,
                "day_of_week": crime.timestamp.weekday(),
                "month": crime.timestamp.month,
                "is_weekend": crime.timestamp.weekday() >= 5,
                "is_night": 18 <= crime.timestamp.hour <= 6,
                "risk_level": crime.risk_level,  # Target variable
                "num_risk_factors": len(crime.risk_factors),
                "has_gang_activity": "gang_activity" in crime.risk_factors,
                "has_poor_lighting": "poor_lighting" in crime.risk_factors,
                "has_theft_reports": "theft_reports" in crime.risk_factors,
            }
            training_data.append(features)
        
        df = pd.DataFrame(training_data)
        logger.info(f"Prepared training dataset with {len(df)} samples and {len(df.columns)} features")
        
        return df
    
    def simulate_social_sentiment_analysis(self, area_name: str) -> Dict[str, Any]:
        """
        Simulate social media sentiment analysis for area safety
        In production, this would integrate with SafeRoute AI NLP models
        """
        # Simulate sentiment scores
        sentiment_score = random.uniform(-0.5, 0.5)  # -1 to 1 scale
        
        # Generate mock social media mentions
        mentions = random.randint(10, 100)
        
        # Simulate keyword analysis
        safety_keywords = random.sample([
            "crime", "safe", "dangerous", "robbery", "police", 
            "security", "incident", "avoid", "careful", "patrol"
        ], random.randint(3, 6))
        
        return {
            "area_name": area_name,
            "sentiment_score": round(sentiment_score, 3),
            "total_mentions": mentions,
            "safety_keywords": safety_keywords,
            "risk_adjustment": max(0, -sentiment_score * 0.2),  # Negative sentiment increases risk
            "confidence": random.uniform(0.7, 0.95)
        }

# Global data ingestion engine
data_engine = DataIngestionEngine(demo_mode=True)