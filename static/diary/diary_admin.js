// 어드민 페이지 JavaScript

// 전역 변수
let currentInquiryId = null;
let currentAlarmId = null;
let currentUserSort = { field: null, direction: null }; // 정렬이 설정되지 않은 상태
let isSortingInProgress = false; // 정렬 진행 중 플래그
let currentCountType = 'main'; // 현재 조회수 타입 (main 또는 diary)

// 원데이 클래스 신청 목록 로드 (먼저 정의)
async function loadClassForms(page = 1) {
    try {
        const searchQuery = document.getElementById('class-form-search')?.value || '';
        const sortBy = document.getElementById('class-form-sort')?.value || '-created_at';
        
        const params = new URLSearchParams({
            search: searchQuery,
            sort: sortBy,
            page: page
        });
        
        const response = await fetch(`/sales/diary_admin/class_forms/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderClassFormsTable(data.class_forms, page, 10);
            renderPagination(data.pagination, 'class-forms-pagination', loadClassForms);
            updateClassFormsSummary(data.total_count);
        } else {
            showAlert('클래스 신청 목록을 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading class forms:', error);
        showAlert('클래스 신청 목록을 불러오는데 실패했습니다.', 'danger');
    }
}

// 원데이 클래스 신청 테이블 렌더링
function renderClassFormsTable(classForms, currentPage = 1, pageSize = 10) {
    const tbody = document.getElementById('class-forms-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (classForms.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">클래스 신청이 없습니다.</td></tr>';
        return;
    }
    
    classForms.forEach((classForm, index) => {
        const row = document.createElement('tr');
        const displayNumber = (currentPage - 1) * pageSize + (classForms.length - index);
        
        row.innerHTML = `
            <td>${displayNumber}</td>
            <td>${classForm.name}</td>
            <td>${classForm.phone}</td>
            <td>${formatDate(classForm.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteClassForm(${classForm.id})">
                    <i class="fas fa-trash"></i> 삭제
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 원데이 클래스 신청 삭제
async function deleteClassForm(classFormId) {
    if (!confirm('정말로 이 클래스 신청을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/sales/diary_admin/class_form/${classFormId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            loadClassForms();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error deleting class form:', error);
        showAlert('클래스 신청 삭제에 실패했습니다.', 'danger');
    }
}

// 원데이 클래스 요약 정보 업데이트
function updateClassFormsSummary(totalCount) {
    const totalClassFormsDisplay = document.getElementById('total-class-forms-display');
    if (totalClassFormsDisplay) {
        totalClassFormsDisplay.textContent = totalCount.toLocaleString();
    }
}

// 유틸리티 함수들
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showAlert(message, type = 'info') {
    // Bootstrap alert 생성
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 5초 후 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 페이지네이션 렌더링
function renderPagination(pagination, containerId, loadFunction) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    if (pagination.num_pages <= 1) return;
    
    // 이전 페이지
    if (pagination.has_previous) {
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item';
        prevLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); ${loadFunction.name}(${pagination.previous_page_number})">이전</a>`;
        container.appendChild(prevLi);
    }
    
    // 페이지 번호들
    for (let i = 1; i <= pagination.num_pages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === pagination.number ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); ${loadFunction.name}(${i})">${i}</a>`;
        container.appendChild(li);
    }
    
    // 다음 페이지
    if (pagination.has_next) {
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item';
        nextLi.innerHTML = `<a class="page-link" href="#" onclick="event.preventDefault(); ${loadFunction.name}(${pagination.next_page_number})">다음</a>`;
        container.appendChild(nextLi);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin page loaded');
    
    // 모든 필요한 요소들이 존재하는지 확인
    const requiredElements = [
        'dashboard-content',
        'inquiries-content',
        'alarms-content', 
        'create-alarm-content',
        'create-alarm-form'
    ];
    
    console.log('Checking required elements:');
    requiredElements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`${id}:`, element ? 'Found' : 'NOT FOUND');
    });
    
    initializeEventListeners();
    
    // 조회수 타입 초기 표시 설정
    updateCountTypeDisplay();
    
    showDashboard();
});

