from django.shortcuts import render
from django.views import View
from .models import User, Diary_main_count, DailyViewRecord
from django.utils import timezone
from datetime import date

class DiaryMainView(View):
    def get(self, request):
        # IP 주소 가져오기
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # IP 카운트 업데이트
        try:
            current_date = timezone.now().date()
            
            # 기존 IP 카운트 업데이트
            ip_count, created = Diary_main_count.objects.get_or_create(
                ip=ip,
                defaults={'count': 1}
            )
            if not created:
                ip_count.count += 1
                ip_count.updated_at = timezone.now()
                ip_count.save()
            
            # 일별 상세 기록 추가
            daily_record, created = DailyViewRecord.objects.get_or_create(
                ip=ip,
                date=current_date,
                page_type='main',
                defaults={'count': 1}
            )
            if not created:
                daily_record.count += 1
                daily_record.save()
                
        except Exception as e:
            # 에러 발생 시 로그 기록 (선택사항)
            print(f"IP 카운트 업데이트 중 오류 발생: {e}")
        
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
    