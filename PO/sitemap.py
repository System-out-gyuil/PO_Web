from django.urls import reverse
from django.contrib.sitemaps import Sitemap

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return [
            'admin',
            'search_result',
            'main',
            'po_admin_login',
            'po_admin_list',
            'counsel_form',
            'thank_you',
            'list',
            ]
    
    def location(self, item):
        return reverse(item)

sitemaps = {
    'static': StaticViewSitemap,
}
