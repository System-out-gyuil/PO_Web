from django.urls import path
from .views import SearchView, SearchResultView, search_industry, SearchAIResultView

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('ai-result/', SearchAIResultView.as_view(), name='search_ai_result'),
    path('result/', SearchResultView.as_view(), name='search_result'),
    path("industry/", search_industry, name="search_industry"),

]
