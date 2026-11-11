"""
AI Copilot Module for SafeRouteAI
Provides intelligent, real-time driving safety briefings via APInex AI Gateway.
Compatible with OpenAI-style chat completion endpoints.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import requests

try:
    from config import settings
except ImportError:
    from src.config import settings

logger = logging.getLogger(__name__)


class AICopilotService:
    """
    Intelligent safety briefing and real-time situational assistant
    powered by APInex LLM Gateway (DeepSeek/GLM/Gemini free models).
    """

    def __init__(self):
        self.api_key = getattr(settings, "apinex_api_key", None) or os.getenv("APINEX_API_KEY")
        self.base_url = (getattr(settings, "apinex_base_url", "https://api.apinex.bond/v1") or "https://api.apinex.bond/v1").rstrip("/")
        self.model = getattr(settings, "apinex_model", "free/deepseek-v4.1-flash") or "free/deepseek-v4.1-flash"
        self.timeout = 10

    def is_configured(self) -> bool:
        """True if APInex API key is present."""
        return bool(self.api_key and self.api_key.strip())

    def generate_safety_briefing(
        self,
        route_summary: Dict[str, Any],
        hazards: Optional[List[Dict[str, Any]]] = None,
        departure_time: Optional[datetime] = None,
    ) -> List[str]:
        """
        Generate driving safety insights using APInex LLM Gateway,
        falling back to local heuristics if APInex is not configured or offline.
        """
        if not self.is_configured():
            return self._fallback_briefing(route_summary, hazards, departure_time)

        try:
            return self._call_llm(route_summary, hazards, departure_time)
        except Exception as e:
            logger.warning(f"APInex AI Copilot call failed ({e}); using local fallback.")
            return self._fallback_briefing(route_summary, hazards, departure_time)

    def _call_llm(
        self,
        route_summary: Dict[str, Any],
        hazards: Optional[List[Dict[str, Any]]] = None,
        departure_time: Optional[datetime] = None,
    ) -> List[str]:
        """Call APInex chat/completions endpoint."""
        dt = departure_time or datetime.now()
        hour = dt.strftime("%H:%M")
        distance_km = route_summary.get("total_distance_km", 0)
        duration_min = route_summary.get("total_time_minutes", 0)
        safety_score = route_summary.get("overall_safety_score", 0.7)

        hazard_notes = []
        if hazards:
            for h in hazards[:4]:
                name = h.get("title") or h.get("name") or "Hazard zone"
                severity = h.get("severity") or h.get("risk", 0.5)
                hazard_notes.append(f"- {name} (risk severity: {severity})")

        prompt = (
            f"You are the SafeRouteAI Driving Safety Copilot for South Africa (Stellenbosch / Western Cape region).\n"
            f"Trip context:\n"
            f"- Departure time: {hour}\n"
            f"- Distance: {distance_km:.1f} km, estimated {duration_min:.0f} mins\n"
            f"- Route safety score: {safety_score * 100:.0f}%\n"
            f"- Nearby known hotspots / hazards:\n"
            f"{chr(10).join(hazard_notes) if hazard_notes else 'None directly on path.'}\n\n"
            f"Provide exactly 3 to 4 concise, high-value, actionable bullet points for the driver "
            f"(e.g. lighting, specific junction alerts like R44/Kayamandi/Dorp St, situational awareness, load shedding). "
            f"Each point must be under 16 words. Do not use asterisks or markdown headings. One tip per line."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a concise in-car navigation safety assistant. Return plain bullet statements only.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 150,
            "temperature": 0.3,
        }

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            lines = [
                line.lstrip("-•* 0123456789.)").strip()
                for line in content.split("\n")
                if line.strip()
            ]
            valid_lines = [l for l in lines if len(l) > 5]
            if valid_lines:
                return valid_lines[:4]

        logger.warning(f"APInex HTTP {resp.status_code}: {resp.text[:200]}")
        return self._fallback_briefing(route_summary, hazards, departure_time)

    def _fallback_briefing(
        self,
        route_summary: Dict[str, Any],
        hazards: Optional[List[Dict[str, Any]]] = None,
        departure_time: Optional[datetime] = None,
    ) -> List[str]:
        """Local heuristic insights when offline or without API key."""
        dt = departure_time or datetime.now()
        hour = dt.hour
        insights = []

        if 18 <= hour or hour <= 6:
            insights.append("Night navigation active — stick to main corridors with operational street lighting")
        else:
            insights.append("Daytime driving route selected with standard pedestrian awareness")

        if hazards:
            insights.append(f"{len(hazards)} caution zones flagged nearby — keep doors locked at intersections")
        else:
            insights.append("Low incident density along current Stellenbosch road segments")

        insights.append("Emergency services (SAPS 10111 / ER24 084 124) monitored along route")
        return insights


ai_copilot = AICopilotService()
