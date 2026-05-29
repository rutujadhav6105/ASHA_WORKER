"""
app/extensions.py
==================
All Flask extension objects are created here WITHOUT a bound app.
They are later initialised with the real Flask app inside create_app()
via the init_app() pattern.

This pattern is the standard solution to circular-import problems in Flask:
  • extensions.py  →  no imports from app/
  • models         →  import db from extensions
  • routes         →  import db, jwt, bcrypt from extensions
  • create_app()   →  import everything and wire it together
"""

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# ------------------------------------------------------------------ Singletons
db  = SQLAlchemy()     # ORM – used by all models
jwt = JWTManager()     # JWT authentication
bcrypt = Bcrypt()      # Password hashing
ma  = Marshmallow()    # Serialisation / validation
migrate = Migrate()    # Database migration tool
