// 어드민 페이지 JavaScript

// 전역 변수
let currentInquiryId = null;
let currentAlarmId = null;

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
    showDashboard();
});

// 이벤트 리스너 초기화
function initializeEventListeners() {
    console.log('Initializing event listeners');
    
    // 검색 이벤트
    const inquirySearch = document.getElementById('inquiry-search');
    const alarmSearch = document.getElementById('alarm-search');
    const userSearch = document.getElementById('user-search');
    
    if (inquirySearch) {
        inquirySearch.addEventListener('input', debounce(loadInquiries, 500));
    }
    if (alarmSearch) {
        alarmSearch.addEventListener('input', debounce(loadAlarms, 500));
    }
    if (userSearch) {
        userSearch.addEventListener('input', debounce(loadUsers, 500));
    }
    
    // 정렬 이벤트
    const inquirySort = document.getElementById('inquiry-sort');
    const alarmSort = document.getElementById('alarm-sort');
    const userSort = document.getElementById('user-sort');
    
    if (inquirySort) {
        inquirySort.addEventListener('change', loadInquiries);
    }
    if (alarmSort) {
        alarmSort.addEventListener('change', loadAlarms);
    }
    if (userSort) {
        userSort.addEventListener('change', loadUsers);
    }
    
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
        dashboardContent.setAttribute('style', 'display: block !important; visibility: visible !important; opacity: 1 !important;');
    }
    updateActiveNav('dashboard');
}

function showInquiries() {
    console.log('Showing inquiries');
    hideAllContent();
    const inquiriesContent = document.getElementById('inquiries-content');
    if (inquiriesContent) {
        inquiriesContent.setAttribute('style', 'display: block !important; visibility: visible !important; opacity: 1 !important;');
        loadInquiries();
    }
    updateActiveNav('inquiries');
}

function showAlarms() {
    console.log('Showing alarms');
    hideAllContent();
    const alarmsContent = document.getElementById('alarms-content');
    if (alarmsContent) {
        alarmsContent.setAttribute('style', 'display: block !important; visibility: visible !important; opacity: 1 !important;');
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
        // 여러 방법으로 display를 설정
        createAlarmContent.style.display = 'block';
        createAlarmContent.style.visibility = 'visible';
        createAlarmContent.style.opacity = '1';
        
        // 인라인 스타일도 직접 설정
        createAlarmContent.setAttribute('style', 'display: block !important; visibility: visible !important; opacity: 1 !important;');
        
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
    console.log('Showing users');
    hideAllContent();
    const usersContent = document.getElementById('users-content');
    if (usersContent) {
        usersContent.setAttribute('style', 'display: block !important; visibility: visible !important; opacity: 1 !important;');
    }
    updateActiveNav('users');
    loadUsers();
}

// 모든 콘텐츠 숨기기
function hideAllContent() {
    console.log('Hiding all content');
    const contents = [
        'dashboard-content',
        'inquiries-content', 
        'alarms-content',
        'create-alarm-content',
        'users-content'
    ];
    
    contents.forEach(id => {
        const element = document.getElementById(id);
        console.log(`Element ${id}:`, element);
        if (element) {
            element.setAttribute('style', 'display: none !important; visibility: hidden !important; opacity: 0 !important;');
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
            renderInquiriesTable(data.inquiries);
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
            renderAlarmsTable(data.alarms);
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
        const sortBy = document.getElementById('user-sort')?.value || '-created_at';
        
        const params = new URLSearchParams({
            search: searchQuery,
            sort: sortBy,
            page: page
        });
        
        const response = await fetch(`/sales/diary_admin/users/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderUsersTable(data.users, data.current_user_id, data.is_super_admin);
            renderPagination(data.pagination, 'users-pagination', loadUsers);
        } else {
            showAlert('사용자 목록을 불러오는데 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showAlert('사용자 목록을 불러오는데 실패했습니다.', 'danger');
    }
}

// 문의사항 테이블 렌더링
function renderInquiriesTable(inquiries) {
    const tbody = document.getElementById('inquiries-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (inquiries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">문의사항이 없습니다.</td></tr>';
        return;
    }
    
    inquiries.forEach(inquiry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${inquiry.id}</td>
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
function renderAlarmsTable(alarms) {
    const tbody = document.getElementById('alarms-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (alarms.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">공지사항이 없습니다.</td></tr>';
        return;
    }
    
    alarms.forEach(alarm => {
        const fileCount = alarm.files ? alarm.files.length : 0;
        const fileInfo = fileCount > 0 ? `<span class="badge bg-info"><i class="fas fa-paperclip"></i> ${fileCount}개</span>` : '-';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${alarm.id}</td>
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
function renderUsersTable(users, currentUserId, isSuperAdmin) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">사용자가 없습니다.</td></tr>';
        return;
    }
    
    users.forEach(user => {
        let adminToggleBtn = '';
        
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
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.name || '-'}</td>
            <td>${user.email}</td>
            <td>${user.company_name || '-'}</td>
            <td>${user.phone_number || '-'}</td>
            <td>${formatDate(user.created_at)}</td>
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
