from django.db import models
import random

# Create your models here.

def random_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default=random_color)
    def __str__(self):
        return self.name

class Region(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class SalesStatus(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default=random_color)
    def __str__(self):
        return self.name

class DiaryEntry(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, default='')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries')
    subregion = models.CharField(max_length=50, blank=True, null=True, default='')
    address = models.CharField(max_length=200, blank=True, null=True, default='')
    manager = models.CharField(max_length=50, blank=True, null=True, default='')
    phone = models.CharField(max_length=20, blank=True, null=True, default='')
    email = models.EmailField(blank=True, null=True, default='')
    ta_date = models.DateField(null=True, blank=True)
    meeting_date = models.DateField(null=True, blank=True)
    fu_date = models.DateField(null=True, blank=True)
    status = models.ForeignKey(SalesStatus, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries')
    possibility = models.CharField(max_length=10, blank=True, null=True, default='')
    amount = models.CharField(max_length=20, blank=True, null=True, default='')
    memo = models.TextField(blank=True, null=True, default='')
    order = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name