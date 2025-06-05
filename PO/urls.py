from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import path, include
from main.views import MainView, TermsOfServiceView, PersonalInfoView, Ads
from counsel.views import CounselFormView
from django.conf import settings
from django.conf.urls.static import static
from .sitemap import sitemaps
from django.contrib.sitemaps.views import sitemap

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', MainView.as_view(), name='main'),
    path('terms_of_service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('personal_info/', PersonalInfoView.as_view(), name='personal_info'),

    path('sitemap.xml', sitemap, {'sitemaps':sitemaps}, name='sitemap'),
    path('ads.txt', Ads.as_view(), name='ads'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),

    path('accounts/', include('allauth.urls')),
    path('board/', include('board.urls')),
    path('counsel/', include('counsel.urls')),
    path('member/', include('member.urls')),
    path('blog/', include('blog.urls')),
    path('po_admin/', include('po_admin.urls')),
    path('search/', include('search.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
