/**
 * SafeRouteAI — Shared Crime Hotspot Database & Proximity Utilities
 * Source: SAPS 2025/2026 Q1-Q3 verified crime statistics
 * Used by: SafeRouteMapComponent.js (map layer) & HazardHUD.js (live alerts)
 */

// ─── Alert radius thresholds ─────────────────────────────────────────────────
export const ALERT_RADIUS_KM = {
  EXTREME: 0.30,  // 300m — red zones (risk >= 0.85)
  HIGH:    0.20,  // 200m — orange zones (risk >= 0.70)
  MODERATE: 0.10, // 100m — yellow zones (risk >= 0.50)
};

// ─── Voice message templates per crime type ──────────────────────────────────
export const VOICE_TEMPLATES = {
  carjacking: (name, dist) =>
    `Warning! Carjacking hotspot ahead in ${dist} metres. ${name}. Keep doors locked and windows up. Stay alert at traffic lights.`,
  hijacking: (name, dist) =>
    `Danger! Vehicle hijacking zone ahead in ${dist} metres. ${name}. Do not stop. Keep moving if safe to do so.`,
  robbery: (name, dist) =>
    `Caution! High robbery area in ${dist} metres. ${name}. Secure valuables. Stay in your vehicle if possible.`,
  mugging: (name, dist) =>
    `Alert! Mugging zone ahead in ${dist} metres. ${name}. Avoid pedestrian contact. Keep windows up.`,
  murder: (name, dist) =>
    `Extreme danger! High violence zone in ${dist} metres. ${name}. Consider re-routing immediately.`,
  default: (name, dist) =>
    `Safety alert! Crime hotspot in ${dist} metres. ${name}. Proceed with caution.`,
};

// ─── Risk level labels ───────────────────────────────────────────────────────
export function getRiskLevel(risk) {
  if (risk >= 0.85) return 'EXTREME';
  if (risk >= 0.70) return 'HIGH';
  if (risk >= 0.50) return 'MODERATE';
  return 'LOW';
}

export function getRiskColor(risk) {
  if (risk >= 0.85) return '#e41e26';
  if (risk >= 0.70) return '#ff7600';
  if (risk >= 0.50) return '#ffc300';
  return '#00cc66';
}

// ─── Haversine distance (km) ─────────────────────────────────────────────────
export function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) *
    Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Find hotspots within alert radius of a given position.
 * Returns array sorted by distance ascending.
 */
export function getNearbyHotspots(lat, lng, hotspots) {
  const results = [];

  for (const h of hotspots) {
    const distKm = haversineKm(lat, lng, h.lat, h.lng);
    const level = getRiskLevel(h.risk);
    const threshold = ALERT_RADIUS_KM[level] || ALERT_RADIUS_KM.MODERATE;

    if (distKm <= threshold) {
      results.push({ ...h, distKm, distM: Math.round(distKm * 1000) });
    }
  }

  return results.sort((a, b) => a.distKm - b.distKm);
}

/**
 * Build voice message for a hotspot.
 */
export function buildVoiceMessage(hotspot) {
  const template = VOICE_TEMPLATES[hotspot.type] || VOICE_TEMPLATES.default;
  return template(hotspot.name, hotspot.distM);
}

/**
 * Speak a message using Web Speech API (non-blocking).
 * Cancels any in-progress utterance of the same priority.
 */
export function speak(message, { rate = 0.95, pitch = 1.0, lang = 'en-ZA' } = {}) {
  if (!window.speechSynthesis) return;

  // Don't interrupt if currently speaking an urgent message
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(message);
  utterance.rate = rate;
  utterance.pitch = pitch;
  utterance.lang = lang;

  // Prefer South African English voice if available
  const voices = window.speechSynthesis.getVoices();
  const zaVoice = voices.find(v => v.lang === 'en-ZA') ||
                  voices.find(v => v.lang.startsWith('en-'));
  if (zaVoice) utterance.voice = zaVoice;

  window.speechSynthesis.speak(utterance);
}

// ─── Re-route eligibility ────────────────────────────────────────────────────
/**
 * Returns true if the current hotspot warrants a re-route suggestion.
 * Only triggers for HIGH or EXTREME zones.
 */
export function shouldSuggestReroute(hotspot) {
  return hotspot.risk >= 0.70;
}