// 이벤트 리스너 초기화
function initializeEventListeners() {
    console.log('Initializing event listeners');
    
    // 검색 이벤트
    const inquirySearch = document.getElementById('inquiry-search');
    const alarmSearch = document.getElementById('alarm-search');
    const userSearch = document.getElementById('user-search');
    const countSearch = document.getElementById('count-search');
    const classFormSearch = document.getElementById('class-form-search');
    const logSearch = document.getElementById('log-search');
    
    if (inquirySearch) {
        inquirySearch.addEventListener('input', debounce(loadInquiries, 500));
    }
    if (alarmSearch) {
        alarmSearch.addEventListener('input', debounce(loadAlarms, 500));
    }
    if (userSearch) {
        userSearch.addEventListener('input', debounce(loadUsers, 500));
    }
    if (countSearch) {
        countSearch.addEventListener('input', debounce(loadViewCounts, 500));
    }
    if (classFormSearch) {
        classFormSearch.addEventListener('input', debounce(loadClassForms, 500));
    }
    if (logSearch) {
        logSearch.addEventListener('input', debounce(loadLogs, 500));
    }
    
    // 정렬 이벤트
    const inquirySort = document.getElementById('inquiry-sort');
    const alarmSort = document.getElementById('alarm-sort');
    const userSort = document.getElementById('user-sort');
    const countSort = document.getElementById('count-sort');
    const classFormSort = document.getElementById('class-form-sort');
    const logSort = document.getElementById('log-sort');
    
    if (inquirySort) {
        inquirySort.addEventListener('change', loadInquiries);
    }
    if (alarmSort) {
        alarmSort.addEventListener('change', loadAlarms);
    }
    if (userSort) {
        userSort.addEventListener('change', loadUsers);
    }
    if (countSort) {
        countSort.addEventListener('change', loadViewCounts);
    }
    if (classFormSort) {
        classFormSort.addEventListener('change', loadClassForms);
    }
    if (logSort) {
        logSort.addEventListener('change', loadLogs);
    }
    
    // 조회수 타입 변경 이벤트
    const countTypeRadios = document.querySelectorAll('input[name="count-type"]');
    countTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            console.log('Count type changed from', currentCountType, 'to', this.value);
            currentCountType = this.value;
            // 탭 변경 시 즉시 데이터 로드
            loadViewCounts(1); // 첫 페이지부터 로드
            updateCountTypeDisplay(); // 조회수 타입 표시 업데이트
        });
    });
    
    // 사용자 테이블 정렬 헤더 이벤트 리스너
    initializeUserTableSorting();
    
    // 폼 제출 이벤트
    const createAlarmForm = document.getElementById('create-alarm-form');
    const saveEditAlarmBtn = document.getElementById('save-edit-alarm-btn');
    const deleteInquiryBtn = document.getElementById('delete-inquiry-btn');
    
    if (createAlarmForm) {
        createAlarmForm.addEventListener('submit', createAlarm);
        console.log('Create alarm form listener added');
    }
    if (saveEditAlarmBtn) {
        saveEditAlarmBtn.addEventListener('click', saveEditAlarm);
    }
    if (deleteInquiryBtn) {
        deleteInquiryBtn.addEventListener('click', function() {
            if (currentInquiryId) {
                deleteInquiry(currentInquiryId);
            }
        });
    }
    
    // 조회수 삭제 확인 버튼 이벤트
    const confirmCountDeleteBtn = document.getElementById('confirm-count-delete-btn');
    if (confirmCountDeleteBtn) {
        confirmCountDeleteBtn.addEventListener('click', function() {
            const countId = this.getAttribute('data-count-id');
            const countType = this.getAttribute('data-count-type');
            if (countId && countType) {
                deleteViewCount(countId, countType);
            }
        });
    }
}

// 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 네비게이션 함수들
function showDashboard() {
    console.log('Showing dashboard');
    hideAllContent();
    const dashboardContent = document.getElementById('dashboard-content');
    if (dashboardContent) {
        dashboardContent.style.display = 'block';
    }
    updateActiveNav('dashboard');
}

function showInquiries() {
    console.log('Showing inquiries');
    hideAllContent();
    const inquiriesContent = document.getElementById('inquiries-content');
    if (inquiriesContent) {
        inquiriesContent.style.display = 'block';
        loadInquiries();
    }
    updateActiveNav('inquiries');
}

function showAlarms() {
    console.log('Showing alarms');
    hideAllContent();
    const alarmsContent = document.getElementById('alarms-content');
    if (alarmsContent) {
        alarmsContent.style.display = 'block';
        loadAlarms();
    }
    updateActiveNav('alarms');
}

function showCreateAlarm() {
    console.log('Showing create alarm');
    hideAllContent();
    
    const createAlarmContent = document.getElementById('create-alarm-content');
    console.log('create-alarm-content element:', createAlarmContent);
    
    if (createAlarmContent) {
        // 간단하게 display만 설정
        createAlarmContent.style.display = 'block';
        
        console.log('Create alarm content displayed');
        console.log('Current display style:', createAlarmContent.style.display);
        console.log('Computed display style:', window.getComputedStyle(createAlarmContent).display);
        
        // 폼 요소들도 확인
        const form = document.getElementById('create-alarm-form');
        const titleInput = document.getElementById('alarm-title');
        const contentTextarea = document.getElementById('alarm-content');
        
        console.log('Form element:', form);
        console.log('Title input:', titleInput);
        console.log('Content textarea:', contentTextarea);
    } else {
        console.error('create-alarm-content element not found!');
    }
    
    updateActiveNav('create-alarm');
}

function showUsers() {
    hideAllContent();
    const usersContent = document.getElementById('users-content');
    if (usersContent) {
        usersContent.style.display = 'block';
    }
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector('a[onclick="showUsers(); return false;"]').classList.add('active');
    updateActiveNav('users');
    loadUsers();
}

function showViewCounts() {
    hideAllContent();
    const viewCountsContent = document.getElementById('view-counts-content');
    if (viewCountsContent) {
        viewCountsContent.style.display = 'block';
    }
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector('a[onclick="showViewCounts(); return false;"]').classList.add('active');
    updateActiveNav('view-counts');
    updateCountTypeDisplay(); // 조회수 타입 표시 업데이트
    loadViewCounts();
}

function showClassForms() {
    hideAllContent();
    const classFormsContent = document.getElementById('class-forms-content');
    if (classFormsContent) {
        classFormsContent.style.display = 'block';
    }
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector('a[onclick="showClassForms(); return false;"]').classList.add('active');
    updateActiveNav('class-forms');
    loadClassForms();
}

// 모든 콘텐츠 숨기기
function hideAllContent() {
    console.log('Hiding all content');
    const contents = [
        'dashboard-content',
        'inquiries-content', 
        'alarms-content',
        'create-alarm-content',
        'users-content',
        'view-counts-content',
        'class-forms-content',
        'logs-content'
    ];
    
    contents.forEach(id => {
        const element = document.getElementById(id);
        console.log(`Element ${id}:`, element);
        if (element) {
            element.style.display = 'none';
            console.log(`Hidden ${id}`);
        } else {
            console.warn(`Element ${id} not found`);
        }
    });
}

