
"""
ASHA Seva Backend - Entry Point
================================
Run with:  python app.py
Production: gunicorn -w 4 -b 0.0.0.0:5000 app:app
"""

import logging
import os

from app import create_app
from flask_cors import CORS

app = create_app()

if __name__ == "__main__":
    # Configure root logger so startup messages appear in the console.
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
