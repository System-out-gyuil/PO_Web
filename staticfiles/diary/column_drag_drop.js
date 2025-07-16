// 컬럼 드래그앤드롭 기능
let draggedColumn = null;
let draggedColumnIndex = -1;
let dropIndicator = null;
let dragImageEl = null; // 드래그 이미지 DOM
let isColumnDragInitialized = false; // 중복 초기화 방지

// 컬럼 드래그앤드롭 초기화
function initializeColumnDragDrop(force) {
    if (isColumnDragInitialized && !force) {
        console.log('컬럼 드래그앤드롭: 이미 초기화됨');
        return;
    }
    
    console.log('컬럼 드래그앤드롭 초기화 시작');
    
    const headers = document.querySelectorAll('.attribute-header');
    console.log('찾은 헤더 개수:', headers.length);
    
    if (headers.length === 0) {
        console.log('헤더를 찾을 수 없음, 초기화 건너뜀');
        return;
    }
    
    headers.forEach((header, index) => {
        // 기존 이벤트 리스너 제거
        const newHeader = header.cloneNode(true);
        header.parentNode.replaceChild(newHeader, header);
        
        // 드래그 가능하게 설정
        newHeader.draggable = true;
        newHeader.style.cursor = 'move';
        
        // 드래그 이벤트 바인딩
        bindColumnDragEvents(newHeader, index);
    });
    
    // 드롭 인디케이터 초기화
    if (!dropIndicator) {
        dropIndicator = document.createElement('div');
        dropIndicator.className = 'drop-indicator';
        document.body.appendChild(dropIndicator);
    }
    
    isColumnDragInitialized = true;
    console.log('컬럼 드래그앤드롭 초기화 완료');
}

// 컬럼 드래그 이벤트 바인딩
function bindColumnDragEvents(header, index) {
    header.addEventListener('dragstart', function(e) {
        if (e.target.closest('.sort-btn, .filter-input, .delete-attribute-btn')) {
            e.preventDefault();
            return;
        }
        // 기존 드래그 이미지가 남아있으면 제거
        if (dragImageEl && dragImageEl.parentNode) dragImageEl.parentNode.removeChild(dragImageEl);
        draggedColumn = header;
        draggedColumnIndex = getColumnIndex(header);
        header.classList.add('dragging');
        document.getElementById('entryTable').classList.add('table-dragging');
        dragImageEl = header.cloneNode(true);
        dragImageEl.style.opacity = '0.8';
        dragImageEl.style.position = 'absolute';
        dragImageEl.style.pointerEvents = 'none';
        dragImageEl.style.top = '-9999px';
        document.body.appendChild(dragImageEl);
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', header.outerHTML);
        e.dataTransfer.setDragImage(dragImageEl, e.offsetX, e.offsetY);
    });
    header.addEventListener('dragover', function(e) {
        if (!draggedColumn || draggedColumn === header) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        const rect = header.getBoundingClientRect();
        const midPoint = rect.left + rect.width / 2;
        const isLeftSide = e.clientX < midPoint;
        showDropIndicator(header, isLeftSide);
        clearDragOverStyles();
        if (isLeftSide) header.classList.add('drag-over');
        else header.classList.add('drag-over-right');
    });
    header.addEventListener('dragleave', function(e) {
        const rect = header.getBoundingClientRect();
        if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
            clearDragOverStyles();
            hideDropIndicator();
        }
    });
    header.addEventListener('drop', function(e) {
        if (!draggedColumn || draggedColumn === header) return;
        e.preventDefault();
        const rect = header.getBoundingClientRect();
        const midPoint = rect.left + rect.width / 2;
        const isLeftSide = e.clientX < midPoint;
        const targetIndex = getColumnIndex(header);
        const insertIndex = isLeftSide ? targetIndex : targetIndex + 1;
        reorderColumns(draggedColumnIndex, insertIndex);
        clearDragState();
    });
    header.addEventListener('dragend', function(e) {
        clearDragState();
    });
}

function clearDragState() {
    document.querySelectorAll('.attribute-header').forEach(h => h.classList.remove('dragging', 'drag-over', 'drag-over-right'));
    hideDropIndicator();
    if (dragImageEl && dragImageEl.parentNode) dragImageEl.parentNode.removeChild(dragImageEl);
    dragImageEl = null;
    draggedColumn = null;
    draggedColumnIndex = -1;
    if (document.getElementById('entryTable')) {
        document.getElementById('entryTable').classList.remove('table-dragging');
    }
}

// 컬럼 인덱스 가져오기 (드래그 셀 제외)
function getColumnIndex(header) {
    const headers = Array.from(document.querySelectorAll('.attribute-header'));
    return headers.indexOf(header);
}

// 드롭 인디케이터 표시
function showDropIndicator(targetHeader, isLeftSide) {
    const rect = targetHeader.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    dropIndicator.className = `drop-indicator show ${isLeftSide ? 'left' : 'right'}`;
    dropIndicator.style.top = (rect.top + scrollTop) + 'px';
    dropIndicator.style.left = (isLeftSide ? rect.left - 2 : rect.right - 2) + scrollLeft + 'px';
    dropIndicator.style.height = rect.height + 'px';
    dropIndicator.style.width = '4px';
    dropIndicator.style.background = '#007bff';
    dropIndicator.style.position = 'absolute';
    dropIndicator.style.zIndex = 9999;
    dropIndicator.style.borderRadius = '2px';
}

