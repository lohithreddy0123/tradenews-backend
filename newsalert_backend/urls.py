from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse  # ✅ Required for test route

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: HttpResponse("✅ Backend is running!")),  # Root test route
    path('api/', include('news.urls')),  # App routes mounted here
]
