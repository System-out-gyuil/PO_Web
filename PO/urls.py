from django.contrib import admin
from django.urls import path, include
from main.views import MainView, SearchResultView
from counsel.views import CounselFormView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', MainView.as_view(), name='main'),
    path("admin/", admin.site.urls),
    path('search/', SearchResultView.as_view(), name='search_result'),
    path('counsel/', include('counsel.urls')),
    path('po_admin/', include('po_admin.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)