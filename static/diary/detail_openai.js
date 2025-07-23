// AI 대화 기능 관련 JavaScript

// AI 캐시 관리 전역 변수
window.aiCacheManager = {
    // 현재 행의 캐시 정보
    currentRowCache: null,
    // 파일 변경사항 추적
    fileChanges: {
        added: [],
        modified: [],
        deleted: []
    },
    // 캐시 무효화 플래그
    cacheInvalidated: false
};

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
        
        // AI 캐시 매니저 초기화
        initializeAICacheManager();
        
        // 현재 행 정보 표시
        displayCurrentRowInfo();
        
        openAIChatModal();
    } else {
        alert('현재 행 정보를 찾을 수 없습니다. 상세보기를 다시 열어주세요.');
    }
}

// AI 캐시 매니저 초기화
function initializeAICacheManager() {
    const rowId = window.currentDetailRowId;
    if (!rowId) return;
    
    // 기존 캐시 정보가 있으면 유지, 없으면 초기화
    if (!window.aiCacheManager || window.aiCacheManager.currentRowCache?.rowId !== rowId) {
        window.aiCacheManager = {
            currentRowCache: {
                rowId: rowId,
                lastUpdate: Date.now(),
                fileHashes: {},
                dataHash: null,
                // 파일 변경사항 추적을 위한 추가 정보
                initialFileCount: 0,
                currentFileCount: 0
            },
            fileChanges: {
                added: [],
                modified: [],
                deleted: []
            },
            cacheInvalidated: false
        };
        console.log('AI 캐시 매니저 새로 초기화 완료:', rowId);
    } else {
        console.log('AI 캐시 매니저 기존 데이터 유지:', rowId);
        console.log('현재 변경사항:', {
            added: window.aiCacheManager.fileChanges.added.length,
            modified: window.aiCacheManager.fileChanges.modified.length,
            deleted: window.aiCacheManager.fileChanges.deleted.length,
            cacheInvalidated: window.aiCacheManager.cacheInvalidated
        });
        
        // 기존 변경사항이 있으면 로깅
        if (window.aiCacheManager.fileChanges.deleted.length > 0) {
            console.log('유지되는 삭제된 파일들:');
            window.aiCacheManager.fileChanges.deleted.forEach((file, index) => {
                console.log(`  ${index + 1}: ${file.fieldName} - ${file.fileName || file.fileInfo?.original_filename}`);
            });
        }
    }
}

// 파일 변경사항 추적 함수
function trackFileChange(rowId, fieldName, changeType, fileInfo = null) {
    if (!window.aiCacheManager || window.aiCacheManager.currentRowCache?.rowId !== rowId) {
        console.log('AI 캐시 매니저가 초기화되지 않았거나 다른 행입니다:', rowId);
        return; // 다른 행이거나 캐시 매니저가 초기화되지 않음
    }

    const fileHash = fileInfo?.file_hash || fileInfo?.hash || null;
    const fileName = fileInfo?.original_filename || fileInfo?.filename || null;
    const s3Key = fileInfo?.s3_key || null;

    // 삭제 이벤트일 때, added/modified에서 해당 파일 제거
    if (changeType === 'deleted') {
        ['added', 'modified'].forEach(type => {
            window.aiCacheManager.fileChanges[type] = window.aiCacheManager.fileChanges[type].filter(f => {
                return !(
                    (f.fileInfo?.original_filename === fileName) ||
                    (fileHash && f.fileInfo?.file_hash === fileHash) ||
                    (s3Key && f.fileInfo?.s3_key === s3Key)
                );
            });
        });
    }

    const change = {
        fieldName: fieldName,
        timestamp: Date.now(),
        fileInfo: fileInfo,
        fileHash: fileHash,
        fileName: fileName,
        s3Key: s3Key,
        // 서버 파일 정보
        s3Key: fileInfo?.s3_key || null,
        downloadUrl: fileInfo?.download_url || null,
        previewUrl: fileInfo?.preview_url || null,
        originalFilename: fileInfo?.original_filename || fileInfo?.filename || null
    };

    switch (changeType) {
        case 'added':
            window.aiCacheManager.fileChanges.added.push(change);
            console.log(`파일 추가 추적: ${fieldName} - ${change.originalFilename || '알 수 없는 파일'}`);
            break;
        case 'modified':
            window.aiCacheManager.fileChanges.modified.push(change);
            console.log(`파일 수정 추적: ${fieldName} - ${change.originalFilename || '알 수 없는 파일'}`);
            break;
        case 'deleted':
            window.aiCacheManager.fileChanges.deleted.push(change);
            console.log(`파일 삭제 추적: ${fieldName}`);
            break;
    }

    // 캐시 무효화 플래그 설정
    window.aiCacheManager.cacheInvalidated = true;

    console.log(`파일 변경사항 추적: ${changeType} - ${fieldName}`, change);
    console.log('현재 AI 캐시 상태:', {
        added: window.aiCacheManager.fileChanges.added.length,
        modified: window.aiCacheManager.fileChanges.modified.length,
        deleted: window.aiCacheManager.fileChanges.deleted.length,
        cacheInvalidated: window.aiCacheManager.cacheInvalidated
    });
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
        
        // AI 캐시 매니저 정리
        cleanupAICacheManager();
    }
}

