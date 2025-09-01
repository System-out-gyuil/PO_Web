from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from diary.models import User
from diary.solapi import solapi_api


class Command(BaseCommand):
    help = '사용 기간이 당일 만료되는 사용자에게 만료 알림 SMS를 발송합니다.'

    def handle(self, *args, **options):
        # 현재 날짜 (시간 제외)
        now = timezone.now()
        today = now.date()
        
        # 당일 만료되는 사용자들을 찾습니다 (날짜만으로 계산)
        # use_date가 오늘 날짜인 사용자
        users_to_notify = User.objects.filter(
            use_date__date=today,  # 당일 만료 날짜
            activate=True,  # 활성화된 사용자만
            phone_number__isnull=False,  # 전화번호가 있는 사용자만
            phone_number__gt=''  # 전화번호가 비어있지 않은 사용자만
        )
        
        # 디버깅 정보 출력
        self.stdout.write(f'현재 시간: {now}')
        self.stdout.write(f'오늘 날짜: {today}')
        self.stdout.write(f'검색 조건: use_date의 날짜 = {today}')
        
        # 전체 사용자 중 use_date가 설정된 사용자 수 확인
        total_users_with_use_date = User.objects.filter(
            use_date__isnull=False,
            activate=True
        ).count()
        self.stdout.write(f'전체 활성화된 사용자 중 use_date 설정된 사용자: {total_users_with_use_date}명')
        
        # 조건별 사용자 수 확인 (날짜 기준)
        users_2days_left = User.objects.filter(
            use_date__date=today + timedelta(days=2),
            activate=True
        ).count()
        users_1day_left = User.objects.filter(
            use_date__date=today + timedelta(days=1),
            activate=True
        ).count()
        users_today = User.objects.filter(
            use_date__date=today,
            activate=True
        ).count()
        users_with_phone = User.objects.filter(
            phone_number__isnull=False,
            phone_number__gt='',
            activate=True
        ).count()
        
        self.stdout.write(f'당일 만료 사용자: {users_today}명')
        self.stdout.write(f'전화번호 있는 사용자: {users_with_phone}명')
        
        self.stdout.write(f'\n총 {users_to_notify.count()}명의 사용자에게 알림을 발송합니다.')
        
        success_count = 0
        fail_count = 0
        
        for user in users_to_notify:
            try:
                # SMS 발송
                solapi_api("use_date_over_today", user.phone_number)
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'사용자 {user.name}({user.email})에게 만료 알림 발송 성공'
                    )
                )
            except Exception as e:
                fail_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'사용자 {user.name}({user.email})에게 만료 알림 발송 실패: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'알림 발송 완료: 성공 {success_count}건, 실패 {fail_count}건'
            )
        )
