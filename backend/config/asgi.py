import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Plain ASGI application for now. Step 8 (real-time alerts) will wrap this
# with Django Channels' ProtocolTypeRouter to add a WebSocket path.
application = get_asgi_application()
