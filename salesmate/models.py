from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=50, unique=False)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    company_name = models.CharField(max_length=50, blank=True, null=True, default='')
    manager_name = models.CharField(max_length=50, blank=True, null=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    use_date = models.DateTimeField(null=True, blank=True)  # 사용 기간 만료일
    activate = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def is_expired(self):
        """사용 기간이 만료되었는지 확인"""
        from django.utils import timezone
        if self.use_date is None:
            return False
        return timezone.now() > self.use_date
    
    def deactivate_if_expired(self):
        """사용 기간이 만료되면 자동으로 비활성화"""
        if self.is_expired() and self.activate:
            self.activate = False
            self.save()
            return True
        return False

class EmailVerification(models.Model):
    """이메일 인증을 위한 모델"""
    email = models.EmailField()
    verification_code = models.CharField(max_length=6)  # 6자리 인증번호
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 인증번호 만료 시간
    
    class Meta:
        verbose_name = '이메일 인증'
        verbose_name_plural = '이메일 인증'
        indexes = [
            models.Index(fields=['email', 'verification_code']),
            models.Index(fields=['email', 'is_verified']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.verification_code}"
    
    def is_expired(self):
        """인증번호가 만료되었는지 확인"""
        from django.utils import timezone
        return timezone.now() > self.expires_at