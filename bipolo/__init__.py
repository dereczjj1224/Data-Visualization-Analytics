import logging.handlers

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import polo_config

# from sqlalchemy import create_engine

app = Flask(__name__, static_folder='templates')
polo_config.init_config(app)
config = app.config

# ----------------------------------------------------------------
# LOGGING SETUP
# Set up logging - tone down some loud libraries
# ----------------------------------------------------------------
logging.getLogger('sqlalchemy').setLevel(logging.WARN)
logging.basicConfig(format=config.get('LOG_FORMAT'))
logging.getLogger().setLevel(config.get('LOG_LEVEL'))

# ----------------------------------------------------------------
# SQLAlchemy Extension for Flask (Handles session creation and such)
# ----------------------------------------------------------------
db = SQLAlchemy(app)
# db = create_engine(config['SQLALCHEMY_DATABASE_URI'], echo=config['SQLALCHEMY_ECHO'])

from model import *
from view import *

