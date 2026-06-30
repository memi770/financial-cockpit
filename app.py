

from flask import Flask, session
from config import Config
from db import init_db, close_db

from routes.dashboard_routes import dashboard_bp
from routes.auth_routes import auth_bp
from routes.expenses_routes import expenses_bp
from routes.incomes_routes import incomes_bp
from routes.export_routes import export_bp
from routes.admin_routes import admin_bp
from routes.charts_routes import charts_bp

app = Flask(__name__)
app.config.from_object(Config)


# ---------- Register Blueprints ----------

app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(incomes_bp)
app.register_blueprint(export_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(charts_bp)


# ------------------- Database -------------------

with app.app_context():
    init_db()

app.teardown_appcontext(close_db)


# ---------- Context ----------

@app.context_processor
def inject_session():
    return dict(session=session)


# ------------------- Run App -------------------
if __name__ == "__main__":
    app.run(debug=True)


