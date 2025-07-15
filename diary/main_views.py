from django.shortcuts import render
from django.views import View

class DiaryMainView(View):
    def get(self, request):
        return render(request, 'diary/diary_main.html')