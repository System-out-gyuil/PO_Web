// 헤더 관련 JavaScript 함수들

// CSRF 토큰 가져오기 함수
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) {
        return token.value;
    }
    
    // 쿠키에서 CSRF 토큰 가져오기
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// 현재 사용자 ID 가져오기 함수
function getCurrentUserId() {
    // 서버에서 제공된 사용자 ID가 있다면 사용
    if (window.currentUserId) {
        return window.currentUserId;
    }
    
    // localStorage에서 사용자 ID 가져오기 (fallback)
    return localStorage.getItem('diary_user_id') || 'anonymous';
}

// 로그아웃 함수
function logout() {
    if (confirm('로그아웃하시겠습니까?')) {
        // 로그아웃 중임을 표시하는 플래그 설정
        window.isLoggingOut = true;
        
        // 모든 진행 중인 fetch 요청을 중단하기 위한 AbortController 생성
        if (window.currentAbortController) {
            window.currentAbortController.abort();
        }
        
        // 브라우저 캐시 정리
        if ('caches' in window) {
            caches.keys().then(function(names) {
                for (let name of names) {
                    caches.delete(name);
                }
            });
        }
        
        // 세션 스토리지 정리
        sessionStorage.clear();
        
        // 현재 사용자의 localStorage 데이터만 정리 (다른 사용자 데이터 보존)
        const currentUserId = getCurrentUserId();
        if (currentUserId && currentUserId !== 'anonymous') {
            // 사용자별 키로 저장된 데이터들 정리
            const keysToRemove = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.includes(`_${currentUserId}`)) {
                    keysToRemove.push(key);
                }
            }
            keysToRemove.forEach(key => localStorage.removeItem(key));
        }
        
        // 브라우저 히스토리 조작 - 뒤로가기 방지
        window.history.pushState(null, '', '/sales/login/');
        window.history.replaceState(null, '', '/sales/login/');
        
        // 서버에 로그아웃 요청
        fetch('/sales/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            // 응답이 JSON이 아닌 경우를 처리
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                // JSON이 아닌 경우 성공으로 처리하고 바로 리다이렉트
                return { success: true };
            }
        })
        .then(data => {
            if (data.success) {
                // 로그인 페이지로 리다이렉트
                window.location.replace('/sales/login/');
            } else {
                alert('로그아웃 중 오류가 발생했습니다: ' + (data.error || ''));
                // 오류가 발생해도 로그인 페이지로 리다이렉트
                window.location.replace('/sales/login/');
            }
        })
        .catch(error => {
            alert('로그아웃 중 오류가 발생했습니다.');
            // 오류가 발생해도 로그인 페이지로 리다이렉트
            window.location.replace('/sales/login/');
        });
    }
}

// 관리자 페이지 이동 함수
function goToAdminPage() {
    window.location.href = '/sales/diary_admin/board/';
}

// 게시판 이동 함수
function toBoard() {
    window.location.href = '/sales/diary_board/';
}

// 일반 게시판 이동 함수
function toGeneralBoard() {
    try {
        window.location.href = '/sales/board_list/';
    } catch (error) {
        console.error('게시판 이동 중 오류:', error);
        // 대안 방법
        window.open('/sales/board_list/', '_self');
    }
}

// 알림 패널 토글 함수
function toggleNotificationPanel() {
    console.log('알림 패널 토글 함수 호출');
    const panel = document.getElementById('notificationPanel');
    console.log(panel);
    
    // 현재 패널이 숨겨져 있는지 확인 (CSS 클래스 또는 인라인 스타일 모두 고려)
    const isHidden = panel.classList.contains('notification-panel-hidden') || 
                     panel.style.display === 'none' || 
                     panel.style.display === '';
    
    if (isHidden) {
        // 숨김 클래스 제거 및 표시
        panel.classList.remove('notification-panel-hidden');
        panel.style.display = 'block';
        loadNotifications();
    } else {
        // 숨김 클래스 추가 및 숨김
        panel.classList.add('notification-panel-hidden');
        panel.style.display = 'none';
    }
}

