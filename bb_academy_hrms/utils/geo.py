"""Geo helpers for geofenced attendance. Pure functions - no Frappe imports, so they unit test cleanly."""

import math

EARTH_RADIUS_M = 6371000.0


def haversine_distance(lat1, lon1, lat2, lon2):
	"""Great-circle distance in metres between two WGS84 points, or None if any value is missing."""
	if None in (lat1, lon1, lat2, lon2):
		return None
	lat1, lon1, lat2, lon2 = (float(lat1), float(lon1), float(lat2), float(lon2))
	p1, p2 = math.radians(lat1), math.radians(lat2)
	d_phi = math.radians(lat2 - lat1)
	d_lambda = math.radians(lon2 - lon1)
	a = math.sin(d_phi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lambda / 2) ** 2
	return round(2 * EARTH_RADIUS_M * math.asin(math.sqrt(a)), 2)


def is_valid_coordinate(lat, lon):
	try:
		lat, lon = float(lat), float(lon)
	except (TypeError, ValueError):
		return False
	if math.isnan(lat) or math.isnan(lon):
		return False
	# (0, 0) is what a broken GPS stack reports; nobody works in the Gulf of Guinea.
	if lat == 0 and lon == 0:
		return False
	return -90 <= lat <= 90 and -180 <= lon <= 180


def nearest_location(lat, lon, locations, default_radius):
	"""Return (location, distance, allowed_radius) for the closest location, or (None, None, None).

	`locations` is an iterable of objects/dicts with location_name, latitude, longitude, radius.
	"""
	best = (None, None, None)
	for loc in locations:
		get = loc.get if isinstance(loc, dict) else lambda k, _l=loc: getattr(_l, k, None)
		distance = haversine_distance(lat, lon, get("latitude"), get("longitude"))
		if distance is None:
			continue
		if best[1] is None or distance < best[1]:
			best = (loc, distance, int(get("radius") or 0) or int(default_radius or 0))
	return best


def within_geofence(distance, radius, accuracy=None, tolerance=0):
	"""A fix counts as inside when distance <= radius + min(accuracy, tolerance).

	Reported accuracy widens the fence only up to `tolerance`, so a wildly
	imprecise fix cannot be used to check in from across town.
	"""
	if distance is None or radius is None:
		return False
	slack = min(max(float(accuracy or 0), 0), float(tolerance or 0))
	return float(distance) <= float(radius) + slack
