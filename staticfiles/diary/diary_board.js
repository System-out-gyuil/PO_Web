// 게시판 JavaScript

// 전역 변수
let currentPage = 1;
let currentSearchQuery = '';

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 공고 목록 로드
    loadAnnouncements();
    
    // 검색 이벤트 리스너
    const searchInput = document.getElementById('announcement-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchAnnouncements();
            }
        });
    }
});

// 공고 목록 로드
async function loadAnnouncements(page = 1) {
    const listContainer = document.getElementById('announcement-list');
    
    if (!listContainer) return;
    
    // 로딩 표시
    listContainer.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    try {
        const params = new URLSearchParams({
            search: currentSearchQuery,
            page: page
        });
        
        const response = await fetch(`/sales/diary_board/announcements/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderAnnouncements(data.announcements);
            renderPagination(data.pagination);
            currentPage = page;
        } else {
            showError('공고를 불러오는데 실패했습니다: ' + data.message);
        }
    } catch (error) {
        console.error('Error loading announcements:', error);
        showError('공고를 불러오는데 실패했습니다.');
    }
}

// 공고 목록 렌더링
function renderAnnouncements(announcements) {
    const listContainer = document.getElementById('announcement-list');
    
    if (!listContainer) return;
    
    if (announcements.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h5>공고가 없습니다</h5>
                <p>등록된 공고가 없거나 검색 결과가 없습니다.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    announcements.forEach(announcement => {
        const unreadClass = !announcement.is_read ? 'unread' : '';
        const fileBadge = announcement.file_count > 0 
            ? `<span class="file-badge"><i class="fas fa-paperclip"></i> ${announcement.file_count}개</span>` 
            : '';
        
        html += `
            <div class="announcement-item ${unreadClass}" onclick="viewAnnouncementDetail(${announcement.id})">
                <div class="announcement-header">
                    <h5 class="announcement-title">${escapeHtml(announcement.title)}</h5>
                    <div class="announcement-meta">
                        <span class="announcement-date">
                            <i class="fas fa-calendar-alt"></i> ${announcement.created_at}
                        </span>
                        ${fileBadge}
                    </div>
                </div>
                <div class="announcement-content">
                    ${escapeHtml(announcement.content)}
                </div>
                <div class="announcement-footer">
                    <span class="text-muted">
                        <i class="fas fa-eye"></i> 상세보기
                    </span>
                    <button class="view-btn" onclick="event.stopPropagation(); viewAnnouncementDetail(${announcement.id})">
                        <i class="fas fa-external-link-alt"></i> 보기
                    </button>
                </div>
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
}

// 페이지네이션 렌더링
function renderPagination(pagination) {
    const paginationContainer = document.getElementById('announcement-pagination');
    
    if (!paginationContainer) return;
    
    if (pagination.num_pages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 이전 페이지
    if (pagination.has_previous) {
        html += `
            <a href="#" class="page-button" onclick="loadAnnouncements(${pagination.previous_page_number})">
                <i class="fas fa-chevron-left"></i>
            </a>
        `;
    }
    
    // 페이지 번호
    const startPage = Math.max(1, pagination.number - 2);
    const endPage = Math.min(pagination.num_pages, pagination.number + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === pagination.number ? 'active' : '';
        html += `
            <a href="#" class="page-button ${activeClass}" onclick="loadAnnouncements(${i})">${i}</a>
        `;
    }
    
    // 다음 페이지
    if (pagination.has_next) {
        html += `
            <a href="#" class="page-button" onclick="loadAnnouncements(${pagination.next_page_number})">
                <i class="fas fa-chevron-right"></i>
            </a>
        `;
    }
    
    paginationContainer.innerHTML = html;
}

// 공고 검색
function searchAnnouncements() {
    const searchInput = document.getElementById('announcement-search');
    if (searchInput) {
        currentSearchQuery = searchInput.value.trim();
        loadAnnouncements(1);
    }
}

// 공고 새로고침
function refreshAnnouncements() {
    currentSearchQuery = '';
    const searchInput = document.getElementById('announcement-search');
    if (searchInput) {
        searchInput.value = '';
    }
    loadAnnouncements(1);
}

// 공고 상세보기 - 새 페이지로 이동
function viewAnnouncementDetail(announcementId) {
    window.location.href = `/sales/diary_board/announcement/${announcementId}/detail/`;
}

// 읽음 처리
async function markAsRead(announcementId) {
    try {
        await fetch(`/sales/diary_board/announcement/${announcementId}/mark-read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        
        // 목록에서 읽음 상태 업데이트
        const announcementItem = document.querySelector(`[onclick="viewAnnouncementDetail(${announcementId})"]`);
        if (announcementItem) {
            announcementItem.classList.remove('unread');
        }
    } catch (error) {
        console.error('Error marking as read:', error);
    }
}

// HTML 이스케이프
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 에러 표시
function showError(message) {
    const listContainer = document.getElementById('announcement-list');
    if (listContainer) {
        listContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                ${escapeHtml(message)}
            </div>
        `;
    }
}

// CSRF 토큰 가져오기
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
