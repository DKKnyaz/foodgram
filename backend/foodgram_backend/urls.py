"""Главный диспетчер путей всего проекта Foodgram."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from recipes.views import RedirectShortLinkView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        's/<str:short_id>/',
        RedirectShortLinkView.as_view(),
        name='short_link_redirect'
    ),
    path('api/', include([
        path('', include('users.urls')),
        path('', include('recipes.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