// 알림 목록 로드 함수
function loadNotifications() {
    if (window.isLoggingOut) {
        return;
    }
    
    const notificationList = document.getElementById('notificationList');
    
    // 서버에서 알림 데이터를 가져오는 API 호출
    fetch('/sales/diary_board/notifications/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (window.isLoggingOut) {
            throw new Error('로그아웃 중');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            renderNotifications(data.notifications);
            updateNotificationBadge(data.unread_count);
        } else {
            notificationList.innerHTML = '<div class="no-notifications">알림을 불러올 수 없습니다.</div>';
        }
    })
    .catch(error => {
        if (!window.isLoggingOut && error.message !== '로그아웃 중') {
            console.error('알림 로드 오류:', error);
            notificationList.innerHTML = '<div class="no-notifications">알림을 불러올 수 없습니다.</div>';
        }
    });
}

// 알림 표시 함수 (renderNotifications로 이름 변경)
function renderNotifications(notifications) {
    const notificationList = document.getElementById('notificationList');
    
    if (notifications.length === 0) {
        notificationList.innerHTML = '<div class="no-notifications">새로운 알림이 없습니다.</div>';
        return;
    }
    
    const notificationsHtml = notifications.map(notification => {
        // 새로운 content 구조에서 text만 추extraction
        let messageText = '';
        if (notification.message && typeof notification.message === 'object' && notification.message.text) {
            messageText = notification.message.text;
        } else if (typeof notification.message === 'string') {
            messageText = notification.message;
        } else {
            messageText = '내용 없음';
        }
        
        return `
            <div class="notification-item ${notification.is_read ? 'read' : 'unread'}" 
                 data-id="${notification.id}" 
                 data-alarm-id="${notification.alarm_id || ''}"
                 onclick="handleNotificationClick(${notification.id}, this, ${notification.alarm_id || 'null'})">
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${messageText}</div>
                    <div class="notification-time">${formatNotificationTime(notification.created_at)}</div>
                </div>
                ${!notification.is_read ? '<div class="unread-indicator"></div>' : ''}
            </div>
        `;
    }).join('');
    
    notificationList.innerHTML = notificationsHtml;
}

// 알림 읽음 처리 함수
function markAsRead(notificationId) {
    fetch(`/sales/diary_board/notifications/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 알림 배지 업데이트
            updateNotificationBadge(data.unread_count);
        }
    })
    .catch(error => {
        console.error('알림 읽음 처리 오류:', error);
    });
}

// 알림 배지 업데이트 함수
function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;
    
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'flex';
        badge.classList.remove('notification-badge-hidden');
    } else {
        badge.style.display = 'none';
        badge.classList.add('notification-badge-hidden');
    }
}

// 알림 배지 초기 업데이트 함수 (페이지 로드시 호출)
function updateNotificationBadgeOnLoad() {
    // 로그아웃 중이면 요청 중단
    if (window.isLoggingOut) {
        return;
    }
    
    fetch('/sales/diary_board/notifications/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        // 로그아웃 중이면 요청 중단
        if (window.isLoggingOut) {
            throw new Error('로그아웃 중');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            updateNotificationBadge(data.unread_count);
        }
    })
    .catch(error => {
        // 로그아웃 중이 아닐 때만 오류 로그 출력
        if (!window.isLoggingOut && error.message !== '로그아웃 중') {
            console.error('알림 배지 업데이트 오류:', error);
        }
    });
}

// 알림 시간 포맷 함수
function formatNotificationTime(timestamp) {
    const now = new Date();
    const notificationTime = new Date(timestamp);
    const diffInMinutes = Math.floor((now - notificationTime) / (1000 * 60));
    
    if (diffInMinutes < 1) {
        return '방금 전';
    } else if (diffInMinutes < 60) {
        return `${diffInMinutes}분 전`;
    } else if (diffInMinutes < 1440) {
        const hours = Math.floor(diffInMinutes / 60);
        return `${hours}시간 전`;
    } else {
        const days = Math.floor(diffInMinutes / 1440);
        return `${days}일 전`;
    }
}

// 알림 읽음 상태로 표시 함수 (diary_list.html 스타일)
function markNotificationRead(notificationId, element) {
    fetch(`/sales/diary_board/notifications/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // UI 업데이트
            element.classList.remove('unread');
            element.classList.add('read');
            const unreadIndicator = element.querySelector('.unread-indicator');
            if (unreadIndicator) {
                unreadIndicator.remove();
            }
            
            // 배지 업데이트
            const badge = document.getElementById('notificationBadge');
            if (badge) {
                const currentCount = parseInt(badge.textContent || '0');
                if (currentCount > 0) {
                    const newCount = currentCount - 1;
                    if (newCount === 0) {
                        badge.style.display = 'none';
                        badge.classList.add('notification-badge-hidden');
                    } else {
                        badge.textContent = newCount;
                    }
                }
            }
        }
    })
    .catch(error => {
        console.error('알림 읽음 상태 변경 오류:', error);
    });
}

