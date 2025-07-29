from django.shortcuts import render
from django.views import View
from .models import User

class DiaryMainView(View):
    def get(self, request):
        is_authenticated = request.session.get('diary_authenticated', False)
        
        if is_authenticated:
            user = User.objects.get(id=request.session['diary_member_id'])
            is_admin = user.is_admin
        else:
            is_admin = False

        return render(request, 'diary/diary_main.html', {'is_authenticated': is_authenticated, 'is_admin': is_admin})
    
class CompanyInfoView(View):
    def get(self, request):
        return render(request, 'diary/company_info.html')
    
class PersonalInfoView(View):
    def get(self, request):
        return render(request, 'diary/personal_info.html')
    
class TermsOfServiceView(View):
    def get(self, request):
        return render(request, 'diary/terms_of_service.html')
    