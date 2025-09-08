from django.views import View
from django.shortcuts import render

class RecommendTestView(View):
  def get(self, request):
    return render(request, 'diary/recommend_test.html') 
