// 게시판 목록 로드
async function loadBoards(page = 1, search = '') {
    try {
        const params = new URLSearchParams({
            page: page,
            search: search
        });
        
        const response = await fetch(`/sales/board/api/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderBoards(data.boards);
            renderPagination(data.pagination);
        } else {
            showError('게시글을 불러오는데 실패했습니다: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading boards:', error);
        showError('게시글을 불러오는데 실패했습니다.');
    }
}

// 게시글 목록 렌더링
function renderBoards(boards) {
    const boardList = document.getElementById('board-list');
    
    if (!boardList) return;
    
    if (boards.length === 0) {
        boardList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comments"></i>
                <h5>게시글이 없습니다</h5>
                <p>첫 번째 게시글을 작성해보세요.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    boards.forEach(board => {
        const createdDate = new Date(board.created_at).toLocaleDateString('ko-KR');
        const contentPreview = board.content.length > 300 ? 
            board.content.substring(0, 300) + '...' : board.content;
        
        html += `
            <div class="board-item" onclick="viewBoardDetail(${board.id})">
                <div class="board-header-info">
                    <div>
                        <div class="board-title">${escapeHtml(board.title)}</div>
                        <div class="board-meta">
                            <span>
                                <i class="fas fa-user"></i> ${escapeHtml(board.author_name)}
                            </span>
                            <span>
                                <i class="fas fa-calendar-alt"></i> ${createdDate}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="board-content">
                    <p>${escapeHtml(contentPreview)}</p>
                </div>
                ${board.files && board.files.length > 0 ? `
                    <div class="board-files">
                        <i class="fas fa-paperclip"></i> 첨부파일 ${board.files.length}개
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    boardList.innerHTML = html;
}

// 페이지네이션 렌더링
function renderPagination(pagination) {
    const paginationContainer = document.getElementById('board-pagination');
    
    if (!paginationContainer) return;
    
    if (pagination.num_pages <= 1) {
        paginationContainer.style.display = 'none';
        paginationContainer.innerHTML = '';
        return;
    }
    
    paginationContainer.style.display = 'flex';
    
    let html = '';
    
    // 이전 페이지
    if (pagination.has_previous) {
        html += `<a href="#" class="page-button" onclick="loadBoards(${pagination.previous_page_number})">
            <i class="fas fa-chevron-left"></i>
        </a>`;
    }
    
    // 페이지 번호
    const startPage = Math.max(1, pagination.number - 2);
    const endPage = Math.min(pagination.num_pages, pagination.number + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === pagination.number ? 'active' : '';
        html += `<a href="#" class="page-button ${activeClass}" onclick="loadBoards(${i})">${i}</a>`;
    }
    
    // 다음 페이지
    if (pagination.has_next) {
        html += `<a href="#" class="page-button" onclick="loadBoards(${pagination.next_page_number})">
            <i class="fas fa-chevron-right"></i>
        </a>`;
    }
    
    paginationContainer.innerHTML = html;
}

// 게시글 검색
function searchBoards() {
    const searchInput = document.getElementById('board-search');
    const searchTerm = searchInput ? searchInput.value.trim() : '';
    loadBoards(1, searchTerm);
}

// 게시글 상세보기
function viewBoardDetail(boardId) {
    window.location.href = `/sales/board/${boardId}/`;
}

// 에러 표시
function showError(message) {
    const boardList = document.getElementById('board-list');
    if (boardList) {
        boardList.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                ${escapeHtml(message)}
            </div>
        `;
    }
}

// HTML 이스케이프 함수
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 게시글 작성 모달 표시
function showWriteBoardModal() {
    const modal = document.getElementById('writeBoardModal');
    modal.style.display = 'block';
    
    // 폼 초기화
    document.getElementById('board-title-input').value = '';
    document.getElementById('board-content-input').value = '';
    document.getElementById('fileList').innerHTML = '';
    document.getElementById('uploadProgress').style.display = 'none';
    
    // 제목 입력 필드에 포커스
    document.getElementById('board-title-input').focus();
    
    // 파일 업로드 설정
    setupFileUpload();
}

// 게시글 작성 모달 닫기
function closeWriteBoardModal() {
    const modal = document.getElementById('writeBoardModal');
    modal.style.display = 'none';
}

// 파일 업로드 설정
function setupFileUpload() {
    const fileInput = document.getElementById('board-file-input');
    const fileList = document.getElementById('fileList');
    
    // 파일 선택 이벤트
    fileInput.addEventListener('change', handleFileSelect);
    
    // 드래그 앤 드롭 이벤트
    const uploadSection = document.querySelector('.file-upload-section');
    
    uploadSection.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadSection.style.borderColor = '#667eea';
    });
    
    uploadSection.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadSection.style.borderColor = '#dee2e6';
    });
    
    uploadSection.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadSection.style.borderColor = '#dee2e6';
        
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
}

// 파일 선택 처리
function handleFileSelect(event) {
    const files = event.target.files;
    handleFiles(files);
}

// 파일 처리
function handleFiles(files) {
    const fileList = document.getElementById('fileList');
    
    Array.from(files).forEach(file => {
        // 파일 크기 제한 (10MB)
        if (file.size > 200 * 1024 * 1024) {
            alert(`파일 크기가 너무 큽니다: ${file.name}`);
            return;
        }
        
        // 파일 아이템 생성
        const fileItem = createFileItem(file);
        fileList.appendChild(fileItem);
    });
}

