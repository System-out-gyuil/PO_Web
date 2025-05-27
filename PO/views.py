from django.http import HttpResponse
from django.views import View

class Ads(View):
    def get(self, request):
      return HttpResponse("google.com, pub-6882409851484122, DIRECT, f08c47fec0942fa0")