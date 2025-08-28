from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from diary.models import User
from diary.solapi import solapi_api


class Command(BaseCommand):
    help = '사용 기간이 2일 남은 사용자에게 만료 알림 SMS를 발송합니다.'

    def handle(self, *args, **options):
        # 현재 시간
        now = timezone.now()
        
        # 2일 남은 사용자들을 찾습니다
        # use_date가 현재 시간으로부터 2일 후에 만료되는 사용자
        # 정확히 2일 남은 시점을 찾기 위해 2일 전후 1시간 범위로 설정
        two_days_later = now + timedelta(days=2)
        one_hour_before = two_days_later - timedelta(hours=1)
        one_hour_after = two_days_later + timedelta(hours=1)
        
        users_to_notify = User.objects.filter(
            use_date__gte=one_hour_before,
            use_date__lte=one_hour_after,
            activate=True,  # 활성화된 사용자만
            phone_number__isnull=False,  # 전화번호가 있는 사용자만
            phone_number__gt=''  # 전화번호가 비어있지 않은 사용자만
        )
        
        self.stdout.write(f'총 {users_to_notify.count()}명의 사용자에게 알림을 발송합니다.')
        
        success_count = 0
        fail_count = 0
        
        for user in users_to_notify:
            try:
                # SMS 발송
                solapi_api("use_date_over", user.phone_number)
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