// 드롭 인디케이터 숨기기
function hideDropIndicator() {
    if (dropIndicator) dropIndicator.classList.remove('show');
}

// 드래그오버 스타일 정리
function clearDragOverStyles() {
    document.querySelectorAll('.attribute-header').forEach(header => {
        header.classList.remove('drag-over', 'drag-over-right');
    });
}

// 컬럼 순서 변경 (기존 코드 유지)
function reorderColumns(fromIndex, toIndex) {
    if (fromIndex === toIndex) return;
    const table = document.getElementById('entryTable');
    const headerRow = table.querySelector('thead tr');
    const bodyRows = table.querySelectorAll('tbody tr');
    const actualFromIndex = fromIndex + 1;
    const actualToIndex = toIndex + 1;
    const headerCells = Array.from(headerRow.children);
    const draggedHeader = headerCells[actualFromIndex];
    if (actualToIndex >= headerCells.length - 1) {
        headerRow.insertBefore(draggedHeader, headerCells[headerCells.length - 1]);
    } else {
        headerRow.insertBefore(draggedHeader, headerCells[actualToIndex]);
    }
    bodyRows.forEach(row => {
        const cells = Array.from(row.children);
        if (cells.length > actualFromIndex) {
            const draggedCell = cells[actualFromIndex];
            if (actualToIndex >= cells.length) {
                row.appendChild(draggedCell);
            } else {
                row.insertBefore(draggedCell, cells[actualToIndex]);
            }
        }
    });
    
    // DOM 업데이트 완료 후 순서 저장
    setTimeout(() => {
        saveColumnOrder();
    }, 50);
    
    // 드래그앤드롭 재초기화는 강제(force)로 1회만
    setTimeout(() => {
        isColumnDragInitialized = false;
        initializeColumnDragDrop(true);
        if (typeof bindTableCellEvents === 'function') {
            bindTableCellEvents();
        }
    }, 100);
}

// 컬럼 순서 서버에 저장
function saveColumnOrder() {
    console.log('=== saveColumnOrder 함수 호출됨 ===');
    
    // DOM에서 실제 순서를 다시 확인
    const headers = document.querySelectorAll('.attribute-header');
    console.log('찾은 헤더 개수:', headers.length);
    
    const columnOrder = Array.from(headers).map((header, index) => {
        const columnName = header.getAttribute('data-column');
        console.log(`[${index}] 헤더:`, header.textContent.trim(), '-> 컬럼명:', columnName);
        return columnName;
    });
    
    console.log('저장할 컬럼 순서:', columnOrder);
    
    // CSRF 토큰 가져오기
    const csrfToken = getCsrfToken();
    console.log('CSRF 토큰:', csrfToken ? '있음' : '없음');
    
    const requestData = {column_order: columnOrder};
    console.log('전송할 데이터:', requestData);
    
    fetch('/sales/save_column_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('서버 응답 상태:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('서버 응답 데이터:', data);
        if (data.success) {
            console.log('컬럼 순서 저장 성공:', data.message);
            // 성공 알림 추가
            if (typeof showNotification === 'function') {
                showNotification('컬럼 순서가 저장되었습니다.', 'success');
            }
        } else {
            console.error('컬럼 순서 저장 실패:', data.error);
            if (typeof showNotification === 'function') {
                showNotification('컬럼 순서 저장 실패: ' + (data.error || '알 수 없는 오류'), 'error');
            }
        }
    })
    .catch(error => {
        console.error('컬럼 순서 저장 중 오류:', error);
        if (typeof showNotification === 'function') {
            showNotification('컬럼 순서 저장 중 오류가 발생했습니다.', 'error');
        }
    });
}

// 페이지 로드 시 드래그앤드롭 초기화
// 최초 1회만
if (!window._columnDragDropLoaded) {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            initializeColumnDragDrop();
        }, 500);
    });
    window._columnDragDropLoaded = true;
}

// 테이블 새로고침 후 드래그앤드롭 재초기화
function reinitializeDragDrop() {
    console.log('드래그앤드롭 재초기화 시작');
    isColumnDragInitialized = false;
    
    // 기존 드래그 이미지 정리
    if (dragImageEl && dragImageEl.parentNode) {
        dragImageEl.parentNode.removeChild(dragImageEl);
        dragImageEl = null;
    }
    
    // 기존 드래그 상태 정리
    clearDragState();
    
    // 약간의 지연 후 초기화 (DOM 렌더링 완료 보장)
    setTimeout(() => {
        try {
            initializeColumnDragDrop(true);
            console.log('드래그앤드롭 재초기화 완료');
        } catch (error) {
            console.error('드래그앤드롭 재초기화 오류:', error);
        }
    }, 200);
}

// 전역 함수로 노출
window.initializeColumnDragDrop = initializeColumnDragDrop;
window.reinitializeDragDrop = reinitializeDragDrop; 