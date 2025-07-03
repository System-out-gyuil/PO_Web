// 컬럼 드래그앤드롭 기능
let draggedColumn = null;
let draggedColumnIndex = -1;
let dropIndicator = null;

// 컬럼 드래그앤드롭 초기화
function initializeColumnDragDrop() {
    console.log('컬럼 드래그앤드롭 초기화 시작');
    
    // 드롭 인디케이터 생성
    if (!dropIndicator) {
        dropIndicator = document.createElement('div');
        dropIndicator.className = 'drop-indicator';
        document.body.appendChild(dropIndicator);
    }
    
    // 모든 헤더에 드래그 기능 추가 (핸들 없이 직접 드래그)
    const headers = document.querySelectorAll('.attribute-header');
    headers.forEach((header, index) => {
        // 헤더를 드래그 가능하게 설정
        header.draggable = true;
        header.style.cursor = 'move';
        
        // 드래그 이벤트 바인딩
        bindColumnDragEvents(header, index);
    });
    
    console.log('컬럼 드래그앤드롭 초기화 완료');
}

// 컬럼 드래그 이벤트 바인딩
function bindColumnDragEvents(header, index) {
    header.addEventListener('dragstart', function(e) {
        // 정렬 버튼이나 필터 입력창을 클릭한 경우 드래그 방지
        if (e.target.classList.contains('sort-btn') || 
            e.target.classList.contains('filter-input') ||
            e.target.classList.contains('delete-attribute-btn')) {
            e.preventDefault();
            return;
        }
        
        console.log('드래그 시작:', header.getAttribute('data-column'));
        
        draggedColumn = header;
        draggedColumnIndex = getColumnIndex(header);
        
        header.classList.add('dragging');
        document.getElementById('entryTable').classList.add('table-dragging');
        
        // 드래그 데이터 설정
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', header.outerHTML);
        
        // 드래그 이미지 설정 (선택사항)
        const dragImage = header.cloneNode(true);
        dragImage.style.opacity = '0.8';
        dragImage.style.transform = 'rotate(2deg)';
        document.body.appendChild(dragImage);
        e.dataTransfer.setDragImage(dragImage, e.offsetX, e.offsetY);
        setTimeout(() => document.body.removeChild(dragImage), 0);
    });
    
    header.addEventListener('dragover', function(e) {
        if (!draggedColumn || draggedColumn === header) return;
        
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        const rect = header.getBoundingClientRect();
        const midPoint = rect.left + rect.width / 2;
        const isLeftSide = e.clientX < midPoint;
        
        // 드롭 위치 표시
        showDropIndicator(header, isLeftSide);
        
        // 헤더 하이라이트
        clearDragOverStyles();
        if (isLeftSide) {
            header.classList.add('drag-over');
        } else {
            header.classList.add('drag-over-right');
        }
    });
    
    header.addEventListener('dragleave', function(e) {
        // 헤더 영역을 완전히 벗어난 경우만 스타일 제거
        const rect = header.getBoundingClientRect();
        if (e.clientX < rect.left || e.clientX > rect.right || 
            e.clientY < rect.top || e.clientY > rect.bottom) {
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
        
        console.log('드롭 실행:', {
            draggedIndex: draggedColumnIndex,
            targetIndex: targetIndex,
            insertIndex: insertIndex,
            isLeftSide: isLeftSide
        });
        
        // 컬럼 순서 변경
        reorderColumns(draggedColumnIndex, insertIndex);
    });
    
    header.addEventListener('dragend', function(e) {
        console.log('드래그 종료');
        
        // 스타일 정리
        header.classList.remove('dragging');
        document.getElementById('entryTable').classList.remove('table-dragging');
        clearDragOverStyles();
        hideDropIndicator();
        
        // 변수 초기화
        draggedColumn = null;
        draggedColumnIndex = -1;
    });
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
    dropIndicator.style.left = (isLeftSide ? rect.left : rect.right - 3) + scrollLeft + 'px';
    dropIndicator.style.height = rect.height + 'px';
}

// 드롭 인디케이터 숨기기
function hideDropIndicator() {
    dropIndicator.classList.remove('show');
}

// 드래그오버 스타일 정리
function clearDragOverStyles() {
    document.querySelectorAll('.attribute-header').forEach(header => {
        header.classList.remove('drag-over', 'drag-over-right');
    });
}

// 컬럼 순서 변경
function reorderColumns(fromIndex, toIndex) {
    console.log('컬럼 순서 변경:', {fromIndex, toIndex});
    
    if (fromIndex === toIndex) return;
    
    const table = document.getElementById('entryTable');
    const headerRow = table.querySelector('thead tr');
    const bodyRows = table.querySelectorAll('tbody tr');
    
    // 실제 컬럼 인덱스 계산 (드래그 셀 포함)
    const actualFromIndex = fromIndex + 1; // 드래그 셀 때문에 +1
    const actualToIndex = toIndex + 1;
    
    // 헤더 이동
    const headerCells = Array.from(headerRow.children);
    const draggedHeader = headerCells[actualFromIndex];
    
    if (actualToIndex >= headerCells.length - 1) {
        // 마지막 위치 (속성 추가 버튼 앞)
        headerRow.insertBefore(draggedHeader, headerCells[headerCells.length - 1]);
    } else {
        headerRow.insertBefore(draggedHeader, headerCells[actualToIndex]);
    }
    
    // 모든 바디 행의 셀도 이동
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
    
    // 드래그앤드롭 이벤트 재바인딩
    setTimeout(() => {
        initializeColumnDragDrop();
        if (typeof bindTableCellEvents === 'function') {
            bindTableCellEvents(); // 셀 이벤트도 재바인딩
        }
    }, 100);
    
    console.log('컬럼 순서 변경 완료');
    
    // 서버에 순서 변경 저장
    saveColumnOrder();
}

// 컬럼 순서 서버에 저장
function saveColumnOrder() {
    const headers = document.querySelectorAll('.attribute-header');
    const columnOrder = Array.from(headers).map(header => header.getAttribute('data-column'));
    
    console.log('저장할 컬럼 순서:', columnOrder);
    
    // 서버에 컬럼 순서 저장
    fetch('/diary/save_column_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({column_order: columnOrder})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('컬럼 순서 저장 성공:', data.message);
        } else {
            console.error('컬럼 순서 저장 실패:', data.error);
        }
    })
    .catch(error => {
        console.error('컬럼 순서 저장 중 오류:', error);
    });
}

// 페이지 로드 시 드래그앤드롭 초기화
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        initializeColumnDragDrop();
    }, 500); // 테이블이 완전히 로드된 후 실행
});

// 테이블 새로고침 후 드래그앤드롭 재초기화
function reinitializeDragDrop() {
    setTimeout(() => {
        initializeColumnDragDrop();
    }, 100);
}

// 전역 함수로 노출
window.initializeColumnDragDrop = initializeColumnDragDrop;
window.reinitializeDragDrop = reinitializeDragDrop; 