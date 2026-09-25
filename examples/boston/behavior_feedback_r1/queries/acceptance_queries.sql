-- One complete observation -> overlay -> OD -> probability -> vehicle -> link trace.
SELECT * FROM end_to_end_feedback_trace;

-- Compare planned and exploratory transit response at the traced OD/departure.
SELECT od_id, departure_time, scenario_id, total_min,
       mu_transit_sensitivity, probability
FROM scenario_transit_response
WHERE od_id='panel_od_019'
  AND departure_time='12:30:00'
  AND mu_transit_sensitivity=1.0
ORDER BY scenario_id;

-- Distinguish scheduled no-path from network coverage unknowns.
SELECT availability_status, COUNT(*) AS rows
FROM od_multimodal_skims
GROUP BY availability_status;

-- Recalculate a transit itinerary's physical time account.
SELECT path_id,
       SUM(COALESCE(physical_seconds,0)+COALESCE(wait_seconds,0)) AS accounted_seconds
FROM itinerary_legs
GROUP BY path_id
ORDER BY accounted_seconds DESC
LIMIT 10;
