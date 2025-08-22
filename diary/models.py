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
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['created_at']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return self.name
    
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
    detail_sort_order = models.IntegerField(default=0, db_index=True)  # 상세보기 모달에서의 순서
    view_select = models.JSONField(default=dict)
    cascade = models.BooleanField(default=False)
    width = models.IntegerField(default=180)

    class Meta:
        ordering = ['sort_order', 'id']  # sort_order 필드로 기본 정렬
        indexes = [
            models.Index(fields=['user', 'sort_order']),
            models.Index(fields=['user', 'name']),
            models.Index(fields=['user', 'detail']),
            models.Index(fields=['attributeType', 'name']),
        ]

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


class KanbanSettings(models.Model):
    """칸반보드 설정을 위한 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kanban_settings')
    settings = models.JSONField(default=dict)  # {main_attr: str, filters: [...], custom_rules: [...]}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user']  # 사용자당 하나의 설정만 허용
        verbose_name = '칸반보드 설정'
        verbose_name_plural = '칸반보드 설정'

    def __str__(self):
        return f"{self.user.name}의 칸반보드 설정"
    
class Row(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # 원본 행 ID들 (복제된 행인 경우, 복제 체인을 추적)
    original_row_ids = models.JSONField(default=list, blank=True)
    # 복제된 행들의 ID 목록 (원본 행인 경우)
    copied_row_ids = models.JSONField(default=list, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'order']),
            models.Index(fields=['user', 'created_at']),
        ]
    
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
    
    class Meta:
        indexes = [
            models.Index(fields=['row', 'attribute']),
            models.Index(fields=['attribute', 'row']),
        ]
    
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
        indexes = [
            models.Index(fields=['attribute', 'order']),
            models.Index(fields=['attribute', 'id']),
        ]

    def __str__(self):
        return self.option
    


class Inquiry(models.Model):
    """문의 테이블 모델"""
    name = models.CharField(max_length=50, blank=True, null=True, default='')
    company_name = models.CharField(max_length=50, blank=True, null=True, default='')
    contact = models.CharField(max_length=50, blank=True, null=True, default='')
    content = models.TextField(blank=True, null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '문의'
        verbose_name_plural = '문의'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.company_name} ({self.created_at.strftime('%Y-%m-%d')})"
    
class Alarm(models.Model):
    title = models.CharField(max_length=100, db_collation='utf8mb4_unicode_ci')
    content = models.JSONField(default=dict)  # dict 형태로 저장: {"text": "...", "files": [...]}
    category = models.ForeignKey('AlarmCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='alarms')  # 카테고리 추가
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diary_alarm'
        verbose_name = '공지사항'
        verbose_name_plural = '공지사항'
        ordering = ['-created_at']  # 최신순 정렬 추가
        indexes = [
            models.Index(fields=['category', '-created_at']),  # 카테고리별 인덱스 추가
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_text_content(self):
        """텍스트 내용 반환"""
        return self.content.get('text', '')
    
    def get_files(self):
        """파일 목록 반환"""
        return self.content.get('files', [])
    
    def set_content(self, text, files=None):
        """내용 설정"""
        self.content = {
            'text': text,
            'files': files or []
        }
        self.save()
    
    def get_category_name(self):
        """카테고리명 반환"""
        return self.category.category_name if self.category else '일반'

class AlarmCategory(models.Model):
    """공지사항 카테고리 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alarm_categories')
    category_name = models.CharField(max_length=50, db_collation='utf8mb4_unicode_ci')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diary_alarm_category'
        verbose_name = '공지사항 카테고리'
        verbose_name_plural = '공지사항 카테고리'
        unique_together = ['user', 'category_name']  # 사용자별로 카테고리명 중복 방지
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['user', 'category_name']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.category_name}"

class UserAlarm(models.Model):
    """사용자별 알람 확인 상태를 관리하는 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_alarms')
    alarm = models.ForeignKey(Alarm, on_delete=models.CASCADE, related_name='user_alarms')
    is_read = models.BooleanField(default=False)  # 알람을 읽었는지 여부
    read_at = models.DateTimeField(null=True, blank=True)  # 읽은 시간
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'alarm']  # 사용자당 같은 알람은 하나만
        verbose_name = '사용자 알람'
        verbose_name_plural = '사용자 알람'
    
    def __str__(self):
        return f"{self.user.name} - {self.alarm.title}"
    
    def mark_as_read(self):
        """알람을 읽음 상태로 표시"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    

class NomalBoardCategory(models.Model):
    """게시판 카테고리 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='board_categories')
    category_name = models.CharField(max_length=50, db_collation='utf8mb4_unicode_ci')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'nomal_diary_board_category'
        verbose_name = '게시판 카테고리'
        verbose_name_plural = '게시판 카테고리'
        unique_together = ['user', 'category_name']  # 사용자별로 카테고리명 중복 방지
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['user', 'category_name']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.category_name}"

class Board(models.Model):
    """게시판 모델"""
    title = models.CharField(max_length=200, db_collation='utf8mb4_unicode_ci')
    content = models.TextField(db_collation='utf8mb4_unicode_ci')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    category = models.ForeignKey(NomalBoardCategory, on_delete=models.CASCADE, related_name='boards', null=True, blank=True)  # FK로 변경
    files = models.JSONField(default=list, blank=True)  # 첨부파일 정보 저장
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diary_board'
        verbose_name = '게시판'
        verbose_name_plural = '게시판'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['category', '-created_at']),  # 카테고리별 인덱스 추가
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_file_count(self):
        """첨부파일 개수 반환"""
        return len(self.files) if self.files else 0
    
    def get_content_preview(self, length=300):
        """내용 미리보기 반환"""
        if len(self.content) > length:
            return self.content[:length] + '...'
        return self.content
    
    def get_category_name(self):
        """카테고리명 반환"""
        return self.category.category_name if self.category else '일반'


class BoardFile(models.Model):
    """게시판 첨부파일 모델"""
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='board_files')
    original_name = models.CharField(max_length=255, db_collation='utf8mb4_unicode_ci')
    saved_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    s3_key = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'diary_board_file'
        verbose_name = '게시판 첨부파일'
        verbose_name_plural = '게시판 첨부파일'
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"{self.board.title} - {self.original_name}"
    
class Diary_main_count(models.Model):
    ip = models.CharField(max_length=50)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ip']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.ip} - {self.count}"


    
class Diary_diary_count(models.Model):
    ip = models.CharField(max_length=50)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ip']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.ip} - {self.count}"


class DailyViewRecord(models.Model):
    """일별 조회수 상세 기록"""
    ip = models.CharField(max_length=50)
    date = models.DateField()  # 접속한 날짜
    count = models.IntegerField(default=1)  # 해당 날짜의 접속 횟수
    page_type = models.CharField(max_length=20, choices=[
        ('main', '메인 페이지'),
        ('diary', '다이어리 페이지')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ip', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['page_type']),
        ]
        unique_together = ['ip', 'date', 'page_type']  # IP, 날짜, 페이지 타입 조합으로 중복 방지
    
    def __str__(self):
        return f"{self.ip} - {self.date} - {self.page_type} ({self.count}회)"

class ClassForm(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.phone}"


class CountUser(models.Model):
    name = models.CharField(max_length=50)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.count}"
        
