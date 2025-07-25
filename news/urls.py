from django.urls import path
from .views import get_news_for_stock

urlpatterns = [
    path("news/<str:stock_name>/", get_news_for_stock),
]
