import json
import os
import sys

import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.routing_engine import routing_engine
from src.real_data_integration import real_data_integrator
from src.data_ingestion import data_engine

try:
    from src.edge_ai_processor import EdgeAIProcessor
except Exception:  # cv2 / ultralytics are optional for the field-test runtime
    EdgeAIProcessor = None


class TestRealIntegration:

    @patch("src.routing_engine.requests")
    def test_routing_engine_calls_osrm(self, mock_requests):
        """Routing geometry must come from public OSRM (not Huawei Map Kit)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "Ok",
            "routes": [
                {
                    "distance": 1200.0,
                    "duration": 180.0,
                    "geometry": {
                        "coordinates": [
                            [18.8604, -33.9338],
                            [18.8550, -33.9300],
                            [18.8360, -33.9195],
                        ]
                    },
                }
            ],
        }
        mock_requests.get.return_value = mock_response

        segments = routing_engine._fetch_route_from_api(
            -33.9338, 18.8604, -33.9195, 18.8360, {}
        )

        args, _kwargs = mock_requests.get.call_args
        url = args[0]
        assert url.startswith("https://router.project-osrm.org/route/v1/driving/")
        assert "18.8604,-33.9338;18.836,-33.9195" in url
        assert "geometries=geojson" in url
        assert "mapapi.cloud.huawei.com" not in url
        assert len(segments) == 2
        assert all(seg.distance_km > 0 for seg in segments)

    def test_map_config_is_huawei_free(self):
        """Map config must describe Leaflet/OSM + OSRM + Nominatim only."""
        from src.opensource_maps import map_service

        config = map_service.get_map_config()
        assert config["provider"] == "leaflet_osm"
        assert config["routing_provider"] == "osrm"
        assert config["geocoding_provider"] == "nominatim"
        assert config["map_options"]["center"] == {"lat": -33.9321, "lng": 18.8602}
        assert "huawei" not in json.dumps(config).lower()

    def test_config_requires_no_huawei_credentials(self):
        """The runtime settings must not expose or require HUAWEI_* variables."""
        from src.config import settings

        assert not hasattr(settings, "huawei_cloud_ak")
        assert settings.osrm_base_url.startswith("http")
        assert settings.get_map_defaults()["center"]["lat"] == pytest.approx(-33.9321)

    @patch("src.real_data_integration.requests")
    def test_eskom_integration_calls_api(self, mock_requests):
        """Verify Eskom integration calls real API"""
        with patch("config.settings.eskom_se_push_key", "test_key"):
            real_data_integrator.get_eskom_load_shedding_data()

            args, kwargs = mock_requests.get.call_args
            assert "developer.sepush.co.za" in args[0]
            assert kwargs["headers"]["token"] == "test_key"

    def test_data_ingestion_no_mock_generation(self):
        """Verify data ingestion does not generate random mock data on init"""
        engine = data_engine.__class__()
        assert len(engine.crime_data) == 0
        assert len(engine.load_shedding_data) == 0

    @pytest.mark.skipif(EdgeAIProcessor is None, reason="edge AI dependencies not installed")
    def test_edge_ai_processor_structure(self):
        """Verify Edge AI processor is set up for real processing"""
        processor = EdgeAIProcessor(model_path="yolov8n.pt")
        assert 0 in processor.hazard_classes
        assert processor.hazard_classes[0] == "pedestrian_on_road"
