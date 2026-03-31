"""
URL configuration for helpme_hub project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .stripe_webhooks import stripe_webhook_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhooks/stripe/', stripe_webhook_view, name='stripe_webhook'),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('chats/', include('chats.urls')),
    path('tickets/', include('tickets.urls')),
    path('knowledge/', include('knowledge.urls')),
    path('inventory/', include('inventory.urls')),
    path('', include('audit.urls')),  # Audit logs (includes superadmin prefix)
    path('', include('accounts.urls')),  # Dashboard and other account pages
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


