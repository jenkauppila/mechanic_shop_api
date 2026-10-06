from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

ma = Marshmallow()  # Instantiate Marshmallow for serialization
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    # Baseline safety net: applies to every route that does not set its own
    # limit. Per-route limits (login, registration, writes) are stricter.
    default_limits=["200 per day", "60 per hour"],
)  # creating an instance of Limiter
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})  # Simple in-memory cache
