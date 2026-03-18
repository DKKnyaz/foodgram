"""Главный диспетчер путей всего проекта Foodgram."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.recipes.views import RedirectShortLinkView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Путь "пустышка" для reverse с фронтом.
    path('recipes/<int:pk>/', lambda r, pk: None, name='recipe-frontend'),
    path(
        's/<str:short_id>/',
        RedirectShortLinkView.as_view(),
        name='short_link_redirect'
    ),
    path('api/', include([
        path('', include('api.users.urls')),
        path('', include('api.recipes.urls')),
    ])),
    path('', lambda r: None, name='index'),  # Главная для redirect с фронтом.
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
