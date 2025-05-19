from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView
from accounts.views import HomeTestPageView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Inkluderer bedriftsruter
    path('business/', include(('businesses.urls', 'businesses'), namespace='businesses')),
    # Inkluderer giveaways
    path('giveaways/', include(('giveaways.urls', 'giveaways'), namespace='giveaways')),
    # Forside med giveaways-scroll koblet til HomeTestPageView
    path('', HomeTestPageView.as_view(), name='home'),
    # Inkluderer brukerregistrering og andre kontorelaterte ruter
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('member-login', RedirectView.as_view(url='/accounts/member/login/', permanent=True)),
    # Tilgjengelighetsdemonstrasjon
    path('accessibility-demo/', TemplateView.as_view(template_name='accessibility_demo.html'), name='accessibility_demo'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)