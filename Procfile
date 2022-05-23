release: python manage.py migrate
web: daphne -b 0.0.0.0 -p $PORT auto_chess.asgi:application
worker: celery -A auto_chess worker --beat --scheduler django --loglevel=info
