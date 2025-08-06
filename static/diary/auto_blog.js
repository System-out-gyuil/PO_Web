// 블로그 모달 관련 JavaScript

// 모바일 디바이스 감지 함수
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
           || window.innerWidth <= 768;
}

// 실시간 미리보기 모달 관련 변수 (전역 객체에 안전하게 저장)
window.blogStatusInterval = window.blogStatusInterval || null;
window.previewModal = window.previewModal || null;
window.blogCompletionNotified = window.blogCompletionNotified || false;
window.currentProgress = window.currentProgress || 0;
// 제목 입력 완료 상태 추적을 위한 변수 추가
window.titleInputCompleted = window.titleInputCompleted || false;
window.currentTypingMode = window.currentTypingMode || null; // 'title' or 'body'
// 블로그 작성 활성 상태 및 완료 메시지 추가 상태 추적
window.isBlogWritingActive = window.isBlogWritingActive || false;
window.completionMessageAdded = window.completionMessageAdded || false;

// 모달 HTML을 동적으로 생성
function createBlogModal() {
    const modalHTML = `
        <div id="blogModal" class="blog-modal" style="display: none;">
            <div class="blog-modal-content">
                <div class="blog-modal-header">
                    <h3>블로그 파일 업로드</h3>
                    <span class="blog-modal-close" onclick="closeBlogModal()">&times;</span>
                </div>
                <div class="blog-modal-body">
                    <div class="file-upload-area">
                        <input type="file" id="blogFileInput" accept=".txt" multiple style="display: none;">
                        <div class="file-drop-zone" onclick="document.getElementById('blogFileInput').click()">
                            <div class="file-drop-text">
                                <i class="fas fa-cloud-upload-alt" style="font-size: 48px; color: #6c757d; margin-bottom: 10px;"></i>
                                <p>클릭하여 파일 선택 또는 파일을 여기에 드래그하세요</p>
                                <p style="font-size: 12px; color: #6c757d;">(.txt 파일만 지원, 여러 파일 선택 가능)</p>
                            </div>
                        </div>
                        <div id="selectedFileInfo" style="display: none; margin-top: 10px;">
                            <p><strong>선택된 파일들:</strong></p>
                            <div id="fileList" style="max-height: 200px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px; background-color: #f8f9fa;"></div>
                        </div>
                    </div>
                    
                    <div class="typing-settings" style="margin-top: 20px;">
                        <h4 style="margin-bottom: 15px; color: #495057; font-size: 16px;">타이핑 설정</h4>
                        
                        <div class="setting-row" style="margin-bottom: 15px;">
                            <label for="typoProbability" style="display: block; margin-bottom: 5px; font-weight: 500; color: #495057;">
                                오타 확률 (0~1)
                            </label>
                            <input 
                                type="number" 
                                id="typoProbability" 
                                min="0" 
                                max="1" 
                                step="0.1" 
                                value="0.1"
                                style="width: 100%; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; font-size: 14px;"
                            >
                            <small style="color: #6c757d; font-size: 12px;">0: 오타 없음, 1: 항상 오타</small>
                        </div>
                        
                        <div class="setting-row" style="margin-bottom: 15px;">
                            <label for="typingSpeed" style="display: block; margin-bottom: 5px; font-weight: 500; color: #495057;">
                                타자 속도 (0~1, n초마다 타이핑)
                            </label>
                            <input 
                                type="number" 
                                id="typingSpeed" 
                                min="0" 
                                max="1" 
                                step="0.1" 
                                value="0.05"
                                style="width: 100%; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; font-size: 14px;"
                            >
                            <small style="color: #6c757d; font-size: 12px;">0: 매우 빠름, 1: 매우 느림</small>
                        </div>
                    </div>
                    
                    <div class="login-settings" style="margin-top: 20px;">
                        <h4 style="margin-bottom: 15px; color: #495057; font-size: 16px;">네이버 로그인 설정 (필수)</h4>
                        <small style="color: #dc3545; font-size: 12px; display: block; margin-bottom: 10px; font-weight: bold;">
                            네이버 아이디와 비밀번호를 반드시 정확하게 입력해주세요. 
                        </small>
                        
                        <div class="setting-row" style="margin-bottom: 15px;">
                            <label for="naverId" style="display: block; margin-bottom: 5px; font-weight: 500; color: #495057;">
                                네이버 아이디 <span style="color: #dc3545;">*</span>
                            </label>
                            <input 
                                type="text" 
                                id="naverId" 
                                placeholder="네이버 아이디를 입력하세요"
                                required
                                style="width: 100%; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; font-size: 14px;"
                            >
                            <div id="naverIdError" class="error-message" style="color: #dc3545; font-size: 12px; margin-top: 5px; display: none;">
                                네이버 아이디를 입력해주세요.
                            </div>
                        </div>
                        
                        <div class="setting-row" style="margin-bottom: 15px;">
                            <label for="naverPassword" style="display: block; margin-bottom: 5px; font-weight: 500; color: #495057;">
                                네이버 비밀번호 <span style="color: #dc3545;">*</span>
                            </label>
                            <input 
                                type="password" 
                                id="naverPassword" 
                                placeholder="네이버 비밀번호를 입력하세요"
                                required
                                style="width: 100%; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; font-size: 14px;"
                            >
                            <div id="naverPasswordError" class="error-message" style="color: #dc3545; font-size: 12px; margin-top: 5px; display: none;">
                                네이버 비밀번호를 입력해주세요.
                            </div>
                        </div>
                    </div>
                </div>
                <div class="blog-modal-footer">
                    <button class="btn btn-info" onclick="openPreviewModal()" style="margin-right: 10px;">🔍 미리보기 창 열기</button>
                    <button class="btn btn-secondary" onclick="closeBlogModal()">취소</button>
                    <button class="btn btn-primary" onclick="uploadBlogFile()" id="uploadBtn" disabled>업로드</button>
                </div>
            </div>
        </div>
    `;
    
    // 모달이 이미 존재하지 않으면 추가
    if (!document.getElementById('blogModal')) {
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
}

// 실시간 미리보기 모달 생성
function createPreviewModal() {
    const previewModalHTML = `
        <div id="blogPreviewModal" class="blog-preview-modal" style="display: none; position: fixed; top: 20px; right: 20px; width: 600px; height: 800px; background: white; border: 2px solid #007bff; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 10000; font-family: Arial, sans-serif;">
            <div class="preview-modal-header" style="background: #007bff; color: white; padding: 15px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; font-size: 16px;">블로그 작성 미리보기</h4>
                <button onclick="closePreviewModal()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">&times;</button>
            </div>
            <div class="preview-modal-body" style="padding: 15px; height: calc(100% - 60px); overflow-y: auto;">
                <div id="previewStatus" style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span id="previewStep" style="font-weight: bold; color: #495057;">준비 중...</span>
                        <span id="previewProgress" style="font-size: 12px; color: #6c757d;">0%</span>
                    </div>
                    <div style="background: #e9ecef; border-radius: 10px; height: 8px; margin-bottom: 10px;">
                        <div id="previewProgressBar" style="background: #007bff; height: 100%; border-radius: 10px; width: 0%; transition: width 0.3s ease;"></div>
                    </div>
                    
                    <!-- 로그 영역 추가 -->
                    <div style="margin-bottom: 15px;">
                        <h5 style="margin: 0 0 8px 0; font-size: 14px; color: #495057;">📋 진행 로그</h5>
                        <div id="previewLog" style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 10px; max-height: 150px; overflow-y: auto; font-size: 12px; line-height: 1.4;">
                            <div style="color: #6c757d; font-style: italic;">블로그 작성을 시작합니다...</div>
                        </div>
                    </div>
                </div>
                
                <div id="previewContent" style="border: 1px solid #dee2e6; border-radius: 6px; padding: 10px; background: #f8f9fa; min-height: 200px;">
                    <div id="previewTitle" style="font-weight: bold; color: #495057; margin-bottom: 10px; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #007bff;">
                        <span style="font-size: 12px; color: #6c757d;">제목:</span><br>
                        <span id="previewTitleText">제목이 여기에 표시됩니다...</span>
                    </div>
                    <div id="previewBody" style="display: flex; flex-direction: column; color: #495057; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #28a745; min-height: 150px; white-space: pre-wrap; font-family: monospace; font-size: 13px; line-height: 1.4;">
                        <span style="font-size: 12px; color: #6c757d; font-family: Arial;">본문:</span><br>
                        <span id="previewBodyText">본문이 여기에 실시간으로 표시됩니다...</span>
                    </div>
                </div>
                
                <div id="previewFileInfo" style="margin-top: 15px; font-size: 12px; color: #6c757d;">
                    <div>📁 <span id="currentFileInfo">파일 정보가 여기에 표시됩니다</span></div>
                </div>
            </div>
        </div>
    `;
    
    if (!document.getElementById('blogPreviewModal')) {
        document.body.insertAdjacentHTML('beforeend', previewModalHTML);
    }
}

// 블로그 모달 열기
function openBlogModal() {
    // 모바일 디바이스 체크
    if (isMobileDevice()) {
        showNotification('모바일 환경에서는 블로그 작성 기능을 사용할 수 없습니다.', 'warning');
        return;
    }
    
    createBlogModal();
    const modal = document.getElementById('blogModal');
    modal.style.display = 'flex';
    
    // 파일 입력 이벤트 리스너 설정
    const fileInput = document.getElementById('blogFileInput');
    fileInput.onchange = handleFileSelection;
    
    // 드래그 앤 드롭 이벤트 설정
    const dropZone = document.querySelector('.file-drop-zone');
    dropZone.ondragover = handleDragOver;
    dropZone.ondrop = handleFileDrop;
    
    // 네이버 로그인 필드 실시간 유효성 검사
    const naverIdInput = document.getElementById('naverId');
    const naverPasswordInput = document.getElementById('naverPassword');
    const naverIdError = document.getElementById('naverIdError');
    const naverPasswordError = document.getElementById('naverPasswordError');
    
    // 네이버 아이디 실시간 검사
    naverIdInput.addEventListener('input', function() {
        if (this.value.trim()) {
            this.style.border = '1px solid #dee2e6';
            naverIdError.style.display = 'none';
        } else {
            this.style.border = '2px solid #dc3545';
            naverIdError.style.display = 'block';
        }
    });
    
    // 네이버 비밀번호 실시간 검사
    naverPasswordInput.addEventListener('input', function() {
        if (this.value.trim()) {
            this.style.border = '1px solid #dee2e6';
            naverPasswordError.style.display = 'none';
        } else {
            this.style.border = '2px solid #dc3545';
            naverPasswordError.style.display = 'block';
        }
    });
}

// 블로그 모달 닫기
function closeBlogModal() {
    const modal = document.getElementById('blogModal');
    if (modal) {
        modal.style.display = 'none';
        // 파일 입력 초기화
        document.getElementById('blogFileInput').value = '';
        document.getElementById('selectedFileInfo').style.display = 'none';
        document.getElementById('uploadBtn').disabled = true;
        // 타이핑 설정 초기화
        document.getElementById('typoProbability').value = '0.1';
        document.getElementById('typingSpeed').value = '0.05';
        // 네이버 로그인 설정 초기화
        document.getElementById('naverId').value = '';
        document.getElementById('naverPassword').value = '';
    }
}

// 실시간 미리보기 모달 열기
function openPreviewModal(startPolling = false) {
    createPreviewModal();
    const modal = document.getElementById('blogPreviewModal');
    modal.style.display = 'block';
    
    // startPolling이 true일 때만 블로그 작성 활성화 및 폴링 시작
    if (startPolling) {
        // 진행도와 완료 알림 플래그 초기화
        window.currentProgress = 0;
        window.blogCompletionNotified = false;
        // 제목 입력 완료 상태 초기화
        window.titleInputCompleted = false;
        window.currentTypingMode = null;
        // 블로그 작성 상태 초기화
        window.isBlogWritingActive = true;
        window.completionMessageAdded = false;
        
        // 로그 초기화
        clearPreviewLog();
        
        // 실시간 상태 업데이트 시작
        startStatusPolling();
    } else {
        // 블로그 작성 중이 아닐 때는 폴링하지 않음
        window.isBlogWritingActive = false;
        
        // 기본 메시지 표시
        const logContainer = document.getElementById('previewLog');
        if (logContainer) {
            logContainer.innerHTML = '<div style="color: #6c757d; font-style: italic;">현재 블로그 작성 중이 아닙니다. 블로그 업로드를 시작하면 실시간 진행상황이 여기에 표시됩니다.</div>';
        }
        
        const stepElement = document.getElementById('previewStep');
        if (stepElement) {
            stepElement.textContent = '대기 중...';
        }
        
        const progressElement = document.getElementById('previewProgress');
        const progressBarElement = document.getElementById('previewProgressBar');
        if (progressElement && progressBarElement) {
            progressElement.textContent = '0%';
            progressBarElement.style.width = '0%';
        }
    }
}

// 실시간 미리보기 모달 닫기
function closePreviewModal() {
    const modal = document.getElementById('blogPreviewModal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // 상태 폴링 중지 및 작업 상태 비활성화
    window.isBlogWritingActive = false;
    stopStatusPolling();
}

// 상태 폴링 시작
function startStatusPolling() {
    // 기존 폴링이 있으면 중지
    stopStatusPolling();
    
    // 즉시 한 번 실행
    updatePreviewStatus();
    
    // 0.5초마다 상태 업데이트
    window.blogStatusInterval = setInterval(updatePreviewStatus, 200);
}

// 상태 폴링 중지
function stopStatusPolling() {
    if (window.blogStatusInterval) {
        clearInterval(window.blogStatusInterval);
        window.blogStatusInterval = null;
    }
}

// 로그에 메시지 추가하는 함수
function addToPreviewLog(message, type = 'info') {
    const logContainer = document.getElementById('previewLog');
    if (!logContainer) return;
    
    const timestamp = new Date().toLocaleTimeString('ko-KR', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
    
    const logEntry = document.createElement('div');
    logEntry.style.marginBottom = '4px';
    logEntry.style.paddingLeft = '8px';
    logEntry.style.borderLeft = '3px solid';
    
    // 타입에 따른 색상 설정
    switch (type) {
        case 'success':
            logEntry.style.borderLeftColor = '#28a745';
            logEntry.style.color = '#155724';
            break;
        case 'error':
            logEntry.style.borderLeftColor = '#dc3545';
            logEntry.style.color = '#721c24';
            break;
        case 'warning':
            logEntry.style.borderLeftColor = '#ffc107';
            logEntry.style.color = '#856404';
            break;
        default:
            logEntry.style.borderLeftColor = '#007bff';
            logEntry.style.color = '#495057';
    }
    
    logEntry.innerHTML = `<span style="color: #6c757d; font-size: 11px;">[${timestamp}]</span> ${message}`;
    
    logContainer.appendChild(logEntry);
    
    // 자동 스크롤
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // 로그 항목이 너무 많으면 오래된 것 제거 (최대 50개)
    const logEntries = logContainer.children;
    if (logEntries.length > 50) {
        logContainer.removeChild(logEntries[0]);
    }
}

// 로그 초기화 함수
function clearPreviewLog() {
    const logContainer = document.getElementById('previewLog');
    if (logContainer) {
        logContainer.innerHTML = '<div style="color: #6c757d; font-style: italic;">블로그 작성을 시작합니다...</div>';
    }
}

// 미리보기 상태 업데이트
function updatePreviewStatus() {
    // 블로그 작성이 비활성 상태면 폴링 중지
    if (!window.isBlogWritingActive) {
        stopStatusPolling();
        return;
    }
    
    fetch('/sales/get_blog_status/')
        .then(response => {
            console.log('🔍 [DEBUG] API 응답 상태:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP 오류! 상태: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('🔍 [DEBUG] API 응답 데이터:', data);
            if (data.success && data.status) {
                const status = data.status;
                
                // 단계 표시 업데이트 (오타 관련 메시지 필터링)
                const stepElement = document.getElementById('previewStep');
                const progressElement = document.getElementById('previewProgress');
                const progressBarElement = document.getElementById('previewProgressBar');
                const titleElement = document.getElementById('previewTitleText');
                const bodyElement = document.getElementById('previewBodyText');
                const fileInfoElement = document.getElementById('currentFileInfo');
                
                if (stepElement && status.title) {
                    // 오타 관련 제목은 표시하지 않음
                    const isTypoTitle = status.title.includes('오타') || 
                                       status.title.includes('오타 수정중') || 
                                       status.title.includes('오타 발생');
                    
                    if (!isTypoTitle) {
                        stepElement.textContent = status.title;
                    }
                    // 오타 관련 메시지일 때는 이전 상태 유지 (업데이트하지 않음)
                }
                
                // 로그에 메시지 추가 (중복 방지를 위해 마지막 메시지와 비교)
                if (status.content) {
                    const logContainer = document.getElementById('previewLog');
                    const lastLogEntry = logContainer ? logContainer.lastElementChild : null;
                    const lastMessage = lastLogEntry ? lastLogEntry.textContent.replace(/^\[\d{2}:\d{2}:\d{2}\]\s/, '') : '';
                    
                    const isBodyContent = status.step === 'typing' || 
                                         status.step === 'typing_with_typos' || 
                                         status.step === 'typing_title' ||
                                         status.step === 'typing_body' ||
                                         status.step === 'typing_typo' || 
                                         status.step === 'typing_body_typo' ||
                                         status.step === 'typing_correction' ||
                                         status.step === 'typing_body_correction';
                    
                    const isTypoMessage = status.content.includes('오타 발생') || 
                                         status.content.includes('오타 수정중') ||
                                         status.content.includes('백스페이스');
                    
                    // 중복 방지 로직 강화: 정확한 메시지 내용과 단계 모두 확인
                    const isDuplicate = (
                        status.content === lastMessage || 
                        (status.step === 'title_input_start' && lastMessage.includes('제목 입력 중')) ||
                        (status.step === 'content_input_start' && lastMessage.includes('본문 입력 중')) ||
                        (isBodyContent && (lastMessage === '제목을 입력하고 있습니다...' || lastMessage === '본문을 입력하고 있습니다...'))
                    );
                    
                    // 중복되지 않고 오타 메시지가 아닌 경우만 로그에 추가
                    if (!isDuplicate && !isTypoMessage) {
                        if (isBodyContent) {
                            // 본문 타이핑 중일 때는 일반적인 상태 메시지만 추가
                            if (status.content.includes('"')) {
                                if (lastMessage !== '제목을 입력하고 있습니다...') {
                                    addToPreviewLog('제목을 입력하고 있습니다...');
                                }
                            } else {
                                if (lastMessage !== '본문을 입력하고 있습니다...') {
                                    addToPreviewLog('본문을 입력하고 있습니다...');
                                }
                            }
                        } else {
                            // 일반 상태 메시지
                            let logType = 'info';
                            if (status.step === 'login_failed' || status.step === 'global_error' || status.step === 'file_error') {
                                logType = 'error';
                            } else if (status.step === 'all_complete' || status.step === 'save_complete') {
                                logType = 'success';
                            }
                            addToPreviewLog(status.content, logType);
                        }
                    }
                }
                
                if (progressElement && progressBarElement) {
                    const progress = status.progress || 0;
                    
                    // 진행도가 현재보다 높을 때만 업데이트 (뒤로 가지 않음)
                    if (progress >= window.currentProgress) {
                        window.currentProgress = progress;
                        progressElement.textContent = `${progress}%`;
                        progressBarElement.style.width = `${progress}%`;
                    }
                }
                
                // 파일 정보 업데이트
                if (fileInfoElement && status.total_files > 0) {
                    fileInfoElement.textContent = `${status.current_file}/${status.total_files} 파일 처리 중`;
                }
                
                // 단계별 상태에 따른 내용 업데이트 (실시간 타이핑 포함)
                switch (status.step) {
                    case 'title_input_start':
                        // 제목 입력 시작 - 타이핑 모드를 제목으로 설정
                        window.currentTypingMode = 'title';
                        window.titleInputCompleted = false;
                        break;
                        
                    case 'content_input_start':
                        // 본문 입력 시작 - 타이핑 모드를 본문으로 설정
                        window.currentTypingMode = 'body';
                        break;
                        
                    case 'typing_title':
                        // 제목 타이핑 중
                        if (!window.titleInputCompleted && titleElement && status.content) {
                            if (status.content.includes('"')) {
                                const match = status.content.match(/"([^"]+)"/);
                                if (match) {
                                    titleElement.textContent = match[1];
                                }
                            } else {
                                titleElement.textContent = status.content;
                            }
                        }
                        break;
                        
                    case 'typing_body':
                        // 본문 타이핑 중
                        if (bodyElement && status.content) {
                            // 따옴표로 감싸인 내용이면 추출, 아니면 그대로 사용
                            let contentToShow = status.content;
                            if (contentToShow.includes('"')) {
                                const match = contentToShow.match(/"([^"]+)"/);
                                if (match) {
                                    contentToShow = match[1];
                                }
                            }
                            bodyElement.textContent = contentToShow;
                        }
                        break;
                        
                    case 'typing':
                    case 'typing_with_typos':
                        // 기존 호환성을 위한 fallback (현재 타이핑 모드에 따라 제목 또는 본문 업데이트)
                        if (window.currentTypingMode === 'title' && !window.titleInputCompleted && titleElement) {
                            // 제목 타이핑 중
                            if (status.content && status.content.includes('"')) {
                                const match = status.content.match(/"([^"]+)"/);
                                if (match) {
                                    titleElement.textContent = match[1];
                                }
                            }
                        } else if (window.currentTypingMode === 'body' && bodyElement) {
                            // 본문 타이핑 중 (오타 관련 메시지가 아닌 경우만)
                            if (status.content && !status.content.includes('오타') && !status.content.includes('백스페이스')) {
                                // 따옴표로 감싸인 내용이면 추출, 아니면 그대로 사용
                                let contentToShow = status.content;
                                if (contentToShow.includes('"')) {
                                    const match = contentToShow.match(/"([^"]+)"/);
                                    if (match) {
                                        contentToShow = match[1];
                                    }
                                }
                                bodyElement.textContent = contentToShow;
                            }
                        }
                        break;
                        
                    case 'typing_body_typo':
                    case 'typing_typo':
                        // 본문 오타 발생 시
                        if (bodyElement && status.content) {
                            // 실제 타이핑된 텍스트만 추출 (오타 메시지 제외)
                            const cleanContent = status.content.replace(/오타 발생.*$/, '').trim();
                            if (cleanContent) {
                                bodyElement.textContent = cleanContent;
                            }
                        }
                        break;
                        
                    case 'typing_body_correction':
                    case 'typing_correction':
                        // 본문 오타 수정 중
                        if (bodyElement && status.content) {
                            const cleanContent = status.content.replace(/오타 수정중.*$/, '').replace(/백스페이스.*$/, '').trim();
                            if (cleanContent) {
                                bodyElement.textContent = cleanContent;
                            }
                        }
                        break;
                        
                    case 'title_input_complete':
                        // 제목 입력 완료 - 제목 완료 상태로 변경
                        window.titleInputCompleted = true;
                        window.currentTypingMode = null;
                        if (titleElement && status.content) {
                            // FINAL_TITLE: 접두사가 있으면 최종 제목 내용을 표시
                            if (status.content.startsWith('FINAL_TITLE:')) {
                                const finalTitle = status.content.replace('FINAL_TITLE:', '');
                                titleElement.textContent = finalTitle;
                                addToPreviewLog(`제목 입력 완료: "${finalTitle}"`, 'success');
                            } else {
                                // 기존 방식 (호환성)
                                titleElement.textContent = status.content;
                                addToPreviewLog(`제목 입력 완료: "${status.content}"`, 'success');
                            }
                        }
                        break;
                        
                    case 'content_input_complete':
                        // 본문 입력 완료 - 최종 내용이 있으면 본문에 표시, 없으면 로그에만 추가
                        window.currentTypingMode = null;
                        if (bodyElement && status.content) {
                            // FINAL_CONTENT: 접두사가 있으면 최종 본문 내용을 표시
                            if (status.content.startsWith('FINAL_CONTENT:')) {
                                const finalContent = status.content.replace('FINAL_CONTENT:', '');
                                bodyElement.textContent = finalContent;
                                addToPreviewLog(`본문 입력 완료 (${finalContent.length}자)`, 'success');
                            } else {
                                // 기존 방식 (호환성)
                                const match = status.content.match(/총 (\d+)자 입력 완료/);
                                if (match) {
                                    addToPreviewLog(`본문 입력 완료 (${match[1]}자)`, 'success');
                                }
                            }
                        }
                        break;
                        
                    case 'save_complete':
                        // 저장 완료 메시지도 본문 영역에 추가하지 않음 (로그에만 표시)
                        break;
                        
                    case 'all_complete':
                        // 모든 작업 완료 시
                        window.isBlogWritingActive = false; // 작업 완료로 설정하여 폴링 중지
                        
                        if (!window.blogCompletionNotified) {
                            window.blogCompletionNotified = true;
                            setTimeout(() => {
                                showNotification('모든 블로그 글 작성이 완료되었습니다!', 'success');
                                // 3초 후 폴링 완전 중지
                                setTimeout(() => {
                                    stopStatusPolling();
                                }, 3000);
                            }, 3000);
                        }
                        break;
                        
                    case 'login_failed':
                    case 'global_error':
                    case 'file_error':
                        // 오류 발생 시
                        window.isBlogWritingActive = false; // 오류 시에도 폴링 중지
                        
                        if (stepElement) {
                            stepElement.style.color = '#dc3545';
                        }
                        if (progressBarElement) {
                            progressBarElement.style.background = '#dc3545';
                        }
                        // 5초 후 모달 자동 닫기
                        setTimeout(() => {
                            closePreviewModal();
                            showNotification(status.content || '오류가 발생했습니다.', 'error');
                        }, 5000);
                        break;
                }
            }
        })
        .catch(error => {
            console.error('🔍 [DEBUG] 상태 조회 오류:', error);
            console.error('🔍 [DEBUG] 오류 상세:', error.message);
            // 에러 발생 시에도 폴링 중지
            window.isBlogWritingActive = false;
            stopStatusPolling();
        });
}

