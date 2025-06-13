from django.db import models

class AdminMember(models.Model):
    member_id = models.CharField(max_length=100)
    member_pw = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.member_id


class CustUser(models.Model):
    company_name = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    region_detail = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField()
    employee_count = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    sales_for_year = models.CharField(max_length=100)
    export_experience = models.CharField(max_length=100)
    job_description = models.TextField()
    possible_product = models.TextField()
    alarm = models.DateField(null=True, blank=True)

    # ✅ FK 설정: 자동 증가하는 AdminMember의 id 참조
    admin_member_id = models.ForeignKey(AdminMember, on_delete=models.CASCADE, default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name
