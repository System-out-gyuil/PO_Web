from django.core.management.base import BaseCommand
from diary.models import ClassFormTextElement


class Command(BaseCommand):
    help = 'AI 클래스 폼 텍스트 요소의 기본값을 생성합니다.'

    def handle(self, *args, **options):
        default_texts = [
            {
                'key': 'form.title',
                'text': '법인영업 원데이 클래스',
                'description': '폼 페이지 제목'
            },
            {
                'key': 'form.date',
                'text': '일자 : 2025년 9월 16일(화요일) 15시 ~ 17시',
                'description': '강의 일자 및 시간'
            },
            {
                'key': 'form.location',
                'text': '장소 : 구로디지털단지역 인근 (자세한 주소는 추후 문자 안내), 주차가능',
                'description': '강의 장소'
            },
            {
                'key': 'form.capacity',
                'text': '인원 : 선착순 10명',
                'description': '수강 정원'
            },
            {
                'key': 'form.bank',
                'text': '기업은행 : 074-118859-04-015(주식회사 피오코퍼레이션)',
                'description': '입금 계좌 정보'
            },
            {
                'key': 'form.fee',
                'text': '강의료 : 5만원',
                'description': '강의료 안내'
            },
            {
                'key': 'form.notice',
                'text': '신청서 접수 후 입금완료시, 클래스 참여 확정됩니다.',
                'description': '신청 안내 문구'
            },
            {
                'key': 'form.label_name',
                'text': '참석자 성함을 알려주세요',
                'description': '이름 입력 필드 라벨'
            },
            {
                'key': 'form.placeholder_name',
                'text': '이름을 입력해주세요',
                'description': '이름 입력 필드 placeholder'
            },
            {
                'key': 'form.label_phone',
                'text': '참석자 연락처를 알려주세요',
                'description': '연락처 입력 필드 라벨'
            },
            {
                'key': 'form.placeholder_phone',
                'text': '연락처를 입력해주세요. (예: 01012341234, 010-1234-1234, 010 1234 1234)',
                'description': '연락처 입력 필드 placeholder'
            },
            {
                'key': 'form.phone_description',
                'text': '연락처로 강의 관련 안내사항을 전달드립니다.',
                'description': '연락처 입력 필드 안내 문구'
            },
            {
                'key': 'form.button_text',
                'text': '클래스 신청하기',
                'description': '제출 버튼 텍스트'
            },
        ]

        created_count = 0
        updated_count = 0

        for data in default_texts:
            element, created = ClassFormTextElement.objects.update_or_create(
                key=data['key'],
                defaults={
                    'text': data['text'],
                    'description': data['description']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 생성됨: {data["key"]}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ 업데이트됨: {data["key"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n완료! 생성: {created_count}개, 업데이트: {updated_count}개'
            )
        )

