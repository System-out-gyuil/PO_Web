from django.core.management.base import BaseCommand
from diary.models import AIClassTextElement

class Command(BaseCommand):
    help = 'AI 클래스 페이지의 기본 텍스트 요소들을 생성합니다.'

    def handle(self, *args, **options):
        # 기본 텍스트 요소들 정의
        default_elements = [
            # 메인 헤로 섹션
            {
                'key': 'badge_text',
                'text': '🔥 월 천만원 목표! 선착순 10명 한정',
                'description': '메인 배지 텍스트'
            },
            {
                'key': 'money_highlight',
                'text': '월 천만원',
                'description': '강조할 금액 텍스트'
            },
            {
                'key': 'main_title_1',
                'text': '법인영업',
                'description': '메인 제목 1번째 줄'
            },
            {
                'key': 'main_title_2',
                'text': 'AI와 함께라면',
                'description': '메인 제목 2번째 줄'
            },
            {
                'key': 'main_title_3',
                'text': '당신도 가능합니다',
                'description': '메인 제목 3번째 줄'
            },
            {
                'key': 'sub_headline_mobile_1',
                'text': '시야·시도·경험 부족으로 포기했던 법인영업',
                'description': '모바일 서브 헤드라인 1번째 줄'
            },
            {
                'key': 'sub_headline_mobile_2',
                'text': '이제 AI 시스템과 10년 전문가가',
                'description': '모바일 서브 헤드라인 2번째 줄'
            },
            {
                'key': 'sub_headline_mobile_3',
                'text': '당신의 고수익을 현실로 만듭니다',
                'description': '모바일 서브 헤드라인 3번째 줄'
            },
            {
                'key': 'sub_headline_desktop',
                'text': '시야·시도·경험 부족으로 포기했던 법인영업<br />이제 AI 시스템과 10년 전문가가 당신의 고수익을 현실로 만듭니다',
                'description': '데스크톱 서브 헤드라인'
            },
            {
                'key': 'ai_name_1',
                'text': '나맞지 AI',
                'description': '첫 번째 AI 이름'
            },
            {
                'key': 'ai_desc_1',
                'text': '맞춤 지원사업 추천',
                'description': '첫 번째 AI 설명'
            },
            {
                'key': 'ai_name_2',
                'text': '자금왕 AI',
                'description': '두 번째 AI 이름'
            },
            {
                'key': 'ai_desc_2',
                'text': '자금 한도 + CRM 영업관리',
                'description': '두 번째 AI 설명'
            },
            
            # 통계 섹션
            {
                'key': 'stats_title',
                'text': '당신은 지금 얼마를 벌고 있습니까?',
                'description': '통계 섹션 제목'
            },
            {
                'key': 'current_income',
                'text': '월 200만원',
                'description': '현재 평균 수입'
            },
            {
                'key': 'current_income_desc',
                'text': '현재 평균 수입',
                'description': '현재 수입 설명'
            },
            {
                'key': 'target_income',
                'text': '월 1,000만원',
                'description': '목표 수입'
            },
            {
                'key': 'target_income_desc',
                'text': '법인영업 고수익',
                'description': '목표 수입 설명'
            },
            {
                'key': 'comparison_title',
                'text': '같은 시간 투자, 5배 다른 결과',
                'description': '비교 제목'
            },
            {
                'key': 'comparison_desc',
                'text': '이제 꿈이 아닌 현실로 만들 차례입니다',
                'description': '비교 설명'
            },
            
            # 경험 섹션
            {
                'key': 'experience_1_mobile',
                'text': '이론만 배우고,<br />실전은 막막하셨나요?',
                'description': '모바일 경험 1'
            },
            {
                'key': 'experience_1_desktop',
                'text': '이론만 배우고, 실전은 막막하셨나요?',
                'description': '데스크톱 경험 1'
            },
            {
                'key': 'experience_2_mobile',
                'text': '시간과 돈을 썼지만,<br />제자리걸음이었나요?',
                'description': '모바일 경험 2'
            },
            {
                'key': 'experience_2_desktop',
                'text': '시간과 돈을 썼지만, 제자리걸음이었나요?',
                'description': '데스크톱 경험 2'
            },
            {
                'key': 'experience_3_mobile',
                'text': '정책자금,<br />결국 혼자서는 어렵다고 느끼셨나요?',
                'description': '모바일 경험 3'
            },
            {
                'key': 'experience_3_desktop',
                'text': '정책자금, 결국 혼자서는 어렵다고 느끼셨나요?',
                'description': '데스크톱 경험 3'
            },
            
            # 3가지 벽 섹션
            {
                'key': 'barriers_title',
                'text': '월 천만원을 가로막는 3가지 벽',
                'description': '벽 섹션 제목'
            },
            {
                'key': 'barriers_desc_mobile',
                'text': '대부분이 고수익 법인영업에 실패하는 이유를 명확히 파악하고,<br />그 해결책을 제시합니다',
                'description': '모바일 벽 섹션 설명'
            },
            {
                'key': 'barriers_desc_desktop',
                'text': '대부분이 고수익 법인영업에 실패하는 이유를 명확히 파악하고, 그 해결책을 제시합니다',
                'description': '데스크톱 벽 섹션 설명'
            },
            {
                'key': 'barrier_1_title',
                'text': '시야의 부족 - 보이지 않는 기회',
                'description': '첫 번째 벽 제목'
            },
            {
                'key': 'barrier_1_desc_mobile',
                'text': '월 천만원을 벌 수 있는 <br />법인영업의 황금 기회가 있다는 것 자체를 모릅니다.<br /><br />정책자금 법인영업이라는 고수익 분야가 <br />존재한다는 것조차 모르는 분들이 대부분입니다. <br />경험이 없으니 기회가 보여도 그게 기회인지 판단할 수 없죠. <br /><span class="wmr-highlight">혼자서는 절대 극복하기 어려운 영역</span>입니다.',
                'description': '모바일 첫 번째 벽 설명'
            },
            {
                'key': 'barrier_1_desc_desktop',
                'text': '"월 천만원을 벌 수 있는 법인영업의 황금 기회가 있다는 것 자체를 모릅니다."<br /><br />정책자금 법인영업이라는 고수익 분야가 존재한다는 것조차 모르는 분들이 대부분입니다. 경험이 없으니 기회가 보여도 그게 기회인지 판단할 수 없죠. <br /><span class="wmr-highlight">혼자서는 절대 극복하기 어려운 영역</span>입니다.',
                'description': '데스크톱 첫 번째 벽 설명'
            },
            {
                'key': 'barrier_2_title',
                'text': '시도의 부족 - 막연한 두려움',
                'description': '두 번째 벽 제목'
            },
            {
                'key': 'barrier_2_desc_mobile',
                'text': '돈 되는 방법은 알지만,<br />어디서부터 시작해야 할지 몰라 미루기만 합니다.<br /><br />정책자금이 있다는 건 알지만<br />복잡해 보이고, 어려워 보여서 시작을 못하는 경우입니다. <br />첫걸음이 가장 어렵죠.<br />하지만 <span class="wmr-highlight">방법만 명확히 알면 즉시 실행</span> 가능합니다.',
                'description': '모바일 두 번째 벽 설명'
            },
            {
                'key': 'barrier_2_desc_desktop',
                'text': '"돈 되는 방법은 알지만, 어디서부터 시작해야 할지 몰라 미루기만 합니다."<br /><br />정책자금이 있다는 건 알지만<br />복잡해 보이고, 어려워 보여서 시작을 못하는 경우입니다. 첫걸음이 가장 어렵죠.<br />하지만 <span class="wmr-highlight">방법만 명확히 알면 즉시 실행</span> 가능합니다.',
                'description': '데스크톱 두 번째 벽 설명'
            },
            {
                'key': 'barrier_3_title',
                'text': '경험의 부족 - 끝없는 시행착오',
                'description': '세 번째 벽 제목'
            },
            {
                'key': 'barrier_3_desc_mobile',
                'text': '성공하는 법인영업은 <br />수많은 경험과 노하우의 집약체입니다.<br /><br />시도는 해봤지만 <br />시행착오를 반복하며 포기하는 경우가 많습니다.<br />혼자서 시행착오를 겪다 보면 시간과 비용만 낭비됩니다.<br />검증된 경험을 통해 <br /><span class="wmr-highlight">2-3년 걸릴 과정을 2-3개월로 단축</span>시켜 드립니다.',
                'description': '모바일 세 번째 벽 설명'
            },
            {
                'key': 'barrier_3_desc_desktop',
                'text': '"성공하는 법인영업은 수많은 경험과 노하우의 집약체입니다."<br /><br />시도는 해봤지만 시행착오를 반복하며 포기하는 경우가 많습니다.<br />혼자서 시행착오를 겪다 보면 시간과 비용만 낭비됩니다.<br />검증된 경험을 통해 <span class="wmr-highlight">2-3년 걸릴 과정을 2-3개월로 단축</span>시켜 드립니다.',
                'description': '데스크톱 세 번째 벽 설명'
            },
            
            # CTA 버튼
            {
                'key': 'cta_button_1',
                'text': '지금 신청하고 월 천만원의 길 열기 ▶',
                'description': '첫 번째 CTA 버튼'
            },
            
            # 혜택 섹션
            {
                'key': 'benefits_title',
                'text': '단 3시간, 월 수익을 뒤바꿀 핵심 가치',
                'description': '혜택 섹션 제목'
            },
            {
                'key': 'benefits_desc_mobile',
                'text': '이론이 아닌 실제 고수익 달성!<br />추상적 개념이 아닌 구체적이고 압도적인 성과를 약속합니다',
                'description': '모바일 혜택 섹션 설명'
            },
            {
                'key': 'benefits_desc_desktop',
                'text': '이론이 아닌 실제 고수익 달성! 추상적 개념이 아닌 구체적이고 압도적인 성과를 약속합니다',
                'description': '데스크톱 혜택 섹션 설명'
            },
            {
                'key': 'benefit_1_title',
                'text': '월 천만원 실제 성공 사례 전격 공개',
                'description': '첫 번째 혜택 제목'
            },
            {
                'key': 'benefit_1_desc',
                'text': '1인 기업부터 보험 영업직까지,<br />실제로 월 천만원 이상을 달성한 생생한 고수익 사례와<br />그들의 전략을 투명하게 공개합니다.',
                'description': '첫 번째 혜택 설명'
            },
            {
                'key': 'benefit_2_title',
                'text': '나맞지 AI: 맞춤 지원사업 추천 시연',
                'description': '두 번째 혜택 제목'
            },
            {
                'key': 'benefit_2_desc',
                'text': 'AI가 5분 만에 우리 회사에 딱 맞는 정책자금을 찾아주는<br />나맞지 AI를 직접 체험해보세요. <br /><span class="wmr-highlight">기존 2-3일 걸리던 탐색 시간을 황금 시간으로 바꿉니다.</span>',
                'description': '두 번째 혜택 설명'
            },
            {
                'key': 'benefit_3_title',
                'text': '자금왕 AI: 자금 한도 & CRM 관리',
                'description': '세 번째 혜택 제목'
            },
            {
                'key': 'benefit_3_desc',
                'text': 'AI가 정확한 자금 한도를 계산하고, 고객사와의 접점을<br />지속적으로 유지하는 자금왕 CRM을 보여드립니다. <br /><span class="wmr-highlight">스마트한 영업관리로 수익을 극대화하세요.</span>',
                'description': '세 번째 혜택 설명'
            },
            {
                'key': 'benefit_4_title',
                'text': '30일 고수익 실행 액션플랜 제공',
                'description': '네 번째 혜택 제목'
            },
            {
                'key': 'benefit_4_desc',
                'text': '강의 후 즉시 월 천만원을 향한 첫 발을 뗄 수 있는<br />체계적인 30일 로드맵과 체크리스트를 드립니다.<br /><span class="wmr-highlight">망설임 없는 고속 성장을 시작하세요.</span>',
                'description': '네 번째 혜택 설명'
            },
            
            # AI 툴 섹션
            {
                'key': 'ai_tools_title_mobile',
                'text': '차원이 다른 AI 시스템,<br />미리 경험하세요',
                'description': '모바일 AI 툴 섹션 제목'
            },
            {
                'key': 'ai_tools_title_desktop',
                'text': '차원이 다른 AI 시스템, 미리 경험하세요',
                'description': '데스크톱 AI 툴 섹션 제목'
            },
            {
                'key': 'ai_tools_desc_mobile',
                'text': '다른 강의에서는 꿈도 못 꿀,<br />실제 월 천만원을 만드는 AI 툴을 직접 시연합니다',
                'description': '모바일 AI 툴 섹션 설명'
            },
            {
                'key': 'ai_tools_desc_desktop',
                'text': '다른 강의에서는 꿈도 못 꿀, 실제 월 천만원을 만드는 AI 툴을 직접 시연합니다',
                'description': '데스크톱 AI 툴 섹션 설명'
            },
            
            # 강사 소개 섹션
            {
                'key': 'instructor_title_mobile',
                'text': '월 천만원 고수익,<br />검증된 전문가와 함께하세요',
                'description': '모바일 강사 섹션 제목'
            },
            {
                'key': 'instructor_title_desktop',
                'text': '월 천만원 고수익, 검증된 전문가와 함께하세요',
                'description': '데스크톱 강사 섹션 제목'
            },
            {
                'key': 'instructor_name',
                'text': '오원석',
                'description': '강사 이름'
            },
            {
                'key': 'instructor_title_mobile',
                'text': '10년차 기업 컨설턴트<br />정책자금·지원사업·법인영업 전문가',
                'description': '모바일 강사 직책'
            },
            {
                'key': 'instructor_title_desktop',
                'text': '10년차 기업 컨설턴트 | 정책자금·지원사업·법인영업 전문가',
                'description': '데스크톱 강사 직책'
            },
            {
                'key': 'instructor_desc_mobile',
                'text': '10년 이상 수많은 기업의 <span class="wmr-highlight">정책자금 유치와 <br />법인영업 고수익 성과를 책임져 온 베테랑 컨설턴트</span> <br />나맞지·자금왕 AI 시스템을 직접 개발하여, <br />실제 성공 사례와 검증된 시스템으로 <br />당신의 월 천만원 목표를 <br /><span class="wmr-highlight">가장 빠르고 확실하게 현실로</span> 만들어 드립니다.',
                'description': '모바일 강사 설명'
            },
            {
                'key': 'instructor_desc_desktop',
                'text': '10년 이상 수많은 기업의 <span class="wmr-highlight">정책자금 유치와 법인영업 고수익 성과를 책임져 온 베테랑 컨설턴트</span>입니다.<br />나맞지·자금왕 AI 시스템을 직접 개발하여, 실제 성공 사례와 검증된 시스템으로 <br />당신의 <span class="wmr-highlight">월 천만원 목표를 가장 빠르고 확실하게 현실로</span> 만들어 드립니다.',
                'description': '데스크톱 강사 설명'
            },
            
            # 강의 정보 섹션
            {
                'key': 'class_info_title',
                'text': '월 천만원 고수익을 위한 원데이 클래스 정보',
                'description': '강의 정보 섹션 제목'
            },
            {
                'key': 'class_schedule_title',
                'text': '일정',
                'description': '일정 카드 제목'
            },
            {
                'key': 'class_schedule_desc',
                'text': '9월 16일(화)<br />오후 3시~5시 (2시간)',
                'description': '일정 카드 설명'
            },
            {
                'key': 'class_method_title',
                'text': '진행방식',
                'description': '진행방식 카드 제목'
            },
            {
                'key': 'class_method_desc',
                'text': '대면 강의<br />구로디지털단지역 인근',
                'description': '진행방식 카드 설명'
            },
            {
                'key': 'class_capacity_title',
                'text': '정원',
                'description': '정원 카드 제목'
            },
            {
                'key': 'class_capacity_desc',
                'text': '선착순 10명 한정<br />밀도 높은 Q&A 및 개별 조언',
                'description': '정원 카드 설명'
            },
            {
                'key': 'class_benefit_title',
                'text': '특별혜택',
                'description': '특별혜택 카드 제목'
            },
            {
                'key': 'class_benefit_desc',
                'text': 'AI 법인영업 무료 툴 제공',
                'description': '특별혜택 카드 설명'
            },
            
            # CTA 섹션
            {
                'key': 'cta_headline_mobile',
                'text': '당신의 월 천만원,<br />지금 바로 시작하세요',
                'description': '모바일 CTA 헤드라인'
            },
            {
                'key': 'cta_headline_desktop',
                'text': '당신의 월 천만원, 지금 바로 시작하세요',
                'description': '데스크톱 CTA 헤드라인'
            },
            {
                'key': 'cta_subtext_mobile',
                'text': '월 천만원 법인영업 고수익,<br />더 이상 꿈이 아닙니다. 현실이 됩니다!',
                'description': '모바일 CTA 서브텍스트'
            },
            {
                'key': 'cta_subtext_desktop',
                'text': '월 천만원 법인영업 고수익, 더 이상 꿈이 아닙니다. 현실이 됩니다!',
                'description': '데스크톱 CTA 서브텍스트'
            },
            {
                'key': 'urgency_title_mobile',
                'text': '⚠️ 이 황금 기회를 놓치면<br />안 되는 이유!',
                'description': '모바일 긴급성 제목'
            },
            {
                'key': 'urgency_title_desktop',
                'text': '⚠️ 이 황금 기회를 놓치면 안 되는 이유!',
                'description': '데스크톱 긴급성 제목'
            },
            {
                'key': 'urgency_strong',
                'text': '단 10명만 모집합니다.',
                'description': '긴급성 강조 텍스트'
            },
            {
                'key': 'urgency_desc',
                'text': '밀착 코칭과 압도적 성과를 위한 최적의 인원입니다.<br /><strong>지금 망설이면, 4분기 고수익 시즌을 놓치고 내년까지 기다려야 합니다.</strong><br />선택은 당신의 몫이지만, 이 기회는 당신을 기다려주지 않습니다.',
                'description': '긴급성 설명'
            },
            {
                'key': 'cta_button_2',
                'text': '지금 신청하고 월 천만원의 길 열기 ▶',
                'description': '두 번째 CTA 버튼'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for element_data in default_elements:
            element, created = AIClassTextElement.objects.get_or_create(
                key=element_data['key'],
                defaults={
                    'text': element_data['text'],
                    'description': element_data['description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 생성됨: {element_data["key"]}')
                )
            else:
                # 기존 요소가 있으면 텍스트와 설명 업데이트
                element.text = element_data['text']
                element.description = element_data['description']
                element.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ 업데이트됨: {element_data["key"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n완료! 총 {len(default_elements)}개 요소 중 '
                f'{created_count}개 생성, {updated_count}개 업데이트'
            )
        )
