from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from apps.core.admin import admin_site

def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('admin/', admin_site.urls),
    path('health/', health_check, name='health_check'),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/github/', include('apps.github.urls')),
    path('api/agents/', include('apps.agents.urls')),
    path('api/analysis/', include('apps.analysis.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)