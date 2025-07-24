from django.shortcuts import render
from django.views import View

class DiaryMainView(View):
    def get(self, request):
        is_authenticated = request.session.get('diary_authenticated', False)
        return render(request, 'diary/diary_main.html', {'is_authenticated': is_authenticated})