// 알림 클릭 처리 함수
function handleNotificationClick(notificationId, element, alarmId) {
    // 먼저 읽음 상태로 표시
    markNotificationRead(notificationId, element);
    
    // 공지 ID가 있으면 해당 공지 상세페이지로 이동
    if (alarmId && alarmId !== 'null') {
        // 잠시 후 페이지 이동 (읽음 상태 업데이트가 완료된 후)
        setTimeout(() => {
            window.location.href = `/sales/diary_board/announcement/${alarmId}/detail/`;
        }, 300);
    }
}

// 문의하기 모달 열기 함수
function openInquiryModal() {
    // 문의하기 모달이 이미 있는지 확인하고 생성
    let modal = document.getElementById('inquiryModal');
    if (!modal) {
        modal = createInquiryModal();
        document.body.appendChild(modal);
    }
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// 문의하기 모달 생성 함수
function createInquiryModal() {
    const modal = document.createElement('div');
    modal.id = 'inquiryModal';
    modal.className = 'inquiry-modal';
    modal.innerHTML = `
        <div class="inquiry-modal-content">
            <div class="inquiry-header">
                <div class="inquiry-header-content">
                    <h2 class="inquiry-title">문의하기</h2>
                    <button type="button" class="inquiry-close" onclick="closeInquiryModal()">&times;</button>
                </div>
            </div>
            <div class="inquiry-body">
                <div class="inquiry-description">
                    궁금한 사항이나 문제가 있으시면 언제든지 문의해 주세요.
                </div>
                <form id="inquiryForm">
                    <div class="form-group">
                        <label for="inquiryContent" class="inquiry-content-label">문의 내용</label>
                        <textarea id="inquiryContent" class="inquiry-textarea" placeholder="문의 내용을 입력해주세요..." required></textarea>
                        <div class="inquiry-char-count">
                            <span id="charCount">0</span> / 1000
                        </div>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn-cancel" onclick="closeInquiryModal()">취소</button>
                        <button type="submit" class="btn-submit">문의하기</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    // 문의 내용 글자 수 카운트
    const textarea = modal.querySelector('#inquiryContent');
    const charCount = modal.querySelector('#charCount');
    
    textarea.addEventListener('input', function() {
        const length = this.value.length;
        charCount.textContent = length;
        
        if (length > 1000) {
            this.value = this.value.substring(0, 1000);
            charCount.textContent = 1000;
        }
    });
    
    // 폼 제출 처리
    const form = modal.querySelector('#inquiryForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        submitInquiry();
    });
    
    return modal;
}

// 문의하기 모달 닫기 함수
function closeInquiryModal() {
    const modal = document.getElementById('inquiryModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// 문의 제출 함수
function submitInquiry() {
    const content = document.getElementById('inquiryContent').value.trim();
    
    if (!content) {
        alert('문의 내용을 입력해주세요.');
        return;
    }
    
    const submitBtn = document.querySelector('.btn-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = '제출 중...';
    
    fetch('/sales/submit_inquiry/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('문의가 성공적으로 제출되었습니다. 빠른 시일 내에 답변 드리겠습니다.');
            closeInquiryModal();
            // 폼 초기화
            document.getElementById('inquiryContent').value = '';
            document.getElementById('charCount').textContent = '0';
        } else {
            alert('문의 제출에 실패했습니다: ' + (data.error || ''));
        }
    })
    .catch(error => {
        console.error('문의 제출 오류:', error);
        alert('문의 제출 중 오류가 발생했습니다.');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = '문의하기';
    });
}

// 메뉴 드롭다운 토글 함수
function toggleMenuDropdown() {
    const dropdown = document.getElementById('menuDropdown');
    
    if (!dropdown) {
        console.error('메뉴 드롭다운 요소를 찾을 수 없습니다.');
        return;
    }
    
    // 현재 드롭다운이 숨겨져 있는지 확인
    const isHidden = dropdown.classList.contains('menu-dropdown-hidden');
    
    if (isHidden) {
        // 드롭다운 표시
        dropdown.classList.remove('menu-dropdown-hidden');
    } else {
        // 드롭다운 숨김
        dropdown.classList.add('menu-dropdown-hidden');
    }
}

// 페이지 로드 시 헤더 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 이벤트 리스너 중복 등록 방지 플래그
    if (window.headerInitialized) {
        return;
    }
    window.headerInitialized = true;
    
    // 전역 함수로 만들어서 콘솔에서 테스트 가능하게 함
    window.testMenuToggle = toggleMenuDropdown;
    
    // 알림 버튼 클릭 이벤트 추가
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function(event) {
            event.stopPropagation(); // 이벤트 버블링 방지
            toggleNotificationPanel();
        });
    }
    
    // 메뉴 버튼 클릭 이벤트 추가
    const menuBtn = document.getElementById('menuBtn');
    if (menuBtn) {
        
        // 메뉴 클릭 핸들러 함수 정의
        const menuClickHandler = function(event) {
            event.stopPropagation(); // 이벤트 버블링 방지
            event.preventDefault(); // 기본 동작 방지
            toggleMenuDropdown();
        };
        
        // 이벤트 리스너 등록
        menuBtn.addEventListener('click', menuClickHandler);
    } else {
        console.error('메뉴 버튼을 찾을 수 없습니다!');
    }
    
    // 알림 배지 초기화
    updateNotificationBadgeOnLoad();
    
    // 알림 패널 및 메뉴 드롭다운 외부 클릭 시 닫기
    document.addEventListener('click', function(event) {
        const notificationContainer = document.querySelector('.notification-container');
        const notificationPanel = document.getElementById('notificationPanel');
        const menuContainer = document.querySelector('.menu-container');
        const menuDropdown = document.getElementById('menuDropdown');
        const notificationBtn = event.target.closest('.notification-btn');
        const menuBtn = event.target.closest('#menuBtn'); // 메뉴 버튼 클릭 감지 개선
        
        
        // 알림 패널이 현재 표시되어 있는지 확인 (CSS 클래스 또는 인라인 스타일 고려)
        const isPanelVisible = notificationPanel && 
                              !notificationPanel.classList.contains('notification-panel-hidden') &&
                              notificationPanel.style.display !== 'none';
        
        // 메뉴 드롭다운이 현재 표시되어 있는지 확인
        const isMenuVisible = menuDropdown && 
                             !menuDropdown.classList.contains('menu-dropdown-hidden');
        
        // 알림 패널 외부 클릭 시 닫기
        if (notificationContainer && notificationPanel && 
            !notificationContainer.contains(event.target) && 
            isPanelVisible) {
            notificationPanel.classList.add('notification-panel-hidden');
            notificationPanel.style.display = 'none';
        }
        
        // 메뉴 드롭다운 외부 클릭 시 닫기 (단, 메뉴 버튼 클릭이 아닌 경우에만)
        if (menuContainer && menuDropdown && 
            !menuContainer.contains(event.target) && 
            !menuBtn && // 메뉴 버튼 클릭이 아닌 경우만
            isMenuVisible) {
            menuDropdown.classList.add('menu-dropdown-hidden');
        }
        
        // diary_list.html과 호환성을 위한 추가 처리
        if (!notificationBtn && notificationPanel && isPanelVisible) {
            notificationPanel.classList.add('notification-panel-hidden');
            notificationPanel.style.display = 'none';
        }
    });
    
    // 일반 게시판 버튼 이벤트 리스너 추가
    const generalBoardBtn = document.getElementById('generalBoardBtn');
    if (generalBoardBtn) {
        generalBoardBtn.addEventListener('click', toGeneralBoard);
    }
    
    // ESC 키로 문의하기 모달 닫기
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modal = document.getElementById('inquiryModal');
            if (modal && modal.style.display === 'flex') {
                closeInquiryModal();
            }
        }
    });
});
