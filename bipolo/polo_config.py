import logging


class LogFormat(object):
    SINGLE_LINE = "%(levelname)-8s| %(asctime)s| %(name)-15s| %(pathname)s:%(module)s:%(funcName)s|%(lineno)d: %(message)s"
    MULTI_PROC = "%(levelname)-8s| [%(process)d]| %(name)-15s| %(module)s:%(funcName)s|%(lineno)d: %(message)s"
    MULTI_THREAD = "%(levelname)-8s| %(threadName)s| %(name)-15s| %(module)s:%(funcName)s|%(lineno)d: %(message)s"
    VERBOSE = "%(levelname)-8s| [%(process)d]| %(threadName)s| %(name)-15s| %(module)s:%(funcName)s|%(lineno)d: %(message)s"
    MULTI_LINE = "Level: %(levelname)s\nTime: %(asctime)s\nProcess: %(process)d\nThread: %(threadName)s\nLogger: %(name)s\nPath: %(module)s:%(lineno)d\nFunction :%(funcName)s\nMessage: %(message)s\n"


class Config(object):
    SECRET_KEY = '>5\x1d@\xc1u\xfa5\xf1\xa0\x14W9\x8e\xf3Q?G\x92\xa0\xea,\x01\xde'
    LOG_FORMAT = LogFormat.SINGLE_LINE
    LOG_LEVEL = "INFO"
    DEBUG = True
    # Set local database and echo
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def init_config(app):
    app.config.from_object(Config)
    # Check for local settings
    import os
    lpath = os.path.join(os.path.dirname(__file__), '..', 'polo_config_local.py')
    if os.path.exists(lpath):
        app.config.from_pyfile(lpath)
    else:
        logging.warn('Database connection string missing: Expected file {}'.format(lpath))
