from django.db import models
import random
import json

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
    
class User(models.Model):
    name = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class AttributeType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class BaseAttribute(models.Model):
    name = models.CharField(max_length=50, unique=True)
    attributeType = models.ForeignKey(AttributeType, on_delete=models.SET_NULL, null=True, blank=True, related_name='base_attributes')
    
    def __str__(self):
        return self.name

class BaseAttributeDetail(models.Model):
    name = models.CharField(max_length=50, unique=True)
    attributeType = models.ForeignKey(AttributeType, on_delete=models.SET_NULL, null=True, blank=True, related_name='base_attribute_details')
    
    def __str__(self):
        return self.name

class Attribute(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attributes')
    attributeType = models.ForeignKey(AttributeType, on_delete=models.SET_NULL, null=True, blank=True, related_name='attributes')
    assential = models.BooleanField(default=False)
    detail = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0, db_index=True)
    view_select = models.JSONField(default=dict)
    cascade = models.BooleanField(default=False)
    width = models.IntegerField(default=150)

    class Meta:
        ordering = ['sort_order', 'id']  # sort_order 필드로 기본 정렬

    def __str__(self):
        return self.name

class CalendarSettings(models.Model):
    """캘린더 설정을 위한 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_settings')
    settings = models.JSONField(default=dict)  # {date_fields: [...], custom_events: [...]}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user']  # 사용자당 하나의 설정만 허용
        verbose_name = '캘린더 설정'
        verbose_name_plural = '캘린더 설정'

    def __str__(self):
        return f"{self.user.name}의 캘린더 설정"

    def get_content_fields_list(self):
        """content_fields를 리스트로 반환"""
        if isinstance(self.content_fields, str):
            try:
                return json.loads(self.content_fields)
            except json.JSONDecodeError:
                return []
        return self.content_fields or []

    def set_content_fields_list(self, fields_list):
        """content_fields를 리스트로 설정"""
        if isinstance(fields_list, list):
            self.content_fields = fields_list
        else:
            self.content_fields = []

    def get_settings_dict(self):
        """설정을 딕셔너리 형태로 반환"""
        return {
            'date_field': self.date_field.name if self.date_field else None,
            'content_fields': self.get_content_fields_list()
        }
    
class Row(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # 원본 행 ID들 (복제된 행인 경우, 복제 체인을 추적)
    original_row_ids = models.JSONField(default=list, blank=True)
    # 복제된 행들의 ID 목록 (원본 행인 경우)
    copied_row_ids = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"Row {self.id} (user={self.user_id}, order={self.order})"
    
    def add_copied_row(self, copied_row_id):
        """복제된 행 ID를 목록에 추가"""
        if copied_row_id not in self.copied_row_ids:
            self.copied_row_ids.append(copied_row_id)
            self.save()
    
    def remove_copied_row(self, copied_row_id):
        """복제된 행 ID를 목록에서 제거"""
        if copied_row_id in self.copied_row_ids:
            self.copied_row_ids.remove(copied_row_id)
            self.save()
    
    def add_original_row(self, original_row_id):
        """원본 행 ID를 목록에 추가"""
        if original_row_id not in self.original_row_ids:
            self.original_row_ids.append(original_row_id)
            self.save()
    
    def get_all_related_rows(self):
        """이 행과 관련된 모든 행들을 반환 (원본 + 복제된 행들)"""
        all_row_ids = set(self.original_row_ids + self.copied_row_ids + [self.id])
        return Row.objects.filter(id__in=all_row_ids)
    
    def get_root_original_row(self):
        """최상위 원본 행을 반환"""
        if not self.original_row_ids:
            return self  # 원본 행인 경우
        # 가장 첫 번째 원본 행을 최상위 원본으로 간주
        return Row.objects.get(id=self.original_row_ids[0])
    
    def get_all_copied_rows(self):
        """이 행에서 복제된 모든 행들을 반환 (직접 + 간접 복제)"""
        all_copied_ids = set()
        to_process = [self.id]
        
        while to_process:
            current_id = to_process.pop(0)
            try:
                current_row = Row.objects.get(id=current_id)
                for copied_id in current_row.copied_row_ids:
                    if copied_id not in all_copied_ids:
                        all_copied_ids.add(copied_id)
                        to_process.append(copied_id)
            except Row.DoesNotExist:
                continue
        
        return Row.objects.filter(id__in=all_copied_ids)

class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.SET_NULL, null=True, blank=True, related_name='values')
    row = models.ForeignKey(Row, on_delete=models.CASCADE, related_name='values', null=True, blank=True)
    value = models.TextField()  # CharField에서 TextField로 변경하여 JSON 저장 가능
    copy_from = models.IntegerField(default=0)
    
    def __str__(self):
        return self.value
    
    def get_file_info(self):
        """파일 타입인 경우 JSON 파싱하여 파일 정보 반환"""
        if self.attribute and self.attribute.attributeType and self.attribute.attributeType.name == 'file':
            try:
                import json
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return None
        return None
    
    def set_file_info(self, file_data):
        """파일 정보를 JSON으로 저장"""
        import json
        self.value = json.dumps(file_data, ensure_ascii=False)
    
class DropdownAttribute(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.SET_NULL, null=True, blank=True, related_name='dropdown_attributes')
    option = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default=random_color)
    order = models.IntegerField(default=0, db_index=True)

    class Meta:
        ordering = ['attribute', 'order', 'id']  # attribute별로 그룹화하고 order로 정렬

    def __str__(self):
        return self.option

    