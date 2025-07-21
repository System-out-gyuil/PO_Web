// AI 대화 기능 관련 JavaScript

// AI 대화 모달 열기
function openAIChatModal() {
    const modal = document.getElementById('aiChatModal');
    if (modal) {
        modal.style.display = 'flex';
        
        // 입력창에 포커스
        setTimeout(() => {
            const input = document.getElementById('aiChatInput');
            if (input) {
                input.focus();
            }
        }, 100);
    }
}

// 상세 모달에서 AI 대화 모달 열기 (현재 행 ID 설정)
function openAIChatModalFromDetail() {
    // 현재 행 ID가 설정되어 있는지 확인
    if (window.currentDetailRowId) {
        console.log('AI 채팅 모달 열기 - 행 ID:', window.currentDetailRowId);
        
        // 현재 행 정보 표시
        displayCurrentRowInfo();
        
        openAIChatModal();
    } else {
        alert('현재 행 정보를 찾을 수 없습니다. 상세보기를 다시 열어주세요.');
    }
}

// 현재 행 정보 표시
function displayCurrentRowInfo() {
    const rowInfoDiv = document.getElementById('aiChatRowInfo');
    const rowDataDiv = document.getElementById('aiChatRowData');
    
    if (rowInfoDiv && rowDataDiv && window.currentDetailRowId) {
        // 현재 행의 기본 정보 표시
        const rowId = window.currentDetailRowId;
        rowDataDiv.innerHTML = `행 ID: ${rowId}`;
        rowInfoDiv.style.display = 'block';
        
        // 추가로 회사명이나 주요 정보가 있다면 표시
        const detailContent = document.getElementById('detailModalContent');
        if (detailContent) {
            const companyName = detailContent.querySelector('.company-name');
            if (companyName) {
                rowDataDiv.innerHTML += ` | 회사: ${companyName.textContent}`;
            }
        }
    }
}