// 활성 네비게이션 업데이트
function updateActiveNav(activeSection) {
    console.log('Updating active nav:', activeSection);
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => link.classList.remove('active'));
    
    // 해당 섹션에 맞는 네비게이션 링크 활성화
    let targetLink = null;
    switch(activeSection) {
        case 'dashboard':
            targetLink = document.querySelector('.nav-link[onclick*="showDashboard"]');
            break;
        case 'inquiries':
            targetLink = document.querySelector('.nav-link[onclick*="showInquiries"]');
            break;
        case 'alarms':
            targetLink = document.querySelector('.nav-link[onclick*="showAlarms"]');
            break;
        case 'create-alarm':
            targetLink = document.querySelector('.nav-link[onclick*="showCreateAlarm"]');
            break;
        case 'users':
            targetLink = document.querySelector('.nav-link[onclick*="showUsers"]');
            break;
        case 'view-counts':
            targetLink = document.querySelector('.nav-link[onclick*="showViewCounts"]');
            break;
        case 'class-forms':
            targetLink = document.querySelector('.nav-link[onclick*="showClassForms"]');
            break;
        case 'logs':
            targetLink = document.querySelector('.nav-link[onclick*="showLogs"]');
            break;
    }
    
    if (targetLink) {
        targetLink.classList.add('active');
    }
}

