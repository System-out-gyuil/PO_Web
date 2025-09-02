from django.shortcuts import render
from django.views import View

# Create your views here.
class SalesmateView(View):
    def get(self, request):
        return render(request, 'salesmate/salesmate_main.html')