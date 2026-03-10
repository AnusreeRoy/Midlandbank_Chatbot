# chatbot/throttles.py
from rest_framework.throttling import SimpleRateThrottle

class SessionRateThrottle(SimpleRateThrottle):
    """
    Throttle rate per user session (not IP).
    Each browser session gets its own limit.
    """
    scope = 'session'

    def get_cache_key(self, request, view):
        # If no session key exists, create one
        if not request.session.session_key:
            request.session.create()

        # Use the session key to track this user's requests
        return self.cache_format % {
            'scope': self.scope,
            'ident': request.session.session_key
        }
