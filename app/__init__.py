import os
from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix
from .extensions import ma, limiter, cache
from .models import db  # Import the SQLAlchemy instance from models
from .blueprints.customers import customers_bp  # Import the customers blueprint
from .blueprints.mechanics import mechanics_bp  # Import the mechanics blueprint
from .blueprints.service_tickets import (
    service_tickets_bp,
)  # Import the service tickets blueprint
from .blueprints.inventory import (
    inventory_items_bp,
)  # Import the inventory items blueprint
from .blueprints.vehicles import vehicles_bp  # Import the vehicles blueprint
from flask_swagger_ui import get_swaggerui_blueprint  # Import swagger ui blueprint

SWAGGER_URL = "/api/docs"  # URL for exposing Swagger UI (without trailing '/')
API_URL = "/static/swagger.yaml"  # Our API URL (can of course be a local resource)

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Mechanic Shop API"}
)


def create_app(config_name):

    # Load app configuration
    app = Flask(__name__)

    if config_name == "TestingConfig":
        app.config.from_object("config.TestingConfig")
    elif config_name == "DevelopmentConfig":
        app.config.from_object("config.DevelopmentConfig")
    elif config_name == "ProductionConfig":
        app.config.from_object("config.ProductionConfig")
        # Set database URI at runtime for production
        from config import get_database_uri

        app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    else:
        raise ValueError("Invalid config name")

    # Override rate limiter storage for production if Redis URL is available
    if config_name == "ProductionConfig" and os.environ.get("REDIS_URL"):
        app.config["RATELIMIT_STORAGE_URL"] = os.environ.get("REDIS_URL")
    elif config_name != "ProductionConfig":
        app.config["RATELIMIT_STORAGE_URL"] = "memory://"

    # On Render the app sits behind a reverse proxy. Without this, every
    # visitor would share the proxy's IP address and therefore one rate
    # limit bucket. x_for=1 trusts only the one proxy hop Render adds.
    if config_name == "ProductionConfig":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

        if not os.environ.get("SECRET_KEY"):
            app.logger.warning(
                "SECRET_KEY is not set: falling back to the default signing "
                "key in app/utils/util.py, which lets anyone forge login "
                "tokens. Set SECRET_KEY in the environment."
            )

    # Initialize extensions
    ma.init_app(app)  # Initialize Marshmallow
    db.init_app(app)  # Initialize SQLAlchemy
    limiter.init_app(app)
    cache.init_app(app)  # Initialize Flask-Caching

    # The default limit should not apply to the uptime check, the Swagger UI
    # (which loads many assets per page view) or static files.
    @limiter.request_filter
    def skip_default_limit_for_infrastructure():
        return (
            request.endpoint == "health_check"
            or request.endpoint == "static"
            or (request.blueprint or "") == swaggerui_blueprint.name
        )

    # Add a root route
    @app.route("/")
    def index():
        return {
            "message": "Welcome to Mechanic Shop API",
            "version": "1.0.0",
            "documentation": "/api/docs/",
            "endpoints": {
                "customers": "/customers",
                "mechanics": "/mechanics",
                "service_tickets": "/service_tickets",
                "inventory": "/inventory",
                "vehicles": "/vehicles",
            },
        }

    # Add health check endpoint for Render
    @app.route("/health")
    def health_check():
        try:
            # Test database connection
            with app.app_context():
                from sqlalchemy import text

                db.session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}, 200
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}, 500

    # Register blueprints
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    app.register_blueprint(service_tickets_bp, url_prefix="/service_tickets")
    app.register_blueprint(inventory_items_bp, url_prefix="/inventory")
    app.register_blueprint(vehicles_bp, url_prefix="/vehicles")
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
