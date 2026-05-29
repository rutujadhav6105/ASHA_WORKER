import os, sys
sys.path.append('C:/FlutterProject/backend')
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    from sqlalchemy import text
    db.session.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
    db.session.commit()
    print('alembic_version dropped')
