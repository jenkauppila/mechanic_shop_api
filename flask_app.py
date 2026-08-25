import os
import sys
from app import create_app
from app.models import db
from config import mask_database_uri

try:
    app = create_app("ProductionConfig")
    print(
        f"✅ App created with config: {mask_database_uri(app.config.get('SQLALCHEMY_DATABASE_URI', 'No DB URI'))}"
    )

    with app.app_context():
        db.create_all()
        print("✅ Database tables created")

except Exception as e:
    print(f"❌ Error during app setup: {e}")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)