// 파일 아이템 생성
function createFileItem(file) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.dataset.fileName = file.name;
    fileItem.dataset.fileSize = file.size;
    
    const fileIcon = getFileIcon(file.name);
    const fileSize = formatFileSize(file.size);
    
    fileItem.innerHTML = `
        <div class="file-info">
            <div class="file-icon">
                ${fileIcon}
            </div>
            <div>
                <div class="file-name">${escapeHtml(file.name)}</div>
                <div class="file-size">${fileSize}</div>
            </div>
        </div>
        <button class="file-remove" onclick="removeFile(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    return fileItem;
}

// 파일 제거
function removeFile(button) {
    const fileItem = button.parentElement;
    fileItem.remove();
}

// 파일 아이콘 반환
function getFileIcon(fileName) {
    const fileExt = fileName.split('.').pop()?.toLowerCase() || '';
    
    const iconMap = {
        // 이미지 파일
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'bmp': '🖼️', 'svg': '🖼️', 'webp': '🖼️',
        // 문서 파일
        'pdf': '📄', 'doc': '📝', 'docx': '📝', 'txt': '📄', 'rtf': '📝',
        // 스프레드시트
        'xls': '📊', 'xlsx': '📊', 'csv': '📊',
        // 프레젠테이션
        'ppt': '📋', 'pptx': '📋',
        // 압축 파일
        'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
        // 오디오 파일
        'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵', 'ogg': '🎵',
        // 비디오 파일
        'mp4': '🎬', 'avi': '🎬', 'mov': '🎬', 'wmv': '🎬', 'flv': '🎬', 'mkv': '🎬',
        // 코드 파일
        'html': '🌐', 'css': '🎨', 'js': '⚙️', 'py': '🐍', 'java': '☕', 'cpp': '⚙️', 'c': '⚙️',
        // 기타
        'json': '📋', 'xml': '📋', 'sql': '🗄️', 'md': '📄'
    };
    
    return iconMap[fileExt] || '📄';
}

// 파일 크기 포맷팅
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// // 게시글 작성 제출
// async function submitBoard() {
//     const title = document.getElementById('board-title-input').value.trim();
//     const content = document.getElementById('board-content-input').value.trim();
    
//     // 유효성 검사
//     if (!title) {
//         alert('제목을 입력해주세요.');
//         document.getElementById('board-title-input').focus();
//         return;
//     }
    
//     if (!content) {
//         alert('내용을 입력해주세요.');
//         document.getElementById('board-content-input').focus();
//         return;
//     }
    
//     // 제출 버튼 비활성화
//     const submitBtn = document.querySelector('.btn-submit');
//     const originalText = submitBtn.textContent;
//     submitBtn.disabled = true;
//     submitBtn.textContent = '작성 중...';
    
//     try {
//         // 파일 업로드 처리
//         const fileItems = document.querySelectorAll('#fileList .file-item');
//         let uploadedFiles = [];
        
//         if (fileItems.length > 0) {
//             // 업로드 진행률 표시
//             document.getElementById('uploadProgress').style.display = 'block';
//             const progressBar = document.getElementById('progressBar');
            
//             for (let i = 0; i < fileItems.length; i++) {
//                 const fileItem = fileItems[i];
//                 const fileName = fileItem.dataset.fileName;
                
//                 // 파일 객체 찾기
//                 const fileInput = document.getElementById('board-file-input');
//                 const file = Array.from(fileInput.files).find(f => f.name === fileName);
                
//                 if (file) {
//                     // 진행률 업데이트
//                     const progress = ((i + 1) / fileItems.length) * 100;
//                     progressBar.style.width = progress + '%';
                    
//                     // 파일 업로드
//                     const formData = new FormData();
//                     formData.append('file', file);
                    
//                     const uploadResponse = await fetch('/sales/board/upload-file/', {
//                         method: 'POST',
//                         headers: {
//                             'X-CSRFToken': getCookie('csrftoken')
//                         },
//                         body: formData
//                     });
                    
//                     const uploadData = await uploadResponse.json();
                    
//                     if (uploadData.success) {
//                         uploadedFiles.push(uploadData.file);
//                     } else {
//                         alert(`파일 업로드 실패: ${fileName}`);
//                     }
//                 }
//             }
//         }
        
//         // 게시글 
//         console.log(321)
//         const response = await fetch('/sales/board/create/', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//                 'X-CSRFToken': getCookie('csrftoken')
//             },
//             body: JSON.stringify({
//                 title: title,
//                 content: content,
//                 files: uploadedFiles
//             })
//         });
        
//         const data = await response.json();
        
//         if (data.success) {
//             alert('게시글이 작성되었습니다.');
//             closeWriteBoardModal();
//             // 게시글 목록 새로고침
//             loadBoards();
//         } else {
//             alert('게시글 작성에 실패했습니다: ' + data.error);
//         }
//     } catch (error) {
//         console.error('Error submitting board:', error);
//         alert('게시글 작성 중 오류가 발생했습니다.');
//     } finally {
//         // 제출 버튼 다시 활성화
//         submitBtn.disabled = false;
//         submitBtn.textContent = originalText;
//         document.getElementById('uploadProgress').style.display = 'none';
//     }
// }

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

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('writeBoardModal');
    if (event.target === modal) {
        closeWriteBoardModal();
    }
}

// Enter 키로 검색
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        const searchInput = document.getElementById('board-search');
        if (document.activeElement === searchInput) {
            event.preventDefault();
            searchBoards();
        }
    }
    
    // Ctrl + Enter로 게시글 제출
    if (event.key === 'Enter' && event.ctrlKey) {
        const modal = document.getElementById('writeBoardModal');
        if (modal.style.display === 'block') {
            event.preventDefault();
            submitBoard();
        }
    }
}); 