from django.shortcuts import render
from django.views.generic import View

class BlogView(View):
    def get(self, request):
        return render(request, 'naver_blog/naver_blog.html')

