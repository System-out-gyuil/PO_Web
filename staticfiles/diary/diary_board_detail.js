// 일반 게시판 관련 함수들

// 일반 게시판 목록 로드
async function loadGeneralBoards(page = 1, search = '') {
    try {
        const params = new URLSearchParams({
            page: page,
            search: search
        });
        
        const response = await fetch(`/sales/diary_board/general/?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderGeneralBoards(data.boards);
            renderGeneralPagination(data.pagination);
        } else {
            showGeneralError('게시글을 불러오는데 실패했습니다: ' + data.message);
        }
    } catch (error) {
        console.error('Error loading general boards:', error);
        showGeneralError('게시글을 불러오는데 실패했습니다.');
    }
}

// 일반 게시판 목록 렌더링
function renderGeneralBoards(boards) {
    const boardList = document.getElementById('general-board-list');
    
    if (!boardList) return;
    
    if (boards.length === 0) {
        boardList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clipboard-list"></i>
                <h3>게시글이 없습니다</h3>
                <p>첫 번째 게시글을 작성해보세요.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    boards.forEach(board => {
        const createdDate = new Date(board.created_at).toLocaleDateString('ko-KR');
        const contentPreview = board.content.length > 100 ? 
            board.content.substring(0, 100) + '...' : board.content;
        
        html += `
            <div class="board-item" onclick="viewBoardDetail(${board.id})">
                <div class="board-header">
                    <h3 class="board-title">${escapeHtml(board.title)}</h3>
                    <div class="board-meta">
                        <span class="board-author">${escapeHtml(board.author_name)}</span>
                        <span class="board-date">${createdDate}</span>
                    </div>
                </div>
                <div class="board-content">
                    <p>${escapeHtml(contentPreview)}</p>
                </div>
            </div>
        `;
    });
    
    boardList.innerHTML = html;
}

// 일반 게시판 페이지네이션 렌더링
function renderGeneralPagination(pagination) {
    const paginationContainer = document.getElementById('general-pagination');
    
    if (!paginationContainer) return;
    
    if (pagination.num_pages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 이전 페이지
    if (pagination.has_previous) {
        html += `<a href="#" class="page-button" onclick="loadGeneralBoards(${pagination.previous_page_number})">
            <i class="fas fa-chevron-left"></i>
        </a>`;
    }
    
    // 페이지 번호
    const startPage = Math.max(1, pagination.number - 2);
    const endPage = Math.min(pagination.num_pages, pagination.number + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === pagination.number ? 'active' : '';
        html += `<a href="#" class="page-button ${activeClass}" onclick="loadGeneralBoards(${i})">${i}</a>`;
    }
    
    // 다음 페이지
    if (pagination.has_next) {
        html += `<a href="#" class="page-button" onclick="loadGeneralBoards(${pagination.next_page_number})">
            <i class="fas fa-chevron-right"></i>
        </a>`;
    }
    
    paginationContainer.innerHTML = html;
}

// 일반 게시판 검색
function searchGeneralBoards() {
    const searchInput = document.getElementById('general-search');
    const searchTerm = searchInput ? searchInput.value.trim() : '';
    loadGeneralBoards(1, searchTerm);
}

// 일반 게시판 새로고침
function refreshGeneralBoards() {
    const searchInput = document.getElementById('general-search');
    if (searchInput) {
        searchInput.value = '';
    }
    loadGeneralBoards();
}

// 일반 게시판 상세보기
function viewBoardDetail(boardId) {
    window.location.href = `/sales/diary_board/general/${boardId}/detail/`;
}

// 일반 게시판 에러 표시
function showGeneralError(message) {
    const boardList = document.getElementById('general-board-list');
    if (boardList) {
        boardList.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                ${escapeHtml(message)}
            </div>
        `;
    }
}

// 일반 게시판 탭 전환 시 로드
function loadGeneralBoardsOnTabSwitch() {
    const generalContent = document.getElementById('general-content');
    if (generalContent && generalContent.classList.contains('active')) {
        loadGeneralBoards();
    }
}
