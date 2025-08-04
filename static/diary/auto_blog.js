// 블로그 모달 관련 JavaScript

// 모달 HTML을 동적으로 생성
function createBlogModal() {
    const modalHTML = `
        <div id="blogModal" class="blog-modal" style="display: none;">
            <div class="blog-modal-content">
                <div class="blog-modal-header">
                    <h3>네이버 블로그 글쓰기</h3>
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
                        <h4 style="margin-bottom: 15px; color: #495057; font-size: 16px;">네이버 로그인 설정 (선택사항)</h4>
                        <small style="color: #6c757d; font-size: 12px; display: block; margin-bottom: 10px;">
                            입력하지 않아도 네이버 창에서 수동으로 로그인 가능합니다.
                        </small>
                        
                        <div class="setting-row" style="margin-bottom: 15px;">
                            <label for="naverId" style="display: block; margin-bottom: 5px; font-weight: 500; color: #495057;">
                                네이버 아이디
                            </label>
                            <input 
                                type="text" 
                                id="naverId" 
                                placeholder="네이버 아이디를 입력하세요 (선택사항)"
                                style="width: 100%; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; font-size: 14px;"
                            >
                        </div>
                        
                        <div class="setting-row" style="margin-bottom: 15px;">
                            <label for="naverPassword" style="display: block; margin-bottom: 5px; font-weight: 500; color: #495057;">
                                네이버 비밀번호
                            </label>
                            <input 
                                type="password" 
                                id="naverPassword" 
                                placeholder="네이버 비밀번호를 입력하세요 (선택사항)"
                                style="width: 100%; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; font-size: 14px;"
                            >
                        </div>
                    </div>
                </div>
                <div class="blog-modal-footer">
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

{/* <div class="text-input-area" style="margin-top: 20px;">
                        <label for="blogTextInput" style="display: block; margin-bottom: 8px; font-weight: 500; color: #495057;">
                            추가 텍스트 입력 (선택사항)
                        </label>
                        <textarea 
                            id="blogTextInput" 
                            placeholder="여기에 추가 텍스트를 입력하세요..."
                            style="width: 100%; min-height: 100px; padding: 12px; border: 1px solid #dee2e6; border-radius: 6px; resize: vertical; font-family: inherit; font-size: 14px;"
                        ></textarea>
                    </div> */}

// 블로그 모달 열기
function openBlogModal() {
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
    const naverId = naverIdInput.value;
    const naverPassword = naverPasswordInput.value;
    
    if (files.length === 0 && !typoProbability && !typingSpeed && !naverId && !naverPassword) {
        alert('파일 또는 타이핑 설정을 입력해주세요.');
        return;
    }
    
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
    if (typoProbability) {
        formData.append('typo_probability', typoProbability);
    }
    if (typingSpeed) {
        formData.append('typing_speed', typingSpeed);
    }
    if (naverId) {
        formData.append('naver_id', naverId);
    }
    if (naverPassword) {
        formData.append('naver_password', naverPassword);
    }
    
    // 서버로 파일 업로드
    fetch('/sales/upload_blog_file/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 성공 메시지 표시
            showNotification(data.message, 'success');
            
            // 파일 정보 콘솔에 출력
            console.log('업로드된 파일 개수:', data.file_count);
            console.log('업로드된 파일 정보들:', data.file_infos);
            if (data.content_preview) {
                console.log('파일 내용 미리보기:', data.content_preview);
            }
            if (data.text_content) {
                console.log('입력된 텍스트:', data.text_content);
            }
            
            // 추가 정보 표시
            console.log('블로그 작성이 윈도우 환경에서 시작되었습니다.');
            console.log('Chrome 브라우저가 곧 열릴 예정입니다.');
            
            // 모달 닫기
            closeBlogModal();
        } else {
            // 오류 메시지 표시
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('업로드 오류:', error);
        showNotification('파일 업로드 중 오류가 발생했습니다.', 'error');
    })
    .finally(() => {
        // 업로드 버튼 상태 복원
        uploadBtn.textContent = originalText;
        uploadBtn.disabled = false;
    });
}

// 알림 메시지 표시 함수
function showNotification(message, type = 'info') {
    // 기존 알림 제거
    const existingNotification = document.querySelector('.blog-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // 새 알림 생성
    const notification = document.createElement('div');
    notification.className = `blog-notification blog-notification-${type}`;
    notification.textContent = message;
    
    // 스타일 적용
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
        max-width: 400px;
        word-wrap: break-word;
    `;
    
    // 타입별 색상 설정
    if (type === 'success') {
        notification.style.backgroundColor = '#28a745';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#dc3545';
    } else {
        notification.style.backgroundColor = '#17a2b8';
    }
    
    // 알림 추가
    document.body.appendChild(notification);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 3000);
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
    }
});
