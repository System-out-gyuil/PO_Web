from django.db import models

class BizInfo(models.Model):
    pblanc_id = models.CharField(max_length=50, unique=True)  # 공고 ID (pblancId)
    title = models.CharField(max_length=500)  # 공고명 (pblancNm)
    content = models.TextField()  # 공고 내용 (bsnsSumryCn)
    registered_at = models.DateField(null=True, blank=True)  # 공고 등록일 (creatPnttm)
    reception_start = models.DateField(max_length=200)  # 접수 시작일 (reqstBeginEndDe)
    reception_end = models.DateField(max_length=200)  # 접수 마감일 (reqstBeginEndDe)
    institution_name = models.CharField(max_length=200)  # 기관명 (jrsdInsttNm)
    enroll_method = models.CharField(max_length=500)  # 신청 방법 (reqstMthPapersCn)
    target = models.CharField(max_length=200)  # 대상 (trgetNm)
    field = models.CharField(max_length=200)  # 분야 (pldirSportRealmLclasCodeNm)
    hashtag = models.CharField(max_length=500)  # 해시태그 (hashtags)
    print_file_name = models.CharField(max_length=200)  # 원문 파일명 (printFileNm)
    print_file_path = models.CharField(max_length=200)  # 원문 파일 경로 (printFlpthNm)(다운로드)
    company_hall_path = models.CharField(max_length=200)  # 기업마당 공고원문 경로 (pblancUrl)
    support_field = models.CharField(max_length=200)  # 지원 분야 (pldirSportRealmMlsfcCodeNm)
    application_form_name = models.CharField(max_length=200)  # 신청서 이름 (fileNm)
    application_form_path = models.CharField(max_length=500)  # 신청서 경로 (flpthNm)
    iframe_src = models.URLField(max_length=1000, null=True, blank=True)  # 상세보기 iframe 링크
    employee_count = models.CharField(max_length=50, blank=True, null=True)
    revenue = models.CharField(max_length=100, blank=True, null=True)
    noti_summary = models.TextField(blank=True, null=True)
    business_period = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"[{self.institution_name}] {self.title}"