// AI 대화 모달 닫기
function closeAIChatModal() {
    const modal = document.getElementById('aiChatModal');
    if (modal) {
        modal.style.display = 'none';
        
        // 입력창 초기화
        const input = document.getElementById('aiChatInput');
        if (input) {
            input.value = '';
        }
        
        // 로딩 상태 해제
        const loadingDiv = document.getElementById('aiChatLoading');
        const sendBtn = document.getElementById('sendAIBtn');
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
        if (sendBtn) {
            sendBtn.disabled = false;
        }
        
        // 행 정보 숨기기
        const rowInfoDiv = document.getElementById('aiChatRowInfo');
        if (rowInfoDiv) {
            rowInfoDiv.style.display = 'none';
        }
        
        // 대화 내용 초기화
        const messagesContainer = document.getElementById('aiChatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div style="text-align:center;color:#6c757d;padding:20px;">
                    AI와 대화를 시작해보세요!<br>
                    영업 관련 질문이나 도움이 필요한 내용을 자유롭게 물어보세요.
                </div>
            `;
        }
    }
}

// AI 메시지 전송
function sendAIMessage(forceRefresh = false) {
    const input = document.getElementById('aiChatInput');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) {
        return;
    }
    
    // 사용자 메시지 추가
    addAIMessage(message, 'user');
    input.value = '';
    
    // 로딩 상태 표시
    const loadingDiv = document.getElementById('aiChatLoading');
    const sendBtn = document.getElementById('sendAIBtn');
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
    }
    if (sendBtn) {
        sendBtn.disabled = true;
    }
    
    // 현재 행 ID 가져오기 (상세 모달에서 사용)
    let rowId = null;
    if (window.currentDetailRowId) {
        rowId = window.currentDetailRowId;
    }
    
    // OpenAI API 호출
    fetch('/sales/ai_chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            message: message,
            row_id: rowId,
            force_refresh: forceRefresh
        })
    })
    .then(response => response.json())
    .then(data => {
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
        if (sendBtn) {
            sendBtn.disabled = false;
        }
        
        if (data.success) {
            // AI 응답 추가
            addAIMessage(data.response, 'assistant');
        } else {
            // 오류 메시지 추가
            addAIMessage('죄송합니다. 응답을 생성하는 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
        }
    })
    .catch(error => {
        console.error('AI 채팅 오류:', error);
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
        if (sendBtn) {
            sendBtn.disabled = false;
        }
        addAIMessage('네트워크 오류가 발생했습니다. 다시 시도해주세요.', 'error');
    });
}

// 캐시 새로고침과 함께 메시지 전송
function sendAIMessageWithRefresh() {
    // 현재 행 ID 가져오기
    let rowId = null;
    if (window.currentDetailRowId) {
        rowId = window.currentDetailRowId;
    }
    if (!rowId) {
        sendAIMessage(true); // fallback
        return;
    }
    // 캐시 삭제 요청
    fetch('/sales/ai_chat_cache_clear/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ row_id: rowId })
    })
    .then(response => response.json())
    .then(data => {
        // 캐시 삭제 후 메시지 전송
        sendAIMessage();
    })
    .catch(error => {
        // 실패해도 그냥 메시지 전송
        sendAIMessage();
    });
}

// AI 메시지 추가
function addAIMessage(message, type) {
    const messagesContainer = document.getElementById('aiChatMessages');
    if (!messagesContainer) return;
    
    // 초기 안내 메시지 제거
    const initialMessage = messagesContainer.querySelector('div[style*="text-align:center"]');
    if (initialMessage) {
        initialMessage.remove();
    }
    
    // 새 메시지 요소 생성
    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-message ${type}`;
    
    // AI 응답인 경우 마크다운 렌더링 적용
    if (type === 'assistant') {
        // 안전한 마크다운 렌더링
        messageDiv.innerHTML = renderMarkdownSafely(message);
    } else {
        // 사용자 메시지나 오류 메시지는 일반 텍스트로 처리
        messageDiv.textContent = message;
    }
    
    // 메시지 추가
    messagesContainer.appendChild(messageDiv);
    
    // 스크롤을 맨 아래로
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// AI 채팅 키보드 이벤트 처리
function handleAIChatKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendAIMessage();
    }
}

// CSRF 토큰 가져오기 함수
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// 안전한 HTML 처리 함수
function sanitizeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

// 안전한 마크다운 렌더링
function renderMarkdownSafely(text) {
    if (typeof marked === 'undefined') {
        // marked 라이브러리가 없으면 기본 텍스트 처리
        return text.replace(/\n/g, '<br>');
    }
    
    try {
        // 마크다운 렌더링
        const html = marked.parse(text);
        
        // 기본적인 XSS 방지 (script 태그 제거)
        return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    } catch (error) {
        console.error('마크다운 렌더링 오류:', error);
        // 오류 발생 시 기본 텍스트 처리
        return text.replace(/\n/g, '<br>');
    }
}

// 페이지 로드 시 AI 모달 이벤트 바인딩
document.addEventListener('DOMContentLoaded', function() {
    // 마크다운 설정
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,  // 줄바꿈 허용
            gfm: true,     // GitHub Flavored Markdown
            sanitize: false // HTML 허용 (XSS 방지는 다른 방법으로)
        });
    }
    
    const aiChatModal = document.getElementById('aiChatModal');
    if (aiChatModal) {
        aiChatModal.onclick = function(e) {
            if (e.target === this) {
                closeAIChatModal();
            }
        };
    }
    
    // AI 채팅 입력창 이벤트 바인딩
    const aiChatInput = document.getElementById('aiChatInput');
    if (aiChatInput) {
        aiChatInput.addEventListener('keydown', handleAIChatKeydown);
    }
});

// 전역 함수로 노출
window.openAIChatModal = openAIChatModal;
window.openAIChatModalFromDetail = openAIChatModalFromDetail;
window.closeAIChatModal = closeAIChatModal;
window.sendAIMessage = sendAIMessage;
window.sendAIMessageWithRefresh = sendAIMessageWithRefresh;
window.handleAIChatKeydown = handleAIChatKeydown;
window.displayCurrentRowInfo = displayCurrentRowInfo;
window.renderMarkdownSafely = renderMarkdownSafely;