// 파일 선택 처리
function handleFileSelection(event) {
    const files = event.target.files;
    if (files.length > 0) {
        validateAndDisplayFiles(files);
    }
}

// 드래그 오버 처리
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.style.borderColor = '#007bff';
    event.currentTarget.style.backgroundColor = '#f8f9fa';
}

// 파일 드롭 처리
function handleFileDrop(event) {
    event.preventDefault();
    const dropZone = event.currentTarget;
    dropZone.style.borderColor = '#dee2e6';
    dropZone.style.backgroundColor = 'white';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        document.getElementById('blogFileInput').files = files;
        validateAndDisplayFiles(files);
    }
}

// 선택된 파일 정보 표시
function displaySelectedFiles(files) {
    const fileListDiv = document.getElementById('fileList');
    fileListDiv.innerHTML = ''; // 기존 내용 지우기
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileInfo = document.createElement('div');
        fileInfo.className = 'selected-file-info';
        fileInfo.innerHTML = `
            <span>${file.name}</span>
            <span>${formatFileSize(file.size)}</span>
        `;
        fileListDiv.appendChild(fileInfo);
    }
    document.getElementById('selectedFileInfo').style.display = 'block';
    document.getElementById('uploadBtn').disabled = false;
}

// 파일 유효성 검사 및 표시
function validateAndDisplayFiles(files) {
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInfo = document.getElementById('selectedFileInfo');
    const fileListDiv = document.getElementById('fileList');
    
    fileListDiv.innerHTML = ''; // 기존 내용 지우기
    
    let hasValidFiles = false;
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 파일 확장자 검사
        if (!file.name.toLowerCase().endsWith('.txt')) {
            alert(`파일 "${file.name}"은(는) 텍스트 파일(.txt)이 아닙니다.`);
            continue;
        }
        
        // 파일 크기 검사 (10MB 제한)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            alert(`파일 "${file.name}"의 크기가 10MB를 초과합니다.`);
            continue;
        }
        
        // 유효한 파일 정보 표시
        const fileInfoDiv = document.createElement('div');
        fileInfoDiv.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            margin: 4px 0;
            background-color: white;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        `;
        fileInfoDiv.innerHTML = `
            <span style="font-weight: 500; color: #495057;">${file.name}</span>
            <span style="color: #6c757d; font-size: 12px;">${formatFileSize(file.size)}</span>
        `;
        fileListDiv.appendChild(fileInfoDiv);
        
        hasValidFiles = true;
    }
    
    if (hasValidFiles) {
        fileInfo.style.display = 'block';
        uploadBtn.disabled = false;
    } else {
        fileInfo.style.display = 'none';
        uploadBtn.disabled = true;
    }
}

// 파일 크기 포맷팅
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 파일 업로드 처리
function uploadBlogFile() {
    const fileInput = document.getElementById('blogFileInput');
    const files = fileInput.files;
    const typoProbabilityInput = document.getElementById('typoProbability');
    const typingSpeedInput = document.getElementById('typingSpeed');
    const naverIdInput = document.getElementById('naverId');
    const naverPasswordInput = document.getElementById('naverPassword');
    
    const typoProbability = typoProbabilityInput.value;
    const typingSpeed = typingSpeedInput.value;
    const naverId = naverIdInput.value.trim();
    const naverPassword = naverPasswordInput.value.trim();
    
    // 유효성 검사 초기화
    let isValid = true;
    
    // 네이버 아이디 검사
    const naverIdError = document.getElementById('naverIdError');
    if (!naverId) {
        naverIdInput.style.border = '2px solid #dc3545';
        naverIdError.style.display = 'block';
        isValid = false;
    } else {
        naverIdInput.style.border = '1px solid #dee2e6';
        naverIdError.style.display = 'none';
    }
    
    // 네이버 비밀번호 검사
    const naverPasswordError = document.getElementById('naverPasswordError');
    if (!naverPassword) {
        naverPasswordInput.style.border = '2px solid #dc3545';
        naverPasswordError.style.display = 'block';
        isValid = false;
    } else {
        naverPasswordInput.style.border = '1px solid #dee2e6';
        naverPasswordError.style.display = 'none';
    }
    
    // 파일 검사 (최소 1개 파일 필요)
    if (files.length === 0) {
        alert('업로드할 파일을 선택해주세요.');
        isValid = false;
    }
    
    // 유효성 검사 실패 시 중단
    if (!isValid) {
        return;
    }
    
    // 알림 권한 요청 (유효성 검사 통과 후)
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('알림 권한이 허용되었습니다.');
                proceedWithUpload();
            } else {
                console.log('알림 권한이 거부되었지만 업로드를 계속 진행합니다.');
                proceedWithUpload();
            }
        });
    } else {
        // 이미 권한이 있거나 알림을 지원하지 않는 경우 바로 업로드 진행
        proceedWithUpload();
    }
    
    // 실제 업로드 처리 함수
    function proceedWithUpload() {
        // 업로드 버튼 비활성화 및 로딩 표시
        const uploadBtn = document.getElementById('uploadBtn');
        const originalText = uploadBtn.textContent;
        uploadBtn.textContent = '업로드 중...';
        uploadBtn.disabled = true;
        
        // FormData 객체 생성
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]); // 파일 여러 개 처리
        }
        formData.append('typo_probability', typoProbability);
        formData.append('typing_speed', typingSpeed);
        formData.append('naver_id', naverId);
        formData.append('naver_password', naverPassword);
        
        // 모달 닫기 및 백그라운드 작업 알림 표시
        closeBlogModal();
        
        // 실시간 미리보기 모달 열기
        openPreviewModal(true); // 폴링 시작
        
        showNotification('백그라운드에서 블로그 작성을 시작합니다. 실시간 미리보기를 확인하세요!', 'info');
        
        // 서버로 파일 업로드
        fetch('/sales/upload_blog_file/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('🔍 [DEBUG] 업로드 API 응답 상태:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP 오류! 상태: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('🔍 [DEBUG] 업로드 API 응답 데이터:', data);
            if (data.success) {
                // 성공 메시지 표시 - 미리보기 모달에서 자동으로 처리됨
                // showNotification(data.message, 'success', true);
                showBrowserNotification(data.message, '블로그 작성 완료');
                
                // 작업 완료 상태로 설정
                window.isBlogWritingActive = false;
                
                // 파일 정보 콘솔에 출력
                console.log('업로드된 파일 개수:', data.file_count);
                console.log('업로드된 파일 정보들:', data.file_infos);
                if (data.content_preview) {
                    console.log('파일 내용 미리보기:', data.content_preview);
                }
                if (data.text_content) {
                    console.log('입력된 텍스트:', data.text_content);
                }
                
                // 업로드 버튼 복원
                const uploadBtn = document.getElementById('uploadBtn');
                if (uploadBtn) {
                    uploadBtn.textContent = '업로드';
                    uploadBtn.disabled = false;
                }
            } else {
                // 오류 메시지 표시
                showNotification(data.error, 'error');
                
                // 오류 시에도 작업 비활성화
                window.isBlogWritingActive = false;
                
                // 미리보기 모달 닫기
                closePreviewModal();
                
                // 오류 시에도 업로드 버튼 복원
                const uploadBtn = document.getElementById('uploadBtn');
                if (uploadBtn) {
                    uploadBtn.textContent = '업로드';
                    uploadBtn.disabled = false;
                }
            }
        })
        .catch(error => {
            console.error('업로드 오류:', error);
            showNotification('파일 업로드 중 오류가 발생했습니다.', 'error');
            
            // 오류 시에도 작업 비활성화
            window.isBlogWritingActive = false;
            
            // 미리보기 모달 닫기
            closePreviewModal();
            
            // 오류 시에도 업로드 버튼 복원
            const uploadBtn = document.getElementById('uploadBtn');
            if (uploadBtn) {
                uploadBtn.textContent = '업로드';
                uploadBtn.disabled = false;
            }
        });
    }
}

// 페이지 로드 시 블로그 div에 클릭 이벤트 추가
document.addEventListener('DOMContentLoaded', function() {
    // 블로그 div 찾기
    const blogDiv = document.querySelector('.filter-controls div:last-child');
    if (blogDiv) {
        blogDiv.style.cursor = 'pointer';
        blogDiv.onclick = openBlogModal;
    }
});

// 모달 외부 클릭 시 닫기
document.addEventListener('click', function(event) {
    const modal = document.getElementById('blogModal');
    if (modal && event.target === modal) {
        closeBlogModal();
    }
});

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeBlogModal();
        closePreviewModal();
    }
});

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', function() {
    stopStatusPolling();
});