// 문의사항 로드
async function loadInquiries(page = 1) {
    try {
        const searchQuery = document.getElementById('inquiry-search')?.value || '';
        const sortBy = document.getElementById('inquiry-sort')?.value || '-created_at';
        
        const params = new URLSearchParams({
            search: searchQuery,
            sort: sortBy,
            page: page
        });
        
        const response = await fetch(`/sales/diary_admin/inquiries/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderInquiriesTable(data.inquiries, page, 10);
            renderPagination(data.pagination, 'inquiries-pagination', loadInquiries);
        } else {
            showAlert('문의사항을 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading inquiries:', error);
        showAlert('문의사항을 불러오는데 실패했습니다.', 'danger');
    }
}

// 공지사항 로드
async function loadAlarms(page = 1) {
    try {
        const searchQuery = document.getElementById('alarm-search')?.value || '';
        const sortBy = document.getElementById('alarm-sort')?.value || '-created_at';
        
        const params = new URLSearchParams({
            search: searchQuery,
            sort: sortBy,
            page: page
        });
        
        const response = await fetch(`/sales/diary_admin/alarms/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderAlarmsTable(data.alarms, page, 10);
            renderPagination(data.pagination, 'alarms-pagination', loadAlarms);
        } else {
            showAlert('공지사항을 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading alarms:', error);
        showAlert('공지사항을 불러오는데 실패했습니다.', 'danger');
    }
}

// 사용자 로드
async function loadUsers(page = 1) {
    try {
        const searchQuery = document.getElementById('user-search')?.value || '';
        
        // 정렬 필드 매핑
        let sortField = currentUserSort.field;
        let sortBy = '';
        
        console.log('=== LOAD USERS SORT LOGIC ===');
        console.log('Raw currentUserSort:', currentUserSort);
        console.log('sortField:', sortField, 'direction:', currentUserSort.direction);
        
        if (sortField && currentUserSort.direction) {
            if (sortField === 'phone_number') {
                sortField = 'phone_number'; // Django 모델 필드명과 일치
            } else if (sortField === 'company_name') {
                sortField = 'company_name'; // Django 모델 필드명과 일치
            }
            
            // 내림차순인 경우 '-' 접두사 추가
            if (currentUserSort.direction === 'desc') {
                sortBy = `-${sortField}`;
                console.log('Descending sort detected, adding minus prefix');
            } else {
                sortBy = sortField;
                console.log('Ascending sort detected, no prefix');
            }
            
            console.log('Direction check:', currentUserSort.direction, 'Is desc?', currentUserSort.direction === 'desc');
            console.log('Final sortBy value:', sortBy);
        } else {
            console.log('No sort field or direction, sortBy will be empty');
        }
        
        console.log('Final sortBy for request:', sortBy);
        
        const params = new URLSearchParams({
            search: searchQuery,
            page: page
        });
        
        // 정렬이 설정된 경우에만 sort 파라미터 추가
        if (sortBy) {
            params.append('sort', sortBy);
            console.log('Added sort parameter to request:', sortBy);
        } else {
            console.log('No sort parameter added to request');
        }
        
        const requestUrl = `/sales/diary_admin/users/?${params}`;
        console.log('Requesting URL:', requestUrl);
        
        const response = await fetch(requestUrl);
        const data = await response.json();
        
        if (data.success) {
            renderUsersTable(data.users, data.current_user_id, data.is_super_admin, page, 10);
            renderPagination(data.pagination, 'users-pagination', loadUsers);
            // 정렬 상태는 이미 handleUserTableSort에서 업데이트됨
        } else {
            showAlert('사용자 목록을 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showAlert('사용자 목록을 불러오는데 실패했습니다.', 'danger');
    }
}

function loadViewCounts(page = 1) {
    const searchQuery = document.getElementById('count-search')?.value || '';
    const sortBy = document.getElementById('count-sort')?.value || '-count';
    
    console.log('Loading view counts with:', { currentCountType, searchQuery, sortBy, page });
    
    const url = `/sales/diary_admin/diary_counts/?search=${encodeURIComponent(searchQuery)}&sort=${encodeURIComponent(sortBy)}&page=${page}&type=${currentCountType}`;
    
    console.log('Requesting URL:', url);
    
    fetch(url)
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            
            
            
            
            if (data.success) {
                displayViewCounts(data.counts, page, 20, data.total_count, data.total_ips);
                displayViewCountPagination(data.pagination, page);
                updateViewCountSummary(data.total_count, data.total_ips);
            } else {
                console.error('조회수 로드 실패:', data.message);
            }
        })
        .catch(error => {
            console.error('조회수 로드 중 오류:', error);
        });
}

// 문의사항 테이블 렌더링
function renderInquiriesTable(inquiries, currentPage = 1, pageSize = 10) {
    const tbody = document.getElementById('inquiries-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (inquiries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">문의사항이 없습니다.</td></tr>';
        return;
    }
    
    inquiries.forEach((inquiry, index) => {
        const row = document.createElement('tr');
        const displayNumber = (currentPage - 1) * pageSize + (inquiries.length - index);
        
        row.innerHTML = `
            <td>${displayNumber}</td>
            <td>${inquiry.name || '익명'}</td>
            <td>${inquiry.company_name || '-'}</td>
            <td>${inquiry.contact || '-'}</td>
            <td>${inquiry.content.length > 50 ? inquiry.content.substring(0, 50) + '...' : inquiry.content}</td>
            <td>${formatDate(inquiry.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewInquiryDetail(${inquiry.id})">
                    <i class="fas fa-eye"></i> 보기
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteInquiry(${inquiry.id})">
                    <i class="fas fa-trash"></i> 삭제
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 공지사항 테이블 렌더링
function renderAlarmsTable(alarms, currentPage = 1, pageSize = 10) {
    const tbody = document.getElementById('alarms-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (alarms.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">공지사항이 없습니다.</td></tr>';
        return;
    }
    
    alarms.forEach((alarm, index) => {
        const fileCount = alarm.files ? alarm.files.length : 0;
        const fileInfo = fileCount > 0 ? `<span class="badge bg-info"><i class="fas fa-paperclip"></i> ${fileCount}개</span>` : '-';
        const displayNumber = (currentPage - 1) * pageSize + (alarms.length - index);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${displayNumber}</td>
            <td>${safeEmojiText(alarm.title)}</td>
            <td>${safeEmojiText(alarm.content.length > 50 ? alarm.content.substring(0, 50) + '...' : alarm.content)}</td>
            <td>${fileInfo}</td>
            <td>${formatDate(alarm.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="editAlarm(${alarm.id})">
                    <i class="fas fa-edit"></i> 수정
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteAlarm(${alarm.id})">
                    <i class="fas fa-trash"></i> 삭제
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 사용자 테이블 렌더링
function renderUsersTable(users, currentUserId, isSuperAdmin, currentPage = 1, pageSize = 10) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">사용자가 없습니다.</td></tr>';
        return;
    }
    
    users.forEach((user, index) => {
        let adminToggleBtn = '';
        const displayNumber = (currentPage - 1) * pageSize + (users.length - index);
        
        // 최고 관리자(ID=1)만 관리자 권한 토글 버튼 표시
        if (isSuperAdmin) {
            adminToggleBtn = user.is_admin 
                ? `<button class="admin-toggle-btn admin" onclick="toggleAdminStatus(${user.id}, '${user.name || '사용자'}', '${user.email}', false)">
                       <i class="fas fa-user-shield"></i> 관리자
                   </button>`
                : `<button class="admin-toggle-btn user" onclick="toggleAdminStatus(${user.id}, '${user.name || '사용자'}', '${user.email}', true)">
                       <i class="fas fa-user"></i> 일반
                   </button>`;
        } else {
            // 일반 관리자는 읽기 전용으로 표시
            adminToggleBtn = user.is_admin 
                ? `<span class="badge bg-danger">관리자</span>`
                : `<span class="badge bg-secondary">일반</span>`;
        }
        
        // 활성화 토글 버튼
        const activateToggleBtn = `
            <button class="btn btn-sm ${user.activate ? 'btn-success' : 'btn-secondary'} activate-toggle-btn" 
                    onclick="toggleActivateStatus(${user.id}, '${user.name || '사용자'}', '${user.email}', ${!user.activate})">
                <i class="fas fa-${user.activate ? 'check-circle' : 'times-circle'}"></i>
                ${user.activate ? '활성' : '비활성'}
            </button>
        `;
        
        // 사용 기간 표시 및 수정 버튼
        const useDate = user.use_date ? formatDateOnly(user.use_date) : '미설정';
        const useDateCell = `
            <div class="d-flex align-items-center">
                <span class="me-2">${useDate}</span>
                <button class="btn btn-sm btn-outline-primary" onclick="editUseDate(${user.id}, '${user.name || '사용자'}', '${user.email}', '${user.use_date || ''}')">
                    <i class="fas fa-edit"></i>
                </button>
            </div>
        `;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${displayNumber}</td>
            <td>${user.name || '-'}</td>
            <td>${user.email}</td>
            <td>${user.company_name || '-'}</td>
            <td>${user.phone_number || '-'}</td>
            <td>${formatDateOnly(user.created_at)}</td>
            <td>${useDateCell}</td>
            <td>${activateToggleBtn}</td>
            <td>${adminToggleBtn}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteUser(${user.id}, '${user.name || '사용자'}', '${user.email}')">
                    <i class="fas fa-trash"></i> 삭제
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 관리자 권한 토글 함수
function toggleAdminStatus(userId, userName, userEmail, makeAdmin) {
    const currentStatus = makeAdmin ? '일반' : '관리자';
    const targetStatus = makeAdmin ? '관리자' : '일반';
    
    // 모달에 정보 설정
    document.getElementById('current-admin-status').textContent = currentStatus;
    document.getElementById('target-admin-status').textContent = targetStatus;
    
    // 확인 버튼에 함수 연결
    const confirmBtn = document.getElementById('confirm-admin-change-btn');
    confirmBtn.onclick = () => changeAdminStatus(userId, makeAdmin);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('adminChangeModal'));
    modal.show();
}

// 관리자 권한 변경 실행 함수
async function changeAdminStatus(userId, makeAdmin) {
    try {
        const response = await fetch(`/sales/diary_admin/users/${userId}/toggle_admin/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                make_admin: makeAdmin
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // 모달 닫기
            bootstrap.Modal.getInstance(document.getElementById('adminChangeModal')).hide();
            // 사용자 목록 새로고침
            loadUsers();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error changing admin status:', error);
        showAlert('관리자 권한 변경에 실패했습니다.', 'danger');
    }
}

// 사용자 삭제 확인
function confirmDeleteUser(userId, userName, userEmail) {
    const userInfoDiv = document.getElementById('user-delete-info');
    userInfoDiv.innerHTML = `
        <div class="alert alert-info">
            <strong>삭제할 사용자 정보:</strong><br>
            이름: ${userName}<br>
            이메일: ${userEmail}<br>
            사용자 ID: ${userId}
        </div>
    `;
    
    // 삭제 버튼에 사용자 ID 저장
    const confirmBtn = document.getElementById('confirm-user-delete-btn');
    confirmBtn.onclick = () => deleteUser(userId);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('userDeleteModal'));
    modal.show();
}

// 사용자 삭제
async function deleteUser(userId) {
    try {
        const response = await fetch(`/sales/diary_admin/users/${userId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // 모달 닫기
            bootstrap.Modal.getInstance(document.getElementById('userDeleteModal')).hide();
            // 사용자 목록 새로고침
            loadUsers();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showAlert('사용자 삭제에 실패했습니다.', 'danger');
    }
}

// 문의사항 상세보기
async function viewInquiryDetail(inquiryId) {
    try {
        const response = await fetch(`/sales/diary_admin/inquiry/${inquiryId}/`);
        const data = await response.json();
        
        if (data.success) {
            const inquiry = data.inquiry;
            currentInquiryId = inquiryId;
            
            const modalBody = document.getElementById('inquiry-detail-content');
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <strong>이름:</strong> ${inquiry.name || '익명'}<br>
                        <strong>회사명:</strong> ${inquiry.company_name || '-'}<br>
                        <strong>연락처:</strong> ${inquiry.contact || '-'}<br>
                        <strong>작성일:</strong> ${formatDate(inquiry.created_at)}
                    </div>
                    <div class="col-md-6">
                        <strong>내용:</strong><br>
                        <div class="mt-2 p-3 bg-light rounded">
                            ${inquiry.content.replace(/\n/g, '<br>')}
                        </div>
                    </div>
                </div>
            `;
            
            const modal = new bootstrap.Modal(document.getElementById('inquiryDetailModal'));
            modal.show();
        } else {
            showAlert('문의사항을 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading inquiry detail:', error);
        showAlert('문의사항을 불러오는데 실패했습니다.', 'danger');
    }
}

// 공지사항 수정
async function editAlarm(alarmId) {
    try {
        const response = await fetch(`/sales/diary_admin/alarm/${alarmId}/`);
        const data = await response.json();
        
        if (data.success) {
            const alarm = data.alarm;
            currentAlarmId = alarmId;
            
            document.getElementById('edit-alarm-id').value = alarmId;
            document.getElementById('edit-alarm-title').value = safeEmojiText(alarm.title);
            document.getElementById('edit-alarm-content').value = safeEmojiText(alarm.content);
            
            // 현재 파일 목록 표시
            const currentFilesSection = document.getElementById('current-files-section');
            const currentFilesList = document.getElementById('current-files-list');
            
            if (alarm.files && alarm.files.length > 0) {
                currentFilesList.innerHTML = '';
                alarm.files.forEach(file => {
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'd-flex justify-content-between align-items-center mb-2 p-2 border rounded';
                    fileDiv.innerHTML = `
                        <div class="d-flex align-items-center">
                            <i class="fas fa-file me-2"></i>
                            <div>
                                <div class="fw-bold">${safeEmojiText(file.original_name || 'Unknown')}</div>
                                <small class="text-muted">${formatFileSize(file.file_size || 0)}</small>
                            </div>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary me-1" onclick="window.open('${file.download_url || file.public_url}', '_blank')">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    `;
                    currentFilesList.appendChild(fileDiv);
                });
                currentFilesSection.style.display = 'block';
            } else {
                currentFilesSection.style.display = 'none';
            }
            
            const modal = new bootstrap.Modal(document.getElementById('editAlarmModal'));
            modal.show();
        } else {
            showAlert('공지사항을 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading alarm:', error);
        showAlert('공지사항을 불러오는데 실패했습니다.', 'danger');
    }
}

// 공지사항 생성
async function createAlarm(event) {
    event.preventDefault();
    
    const title = document.getElementById('alarm-title').value.trim();
    const content = document.getElementById('alarm-content').value.trim();
    const files = document.getElementById('alarm-files').files;
    
    if (!title || !content) {
        showAlert('제목과 내용을 모두 입력해주세요.', 'warning');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('content', content);
        
        // 파일 추가
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        
        const response = await fetch('/sales/diary_admin/alarm/create/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            document.getElementById('create-alarm-form').reset();
            showDashboard();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error creating alarm:', error);
        showAlert('공지사항 작성에 실패했습니다.', 'danger');
    }
}

// 공지사항 수정 저장
async function saveEditAlarm() {
    const alarmId = document.getElementById('edit-alarm-id').value;
    const title = document.getElementById('edit-alarm-title').value.trim();
    const content = document.getElementById('edit-alarm-content').value.trim();
    const files = document.getElementById('edit-alarm-files').files;
    
    if (!title || !content) {
        showAlert('제목과 내용을 모두 입력해주세요.', 'warning');
        return;
    }
    
    try {
        // 기존 파일 정보 가져오기
        const currentFilesSection = document.getElementById('current-files-section');
        const currentFiles = [];
        if (currentFilesSection.style.display !== 'none') {
            const fileItems = currentFilesSection.querySelectorAll('.file-item');
            fileItems.forEach(item => {
                const fileName = item.querySelector('.fw-bold').textContent;
                const fileSize = item.querySelector('.text-muted').textContent;
                // 기존 파일 정보를 유지
                currentFiles.push({
                    original_name: fileName,
                    file_size: fileSize
                });
            });
        }
        
        // 새 파일 업로드
        let uploadedFiles = [];
        if (files.length > 0) {
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            const uploadResponse = await fetch('/sales/diary_admin/alarm/create/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });
            
            const uploadData = await uploadResponse.json();
            if (uploadData.success) {
                uploadedFiles = uploadData.files || [];
            }
        }
        
        // 모든 파일 정보 결합
        const allFiles = [...currentFiles, ...uploadedFiles];
        
        const response = await fetch(`/sales/diary_admin/alarm/${alarmId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                title: title,
                content: content,
                files: allFiles
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('editAlarmModal')).hide();
            loadAlarms();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error saving alarm:', error);
        showAlert('공지사항 수정에 실패했습니다.', 'danger');
    }
}

// 문의사항 삭제
async function deleteInquiry(inquiryId) {
    if (!confirm('정말로 이 문의사항을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch('/sales/diary_admin/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                action: 'delete_inquiry',
                inquiry_id: inquiryId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            loadInquiries();
            bootstrap.Modal.getInstance(document.getElementById('inquiryDetailModal')).hide();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error deleting inquiry:', error);
        showAlert('문의사항 삭제에 실패했습니다.', 'danger');
    }
}

// 공지사항 삭제
async function deleteAlarm(alarmId) {
    if (!confirm('정말로 이 공지사항을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch('/sales/diary_admin/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                action: 'delete_alarm',
                alarm_id: alarmId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            loadAlarms();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error deleting alarm:', error);
        showAlert('공지사항 삭제에 실패했습니다.', 'danger');
    }
}

// 유틸리티 함수들
function formatDateOnly(dateString) {
    const date = new Date(dateString);
    const formattedDate = date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
    // 마지막 점 제거
    return formattedDate.replace(/\.$/, '');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 이모지 안전 처리 함수
function safeEmojiText(text) {
    if (!text) return '';
    // 이모지가 제대로 표시되도록 안전하게 처리
    return text.replace(/[\uD800-\uDBFF][\uDC00-\uDFFF]/g, function(match) {
        return match;
    });
}

// 사용 기간 수정
function editUseDate(userId, userName, userEmail, currentUseDate) {
    // 모달에 사용자 정보 설정
    document.getElementById('edit-use-date-user-name').textContent = userName;
    document.getElementById('edit-use-date-user-email').textContent = userEmail;
    
    // 현재 사용 기간 설정
    const useDateInput = document.getElementById('edit-use-date');
    if (currentUseDate) {
        useDateInput.value = currentUseDate.split('T')[0]; // ISO 문자열에서 날짜 부분만 추출
    } else {
        useDateInput.value = '';
    }
    
    // 저장 버튼에 사용자 ID 저장
    const saveBtn = document.getElementById('save-use-date-btn');
    saveBtn.onclick = () => saveUseDate(userId);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('useDateEditModal'));
    modal.show();
}

// 사용 기간 저장
async function saveUseDate(userId) {
    const useDate = document.getElementById('edit-use-date').value;
    
    if (!useDate) {
        showAlert('사용 기간을 입력해주세요.', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/sales/diary_admin/users/${userId}/update_use_date/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                use_date: useDate
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // 모달 닫기
            bootstrap.Modal.getInstance(document.getElementById('useDateEditModal')).hide();
            // 사용자 목록 새로고침
            loadUsers();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error updating use date:', error);
        showAlert('사용 기간 수정에 실패했습니다.', 'danger');
    }
}

// 사용자 테이블 정렬 초기화
function initializeUserTableSorting() {
    // 기존 이벤트 리스너 제거
    const sortButtons = document.querySelectorAll('.sort-btn');
    sortButtons.forEach(button => {
        // 기존 클릭 이벤트 제거
        button.removeEventListener('click', button._sortClickHandler);
        
        // 새로운 클릭 이벤트 핸들러 생성 및 저장
        button._sortClickHandler = function() {
            const field = this.getAttribute('data-field');
            const direction = this.getAttribute('data-direction');
            handleUserTableSort(field, direction);
        };
        
        // 이벤트 리스너 등록
        button.addEventListener('click', button._sortClickHandler);
    });
}

// 사용자 테이블 정렬 처리
function handleUserTableSort(field, direction) {
    // 이미 정렬 중이면 무시
    if (isSortingInProgress) {
        console.log('Sort already in progress, ignoring click');
        return;
    }
    
    console.log('=== SORT CLICK ===');
    console.log('Clicked field:', field, 'direction:', direction);
    console.log('Current sort before:', currentUserSort);
    
    // 정렬 진행 중 플래그 설정
    isSortingInProgress = true;
    
    try {
        // 같은 필드와 방향을 클릭한 경우 정렬 해제
        if (currentUserSort.field === field && currentUserSort.direction === direction) {
            console.log('Removing sort - same field and direction clicked');
            currentUserSort.field = null;
            currentUserSort.direction = null;
        } else {
            // 새로운 정렬 설정 (기존 정렬과 다른 경우)
            console.log('Setting new sort - field:', field, 'direction:', direction);
            currentUserSort.field = field;
            currentUserSort.direction = direction;
        }
        
        console.log('Current sort after update:', currentUserSort);
        console.log('Will send sort parameter:', currentUserSort.field && currentUserSort.direction ? `${currentUserSort.direction === 'desc' ? '-' : ''}${currentUserSort.field}` : 'none');
        
        // 즉시 시각적 업데이트
        updateUserTableSortVisuals();
        
        // 사용자 목록 새로고침
        loadUsers();
    } finally {
        // 정렬 완료 후 플래그 해제
        setTimeout(() => {
            isSortingInProgress = false;
        }, 100); // 100ms 후 플래그 해제
    }
}

// 사용자 테이블 정렬 상태 시각적 업데이트
function updateUserTableSortVisuals() {
    console.log('=== UPDATE SORT VISUALS ===');
    console.log('Current sort state:', currentUserSort);
    
    // 모든 정렬 버튼을 비활성 상태로 초기화
    const allSortButtons = document.querySelectorAll('.sort-btn');
    console.log('Found sort buttons:', allSortButtons.length);
    allSortButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // 현재 정렬 중인 버튼만 활성화
    if (currentUserSort.field && currentUserSort.direction) {
        const activeButton = document.querySelector(`.sort-btn[data-field="${currentUserSort.field}"][data-direction="${currentUserSort.direction}"]`);
        console.log('Looking for button with field:', currentUserSort.field, 'direction:', currentUserSort.direction);
        console.log('Found active button:', activeButton);
        
        if (activeButton) {
            activeButton.classList.add('active');
            console.log('Successfully activated button for:', currentUserSort.field, currentUserSort.direction);
        } else {
            console.error('Button not found for field:', currentUserSort.field, 'direction:', currentUserSort.direction);
        }
    } else {
        console.log('No active sort - all buttons deactivated');
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.name || '-'}</td>
            <td>${user.email}</td>
            <td>${user.company_name || '-'}</td>
            <td>${user.phone_number || '-'}</td>
            <td>${formatDate(user.created_at)}</td>
            <td>${user.use_date ? formatDate(user.use_date) : '무제한'}</td>
            <td>
                <button class="btn btn-sm ${user.is_admin ? 'btn-success' : 'btn-secondary'} admin-toggle-btn ${user.is_admin ? 'admin' : 'user'}" 
                        onclick="toggleAdminStatus(${user.id}, ${!user.is_admin})" 
                        ${user.id == 1 ? 'disabled' : ''}>
                    ${user.is_admin ? '관리자' : '일반사용자'}
                </button>
            </td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-primary" onclick="editUseDate(${user.id}, '${user.name}', '${user.email}', '${user.use_date || ''}')">
                        <i class="fas fa-calendar"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id}, '${user.name}', '${user.email}')" ${user.id == 1 ? 'disabled' : ''}>
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 조회수 테이블 렌더링
function displayViewCounts(counts, currentPage = 1, pageSize = 20, totalCount = 0, totalIps = 0) {
    console.log('Displaying view counts:', counts);
    const tbody = document.getElementById('counts-table-body');
    if (!tbody) {
        console.error('counts-table-body not found');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (counts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">조회수 기록이 없습니다.</td></tr>';
        return;
    }
    
    counts.forEach((count, index) => {
        const row = document.createElement('tr');
        // IP 수 기준으로 번호 매기기: 1페이지 맨 위에 가장 큰 번호(총 IP 수)가 나오도록
        const displayNumber = totalIps - ((currentPage - 1) * pageSize + index);
        
        row.innerHTML = `
            <td>${displayNumber}</td>
            <td>${count.ip}</td>
            <td><span class="badge bg-primary">${count.count}</span></td>
            <td>${formatDate(count.created_at)}</td>
            <td>${formatDate(count.updated_at)}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteViewCountConfirm(${count.id}, '${count.ip}', ${count.count})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function displayViewCountPagination(pagination, currentPage = 1) {
    const paginationElement = document.getElementById('counts-pagination');
    if (!paginationElement) return;
    
    paginationElement.innerHTML = '';
    
    // 이전 페이지 버튼
    if (pagination.has_previous) {
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item';
        prevLi.innerHTML = `<a class="page-link" href="javascript:void(0)" onclick="loadViewCounts(${pagination.previous_page_number})">이전</a>`;
        paginationElement.appendChild(prevLi);
    }
    
    // 페이지 번호들
    for (let i = 1; i <= pagination.num_pages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === pagination.number ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="javascript:void(0)" onclick="loadViewCounts(${i})">${i}</a>`;
        paginationElement.appendChild(li);
    }
    
    // 다음 페이지 버튼
    if (pagination.has_next) {
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item';
        nextLi.innerHTML = `<a class="page-link" href="javascript:void(0)" onclick="loadViewCounts(${pagination.next_page_number})">다음</a>`;
        paginationElement.appendChild(nextLi);
    }
}

function updateViewCountSummary(totalCount, totalIps) {
    console.log('Updating view count summary:', { totalCount, totalIps, currentCountType });
    
    const totalCountDisplay = document.getElementById('total-count-display');
    const totalIpsDisplay = document.getElementById('total-ips-display');
    
    if (totalCountDisplay) {
        totalCountDisplay.textContent = totalCount.toLocaleString();
        console.log('Updated total count display:', totalCount.toLocaleString());
    } else {
        console.error('total-count-display element not found');
    }
    
    if (totalIpsDisplay) {
        totalIpsDisplay.textContent = totalIps.toLocaleString();
        console.log('Updated total IPs display:', totalIps.toLocaleString());
    } else {
        console.error('total-ips-display element not found');
    }
}

function deleteViewCountConfirm(countId, ip, count) {
    // 조회수 삭제 확인 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('countDeleteModal'));
    const countDeleteInfo = document.getElementById('count-delete-info');
    
    if (countDeleteInfo) {
        countDeleteInfo.innerHTML = `
            <p><strong>IP 주소:</strong> ${ip}</p>
            <p><strong>조회수:</strong> ${count}</p>
        `;
    }
    
    // 삭제 확인 버튼에 조회수 ID와 타입 설정
    const confirmBtn = document.getElementById('confirm-count-delete-btn');
    if (confirmBtn) {
        confirmBtn.setAttribute('data-count-id', countId);
        confirmBtn.setAttribute('data-count-type', currentCountType);
    }
    
    modal.show();
}

function deleteViewCount(countId, countType) {
    const url = `/sales/diary_admin/diary_count/${countId}/delete/?type=${countType}`;
    
    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 모달 닫기
            const modal = bootstrap.Modal.getInstance(document.getElementById('countDeleteModal'));
            if (modal) {
                modal.hide();
            }
            
            // 성공 메시지 표시
            showAlert(data.message, 'success');
            
            // 조회수 목록 새로고침
            loadViewCounts();
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('조회수 삭제 중 오류:', error);
        showAlert('조회수 삭제 중 오류가 발생했습니다.', 'danger');
    });
}

function updateCountTypeDisplay() {
    const countTypeDisplay = document.getElementById('count-type-display');
    if (countTypeDisplay) {
        const displayText = currentCountType === 'main' ? '메인 페이지' : '다이어리 페이지';
        countTypeDisplay.textContent = displayText;
        console.log('Updated count type display:', displayText);
    }
}

// 활성화 상태 토글 함수
function toggleActivateStatus(userId, userName, userEmail, makeActive) {
    const currentStatus = makeActive ? '비활성' : '활성';
    const targetStatus = makeActive ? '활성' : '비활성';
    
    if (confirm(`사용자 "${userName}"의 계정을 ${targetStatus}화하시겠습니까?`)) {
        changeActivateStatus(userId, makeActive);
    }
}

// 활성화 상태 변경 실행 함수
async function changeActivateStatus(userId, makeActive) {
    try {
        const response = await fetch(`/sales/diary_admin/users/${userId}/toggle_activate/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                make_active: makeActive
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // 사용자 목록 새로고침
            loadUsers();
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error changing activate status:', error);
        showAlert('계정 활성화 상태 변경에 실패했습니다.', 'danger');
    }
}

// 로그 관련 함수들
async function loadLogs(page = 1) {
    try {
        const searchQuery = document.getElementById('log-search')?.value || '';
        const sortBy = document.getElementById('log-sort')?.value || '-created_at';
        const startDate = document.getElementById('log-start-date')?.value || '';
        const endDate = document.getElementById('log-end-date')?.value || '';
        
        const params = new URLSearchParams({
            search: searchQuery,
            sort: sortBy,
            page: page
        });
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        const response = await fetch(`/sales/diary_admin/logs/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderLogsTable(data.logs, page, 20);
            renderPagination(data.pagination, 'logs-pagination', loadLogs);
            updateLogsSummary(data.total_count, data.logs);
        } else {
            showAlert('로그를 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        showAlert('로그를 불러오는데 실패했습니다.', 'danger');
    }
}

// 로그 테이블 렌더링
function renderLogsTable(logs, currentPage = 1, pageSize = 20) {
    const tbody = document.getElementById('logs-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">로그가 없습니다.</td></tr>';
        return;
    }
    
    logs.forEach((log, index) => {
        const row = document.createElement('tr');
        const displayNumber = (currentPage - 1) * pageSize + (logs.length - index);
        const created_at = log.created_at.split('T')[0]+' '+log.created_at.split('T')[1].split('.')[0];
        
        row.innerHTML = `
            <td>${displayNumber}</td>
            <td><code>${log.ip}</code></td>
            <td>${log.user_name || '-'}</td>
            <td>${log.user_email || '-'}</td>
            <td>${created_at}</td>
        `;
        tbody.appendChild(row);
    });
}

// 로그 요약 정보 업데이트
function updateLogsSummary(totalCount, logs) {
    const totalLogsDisplay = document.getElementById('total-logs-display');
    const uniqueUsersDisplay = document.getElementById('unique-users-display');
    const uniqueIPsDisplay = document.getElementById('unique-ips-display');
    
    if (totalLogsDisplay) {
        totalLogsDisplay.textContent = totalCount.toLocaleString();
    }
    
    if (uniqueUsersDisplay && logs) {
        const uniqueUsers = new Set(logs.map(log => log.user_email).filter(email => email && email !== '알 수 없음'));
        uniqueUsersDisplay.textContent = uniqueUsers.size.toLocaleString();
    }
    
    if (uniqueIPsDisplay && logs) {
        const uniqueIPs = new Set(logs.map(log => log.ip));
        uniqueIPsDisplay.textContent = uniqueIPs.size.toLocaleString();
    }
}

// 로그 엑셀 다운로드
function exportLogsToExcel() {
    const startDate = document.getElementById('log-start-date')?.value || '';
    const endDate = document.getElementById('log-end-date')?.value || '';
    
    let url = '/sales/diary_admin/logs/export/';
    const params = new URLSearchParams();
    
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    // 파일명 생성
    let filename = '사용자_접속_로그';
    if (startDate && endDate) {
        filename += `_${startDate}_to_${endDate}`;
    } else {
        const today = new Date();
        filename += `_전체_${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
    }
    filename += '.xlsx';
    
    // fetch를 사용하여 파일 다운로드
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
        .then(blob => {
            // Blob URL 생성
            const blobUrl = window.URL.createObjectURL(blob);
            
            // 다운로드 링크 생성
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            link.style.display = 'none';
            
            // DOM에 추가하고 클릭
            document.body.appendChild(link);
            link.click();
            
            // 정리
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
        })
        .catch(error => {
            console.error('엑셀 다운로드 중 오류:', error);
            showAlert('엑셀 다운로드에 실패했습니다.', 'danger');
        });
}

// 로그 날짜 초기화
function clearLogDates() {
    document.getElementById('log-start-date').value = '';
    document.getElementById('log-end-date').value = '';
    loadLogs(); // 전체 기간 데이터 로드
}

// 로그 보기 탭 표시
function showLogs() {
    hideAllContent();
    const logsContent = document.getElementById('logs-content');
    if (logsContent) {
        logsContent.style.display = 'block';
    }
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector('a[onclick="showLogs(); return false;"]').classList.add('active');
    updateActiveNav('logs');
    
    // 페이지 로드 시 기본 날짜 설정
    const today = new Date();
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(today.getDate() - 7);
    
    document.getElementById('log-end-date').value = today.toISOString().split('T')[0];
    document.getElementById('log-start-date').value = sevenDaysAgo.toISOString().split('T')[0];
    
    loadLogs();
}