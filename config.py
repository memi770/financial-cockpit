import os


class Config:
    SECRET_KEY =os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    DATABASE = "finance.db"