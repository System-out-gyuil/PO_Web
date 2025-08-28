from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from diary.models import User


class Command(BaseCommand):
    help = '만료 알림 대상 사용자를 테스트합니다.'

    def handle(self, *args, **options):
        # 현재 시간
        now = timezone.now()
        
        # 2일 후
        two_days_later = now + timedelta(days=2)
        one_hour_before = two_days_later - timedelta(hours=1)
        one_hour_after = two_days_later + timedelta(hours=1)
        
        self.stdout.write(f'현재 시간: {now}')
        self.stdout.write(f'2일 후: {two_days_later}')
        self.stdout.write(f'검색 범위: {one_hour_before} ~ {one_hour_after}')
        
        # 조건에 맞는 사용자들 찾기
        users_to_notify = User.objects.filter(
            use_date__gte=one_hour_before,
            use_date__lte=one_hour_after,
            activate=True,
            phone_number__isnull=False,
            phone_number__gt=''
        )
        
        self.stdout.write(f'\n총 {users_to_notify.count()}명의 사용자가 알림 대상입니다.')
        
        if users_to_notify.exists():
            self.stdout.write('\n알림 대상 사용자 목록:')
            for user in users_to_notify:
                remaining_time = user.use_date - now
                days = remaining_time.days
                hours = remaining_time.seconds // 3600
                minutes = (remaining_time.seconds % 3600) // 60
                
                self.stdout.write(
                    f'- {user.name} ({user.email}): '
                    f'만료일 {user.use_date}, '
                    f'남은 시간 {days}일 {hours}시간 {minutes}분, '
                    f'전화번호 {user.phone_number}'
                )
        else:
            self.stdout.write('\n알림 대상 사용자가 없습니다.')
        
        # 전체 사용자 중 use_date가 설정된 사용자들도 확인
        users_with_use_date = User.objects.filter(
            use_date__isnull=False,
            activate=True
        ).order_by('use_date')
        
        if users_with_use_date.exists():
            self.stdout.write(f'\n전체 {users_with_use_date.count()}명의 사용자가 use_date를 가지고 있습니다:')
            for user in users_with_use_date[:10]:  # 상위 10명만 표시
                remaining_time = user.use_date - now
                if remaining_time.total_seconds() > 0:  # 아직 만료되지 않은 사용자만
                    days = remaining_time.days
                    hours = remaining_time.seconds // 3600
                    minutes = (remaining_time.seconds % 3600) // 60
                    
                    self.stdout.write(
                        f'- {user.name}: 만료일 {user.use_date}, '
                        f'남은 시간 {days}일 {hours}시간 {minutes}분'
                    )
