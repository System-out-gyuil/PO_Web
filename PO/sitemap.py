from django.urls import reverse
from django.contrib.sitemaps import Sitemap
from board.models import BizInfo
from django.contrib.sites.models import Site

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
    limit = 1000  # ✅ sitemap을 1000개 단위로 자동 분할

    def items(self):
        return BizInfo.objects.all()

    def location(self, obj):
        return reverse('board:detail', args=[obj.pblanc_id])

    def get_urls(self, site=None, **kwargs):
        # ✅ 도메인을 명시적으로 지정해 example.com 문제 방지
        if not site:
            site = Site(domain="namatji.com", name="나맞지")
        return super().get_urls(site=site, **kwargs)


# sitemap dict
sitemaps = {
    'static': StaticViewSitemap,
    'bizinfo': BizInfoSitemap,
}
