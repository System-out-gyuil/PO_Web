from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from diary.models import User

class Command(BaseCommand):
    help = '기존 사용자들의 use_date를 설정합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='사용 기간을 일 단위로 설정 (기본값: 30일)'
        )
        parser.add_argument(
            '--from-created',
            action='store_true',
            help='생성일로부터 계산하여 설정'
        )

    def handle(self, *args, **options):
        days = options['days']
        from_created = options['from_created']
        
        # use_date가 설정되지 않은 사용자들 조회
        users_without_expiry = User.objects.filter(use_date__isnull=True)
        
        if not users_without_expiry.exists():
            self.stdout.write(
                self.style.SUCCESS('모든 사용자의 use_date가 이미 설정되어 있습니다.')
            )
            return
        
        updated_count = 0
        
        for user in users_without_expiry:
            if from_created:
                # 생성일로부터 계산
                expiry_date = user.created_at + timedelta(days=days)
            else:
                # 현재 시간으로부터 계산
                expiry_date = timezone.now() + timedelta(days=days)
            
            user.use_date = expiry_date
            user.save()
            updated_count += 1
            
            self.stdout.write(
                f'사용자 {user.email}의 만료일을 {expiry_date.strftime("%Y-%m-%d %H:%M")}로 설정했습니다.'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'총 {updated_count}명의 사용자 use_date를 설정했습니다.')
        ) 