"""Serves the BB HR single-page app at /bbhr and /bbhr/<anything>."""

import frappe

no_cache = 1


def get_context(context):
	# The SPA posts to whitelisted methods, so it needs this session's CSRF token.
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # get_csrf_token may have written the session
	context.csrf_token = csrf_token
	context.no_cache = 1
	return context
