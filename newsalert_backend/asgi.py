import os
from dotenv import load_dotenv  # ✅ Add this line

load_dotenv()  # ✅ Load .env before getting ASGI app

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import news.routing  # your app's routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsalert_backend.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            news.routing.websocket_urlpatterns
        )
    ),
})