// AI 캐시 매니저 정리
function cleanupAICacheManager() {
    window.aiCacheManager = {
        currentRowCache: null,
        fileChanges: {
            added: [],
            modified: [],
            deleted: []
        },
        dataChanges: {},
        cacheInvalidated: false
    };
    console.log('AI 캐시 매니저 정리 완료');
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
    
    // AI 캐시 매니저가 초기화되지 않은 경우 초기화
    if (!window.aiCacheManager || window.aiCacheManager.currentRowCache?.rowId !== rowId) {
        console.log('sendAIMessage에서 AI 캐시 매니저 초기화:', rowId);
        initializeAICacheManager();
    }
    
    // 변경사항 정보 수집
    const changes = {
        fileChanges: window.aiCacheManager?.fileChanges || { added: [], modified: [], deleted: [] },
        cacheInvalidated: window.aiCacheManager?.cacheInvalidated || false
    };
    
    // 변경사항 로깅
    console.log('AI 메시지 전송 - 변경사항 정보:', {
        rowId: rowId,
        message: message,
        forceRefresh: forceRefresh,
        changes: changes,
        addedFiles: changes.fileChanges.added.length,
        modifiedFiles: changes.fileChanges.modified.length,
        deletedFiles: changes.fileChanges.deleted.length,
        cacheInvalidated: changes.cacheInvalidated
    });
    
    // AI 캐시 매니저 상태 상세 로깅
    if (window.aiCacheManager) {
        console.log('AI 캐시 매니저 상태:', {
            currentRowId: window.aiCacheManager.currentRowCache?.rowId,
            addedFiles: window.aiCacheManager.fileChanges.added.map(f => f.fileInfo?.original_filename),
            modifiedFiles: window.aiCacheManager.fileChanges.modified.map(f => f.fileInfo?.original_filename),
            deletedFiles: window.aiCacheManager.fileChanges.deleted.map(f => f.fileName || f.fileInfo?.original_filename),
            cacheInvalidated: window.aiCacheManager.cacheInvalidated
        });
        
        // 삭제된 파일 정보 상세 로깅
        if (window.aiCacheManager.fileChanges.deleted.length > 0) {
            console.log('삭제된 파일 상세 정보:');
            window.aiCacheManager.fileChanges.deleted.forEach((deletedFile, index) => {
                console.log(`  삭제된 파일 ${index + 1}:`, {
                    fieldName: deletedFile.fieldName,
                    fileName: deletedFile.fileName,
                    fileInfo: deletedFile.fileInfo
                });
            });
        }
    } else {
        console.log('AI 캐시 매니저가 초기화되지 않음');
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
            force_refresh: forceRefresh,
            changes: changes
        }),
        // 타임아웃 설정 (5분)
        signal: AbortSignal.timeout(300000)
    })
    .then(response => {
        // 응답 상태 코드 확인
        if (!response.ok) {
            if (response.status === 504) {
                throw new Error('서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.');
            } else {
                throw new Error(`서버 오류 (${response.status}): ${response.statusText}`);
            }
        }
        
        // Content-Type 확인
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('서버에서 JSON 응답을 받지 못했습니다. 잠시 후 다시 시도해주세요.');
        }
        
        return response.json();
    })
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
            
            // 캐시 업데이트 성공 시 변경사항 초기화
            if (data.cache_updated) {
                resetAICacheChanges();
            }
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

// AI 캐시 변경사항 초기화
function resetAICacheChanges() {
    if (window.aiCacheManager) {
        const previousState = {
            added: window.aiCacheManager.fileChanges.added.length,
            modified: window.aiCacheManager.fileChanges.modified.length,
            deleted: window.aiCacheManager.fileChanges.deleted.length,
            cacheInvalidated: window.aiCacheManager.cacheInvalidated
        };
        
        window.aiCacheManager.fileChanges = {
            added: [],
            modified: [],
            deleted: []
        };
        window.aiCacheManager.cacheInvalidated = false;
        
        console.log('AI 캐시 변경사항 초기화 완료:', {
            previous: previousState,
            current: {
                added: 0,
                modified: 0,
                deleted: 0,
                cacheInvalidated: false
            }
        });
    }
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
window.trackFileChange = trackFileChange;
window.resetAICacheChanges = resetAICacheChanges;