from django.db import models

class Counsel(models.Model):
    company = models.CharField(max_length=100)   # 상호
    phone = models.CharField(max_length=20)      # 연락처
    region = models.CharField(max_length=50)     # 지역
    industry = models.CharField(max_length=50)   # 업종
    start_date = models.CharField(max_length=10) # 사업개시일
    sales_2024 = models.CharField(max_length=30, blank=True, null=True)  # 24년 매출
    sales_2025 = models.CharField(max_length=30, blank=True, null=True)  # 25년 현재매출
    inquiry_type = models.CharField(max_length=50)  # 문의내용
    consent = models.BooleanField(default=False)     # ✅ 개인정보 수집 이용 동의
    consent2 = models.BooleanField(default=False)    # ✅ 제3자 제공 동의
    created_at = models.DateTimeField(auto_now_add=True)  # 접수 일시

    def __str__(self):
        return self.company
