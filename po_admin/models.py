from django.db import models

# Create your models here.

class CustUser(models.Model):
    company_name = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    start_date = models.DateField()
    employee_count = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    sales_for_year = models.CharField(max_length=100)
    export_experience = models.CharField(max_length=100)
    job_description = models.TextField()
    possible_product = models.TextField()
    alarm = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


