from django.urls import path
from .views import SearchView, SearchResultView, search_industry

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('result/', SearchResultView.as_view(), name='search_result'),
    path("industry/", search_industry, name="search_industry"),

]
