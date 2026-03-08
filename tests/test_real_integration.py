
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

# Add src to path
# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.routing_engine import routing_engine, RouteSegment
from src.real_data_integration import real_data_integrator
from src.data_ingestion import data_engine
from src.edge_ai_processor import EdgeAIProcessor

class TestRealIntegration:
    
    @patch('src.routing_engine.requests')
    def test_routing_engine_calls_api(self, mock_requests):
        """Verify routing engine calls real Huawei API"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"routes": []} 
        mock_requests.post.return_value = mock_response
        
        # We need to ensure API key is present for the test logic to proceed to request
        with patch('src.config.settings.huawei_map_api_key', 'test_key'):
            try:
                # We expect segments even if empty api response due to our fail-safe logic, 
                # but KEY is we want to see the API call.
                routing_engine._fetch_route_from_api(
                    -26.0, 28.0, -26.1, 28.1, {}
                )
            except Exception:
                # pass if it fails on parsing, we just want to check the call
                pass
                
            # Assert API was called
            args, kwargs = mock_requests.post.call_args
            assert "mapapi.cloud.huawei.com" in args[0]
            assert kwargs['json']['origin'] == {'lat': -26.0, 'lng': 28.0}

    @patch('src.real_data_integration.requests')
    def test_eskom_integration_calls_api(self, mock_requests):
        """Verify Eskom integration calls real API"""
        with patch('src.config.settings.eskom_se_push_key', 'test_key'):
            real_data_integrator.get_eskom_load_shedding_data()
            
            # Assert API was called
            args, kwargs = mock_requests.get.call_args
            assert "developer.sepush.co.za" in args[0]
            assert kwargs['headers']['token'] == 'test_key'

    def test_data_ingestion_no_mock_generation(self):
        """Verify data ingestion does not generate random mock data on init"""
        # Re-init data engine to check state
        engine = data_engine.__class__() 
        assert len(engine.crime_data) == 0
        assert len(engine.load_shedding_data) == 0
        # It should rely on real_data_integrator, not internal loop

    def test_edge_ai_processor_structure(self):
        """Verify Edge AI processor is set up for real processing"""
        processor = EdgeAIProcessor(model_path="yolov8n.pt")
        # hazard_classes should be defined
        assert 0 in processor.hazard_classes
        assert processor.hazard_classes[0] == "pedestrian_on_road"
