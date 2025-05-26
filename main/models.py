from django.db import models

# Create your models here.
class Industry(models.Model):
    big_category = models.CharField(max_length=100)
    small_category = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.big_category} - {self.small_category}"

class Count(models.Model):
    COUNT_TYPE_CHOICES = [
        ("main", "메인페이지"),
        ("search", "검색창"),
        ("search_result", "검색결과"),
        ("board", "공고 리스트"),
        ("board_detail", "공고 상세"),
        ("inquiry", "문의페이지"),
    ]

    count_type = models.CharField(max_length=50, choices=COUNT_TYPE_CHOICES, unique=True)
    value = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.count_type} - {self.value}"

class IpAddress(models.Model):
    ip_address = models.CharField(max_length=100)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} - {self.created_at}"

