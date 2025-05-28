from django.urls import path
from .views import SearchView, SearchResultView, search_industry, SearchAIResultView, SearchIndustryAPIView

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('ai-result/', SearchAIResultView.as_view(), name='search_ai_result'),
    path('result/', SearchResultView.as_view(), name='search_result'),
    path("industry/", search_industry, name="search_industry"),
    path("industry-api/", SearchIndustryAPIView.as_view(), name="search_industry_api"),
]
