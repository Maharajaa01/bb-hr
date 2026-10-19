"""Response headers for BB HR.

HR data must never sit in a shared or browser HTTP cache, so every BB HR API
response and the session-bound /bbhr page are marked private + no-store. The
service worker script is revalidated on every load so updates roll out promptly.
"""

API_PREFIX = "/api/method/bb_academy_hrms."


def after_request(response, request):
	path = request.path or ""
	if path.startswith(API_PREFIX) or path == "/bbhr" or path.startswith("/bbhr/"):
		response.headers["Cache-Control"] = "private, no-store, max-age=0"
		response.headers["Pragma"] = "no-cache"
		response.headers["X-Content-Type-Options"] = "nosniff"
	elif path == "/bbhr_sw.js":
		response.headers["Cache-Control"] = "no-cache, max-age=0"
	return response
