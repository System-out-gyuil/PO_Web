from django.db import models

# Create your models here.
class Industry(models.Model):
    big_category = models.CharField(max_length=100)
    small_category = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.big_category} - {self.small_category}"
