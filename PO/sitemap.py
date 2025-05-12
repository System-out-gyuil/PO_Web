from django.urls import reverse
from django.contrib.sitemaps import Sitemap
from board.models import BizInfo

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return [
            'main',
            'search_result',
            'po_admin_login',
            'po_admin_list',
            'counsel_form',
            'thank_you',
        ]

    def location(self, item):
        return reverse(item)


class BizInfoSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return BizInfo.objects.all()

    def location(self, obj):
        return reverse('board:detail', args=[obj.pblanc_id])


sitemaps = {
    'static': StaticViewSitemap,
    'bizinfo': BizInfoSitemap,
}
