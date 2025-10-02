import logging
import os
from pathlib import Path

from celery import Celery
from flask import Flask
from flask_cors import CORS
from prometheus_client import make_wsgi_app
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from api import api
from reloader import get_config


def create_app():
    app = Flask('s4d_farm')

    # Trigger singleton init
    app.config.update(get_config())

    app.logger.setLevel(logging.DEBUG)
    for handler in app.logger.handlers:
        handler.setLevel(logging.DEBUG)

    app.register_blueprint(api)

    CORS(app)
    PrometheusMetrics(app)

    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/api/metrics': make_wsgi_app(),
    })

    return app


def create_celery():
    # Ensure the data directory exists
    data_dir = Path('/app/data')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure the celery directory exists
    celery_dir = data_dir / 'celery' / 'out'
    celery_dir.mkdir(parents=True, exist_ok=True)
    
    broker = os.getenv('CELERY_BROKER_URL', 'filesystem:///app/data/celery')
    celery = Celery(
        'ad_farm',
        broker=broker,
        include=['tasks'],
    )
    
    # Configure Celery for filesystem broker
    celery.conf.update(
        result_backend='cache+memory://',
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        broker_transport_options={
            'data_folder_in': '/app/data/celery/out',
            'data_folder_out': '/app/data/celery/out',
        }
    )
    
    period = get_config()['SUBMIT_PERIOD']
    celery.conf.beat_schedule = {
        f'submit_flags': {
            'task': 'tasks.submit_flags_task',
            'schedule': period,
        },
    }
    return celery
