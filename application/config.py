import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DB_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "secret-key-vishvam-1025-21f1005939"
    JWT_ACCESS_TOKEN_EXPIRES = 14400


class LocalDevelopmentConfig(Config):
    SQLITE_DB_DIR = os.path.join(basedir, "../db_directory")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + \
        os.path.join(SQLITE_DB_DIR, "db.sqlite3")
    DEBUG = True
    JWT_SECRET_KEY = "secret-key-vishvam-1025-21f1005939"
    JWT_ACCESS_TOKEN_EXPIRES = 14400
