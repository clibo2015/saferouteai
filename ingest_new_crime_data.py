import logging
import sys
import os
from pathlib import Path
from src.real_data_integration import RealDataIntegrator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ingest_2025_data():
    """
    Ingest and process the new 2025/2026 SAPS crime data.
    Ensures safe-routing is based on the most recent statistics.
    """
    logger.info("Starting SAPS 2025/2026 Data Ingestion Process")
    
    # Check if root CSV files exist
    csv_1 = "South Africa Crime Hotspots Analysis - South Africa Crime Hotspots Analysis.csv"
    csv_2 = "South Africa Crime Hotspots Analysis - South Africa Crime Hotspots Analysis (1).csv"
    
    if not os.path.exists(csv_1) or not os.path.exists(csv_2):
        logger.error("Error: Updated SAPS CSV files not found in the root directory.")
        logger.error(f"Expected: {csv_1}")
        logger.error(f"Expected: {csv_2}")
        return False

    try:
        # Initialize the integrator
        integrator = RealDataIntegrator()
        
        # 1. Process Hotspots (Parses your new CSV data)
        logger.info("Processing quarterly statistics into risk hotspots...")
        hotspots_df = integrator.load_real_crime_hotspots_data()
        
        if hotspots_df.empty:
            logger.error("Processing failed: No data extracted from the CSVs.")
            return False
            
        # 2. Integrate and Cache (Creates data/saps_crime_data_real.csv)
        logger.info("Generating backend integrated dataset...")
        crime_df = integrator.download_saps_crime_data()
        
        logger.info("=" * 60)
        logger.info("✅ SUCCESS: 2025/2026 Data Ingested Successfully")
        logger.info(f"   Processed Records: {len(hotspots_df)}")
        logger.info(f"   Provinces Covered: {hotspots_df['province'].nunique()}")
        logger.info(f"   Destination: data/real_crime_hotspots_analysis.csv")
        logger.info("=" * 60)
        
        logger.info("\nNEXT STEP: Run 'python retrain_model_locally.py' to update the AI logic.")
        return True
        
    except Exception as e:
        logger.error(f"FATAL ERROR during ingestion: {e}")
        return False

if __name__ == "__main__":
    if ingest_2025_data():
        sys.exit(0)
    else:
        sys.exit(1)
