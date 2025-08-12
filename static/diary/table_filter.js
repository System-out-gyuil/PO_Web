
// 정렬/필터 기능
function initializeTableData() {
  const tbody = document.getElementById('entryTbody');
  if (tbody) {
      window.originalRows = Array.from(tbody.querySelectorAll('tr'));
  }
  
  // 저장된 상태 복원
  restoreTableState();
}

// 현재 사용자 ID 가져오기 (동기적 처리)
function getCurrentUserId() {
  // 세션에서 사용자 ID 가져오기
  const userId = sessionStorage.getItem('currentUserId');
  if (userId) {
    return userId;
  }
  
  // 세션에 없으면 기본값 반환 (비동기 처리는 별도 함수에서)
  return 'anonymous';
}

// 사용자 ID를 서버에서 가져와서 세션에 저장
function initializeUserSession() {
  return fetch('/sales/get_current_user_id/', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success && data.user_id) {
      sessionStorage.setItem('currentUserId', data.user_id);
      return data.user_id;
    }
    return 'anonymous';
  })
  .catch(error => {
    console.error('사용자 ID 조회 실패:', error);
    return 'anonymous';
  });
}

// 테이블 상태 저장
function saveTableState() {
  // 사용자별 고유 키 생성
  const userId = getCurrentUserId();
  const stateKey = `tableState_${userId}`;
  
  const state = {
    currentSort: window.currentSort,
    filters: window.filters,
    timestamp: Date.now(),
    userId: userId
  };
  localStorage.setItem(stateKey, JSON.stringify(state));
}

// 테이블 상태 복원 (개선된 버전)
function restoreTableState(retryCount = 0) {
  
  try {
    // 사용자별 고유 키로 상태 조회
    const userId = getCurrentUserId();
    const stateKey = `tableState_${userId}`;
    const savedState = localStorage.getItem(stateKey);
    
    if (savedState) {
      const state = JSON.parse(savedState);
      const oneHour = 60 * 60 * 1000;
      
      // 사용자 ID가 일치하고 1시간 이내의 상태만 복원
      if (state.userId === userId && Date.now() - state.timestamp < oneHour) {
        window.currentSort = state.currentSort || { column: null, direction: null };
        window.filters = state.filters || {};
        
        
        // tbody가 없으면 100ms 후 재시도 (최대 10회)
        const tbody = document.getElementById('entryTbody');
        if (!tbody && retryCount < 10) {
          setTimeout(() => restoreTableState(retryCount + 1), 100);
          return;
        }
        
        if (tbody) {
          // 저장된 필터 상태 복원
          restoreFilters();
          // 저장된 정렬 상태 복원 (필터 복원 후)
          setTimeout(() => {
            restoreSort();
          }, 50);
        } else {
          console.log('최대 재시도 횟수 초과, tbody를 찾을 수 없음');
        }
      } else {
        localStorage.removeItem(stateKey);
      }
    } else {
      console.log('저장된 테이블 상태가 없음');
    }
  } catch (e) {
    console.error('테이블 상태 복원 오류:', e);
  }
}

// 필터 상태 복원
function restoreFilters() {
    if (!window.filters) return;
    
    // 실제 테이블 구조 검증
    const actualColumns = validateTableStructure();
    
    Object.keys(window.filters).forEach(column => {
        const filterValue = window.filters[column];
        if (filterValue) {
            // 필터링하려는 컬럼이 실제로 표시되는지 확인
            const targetColumn = actualColumns.find(col => col.name === column);
            if (!targetColumn) {
                console.log(`restoreFilters: 컬럼 "${column}"이 실제 테이블에 표시되지 않음, 필터 건너뜀`);
                return;
            }
            
            // 필터 입력 필드에 값 설정
            const filterInput = document.querySelector(`input[data-column="${column}"]`);
            if (filterInput) {
                filterInput.value = filterValue;
                // 필터 적용
                filterTable(column, filterValue);
            }
        }
    });
}

// 정렬 상태 복원 (재시도 로직 추가)
function restoreSort(retry = 0) {
    const entryTbody = document.querySelector('#entryTbody');
    if (!entryTbody || entryTbody.rows.length === 0) {
        if (retry < 5) {
            setTimeout(() => restoreSort(retry + 1), 100);
        } else {
            console.log('[restoreSort] 5회 재시도 후 포기');
        }
        return;
    }
    
    if (!window.currentSort || !window.currentSort.column || !window.currentSort.direction) {
        return;
    }
    
    // 실제 테이블 구조 검증
    const actualColumns = validateTableStructure();
    
    // 정렬하려는 컬럼이 실제로 표시되는지 확인
    const targetColumn = actualColumns.find(col => col.name === window.currentSort.column);
    if (!targetColumn) {
        return;
    }
    
    // 정렬 버튼 상태 업데이트
    updateSortButtonStates(window.currentSort.column, window.currentSort.direction);
    // 실제 정렬 적용
    const column = window.currentSort.column;
    const direction = window.currentSort.direction;
    const rows = Array.from(entryTbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
        const aValue = getCellValue(a, column);
        const bValue = getCellValue(b, column);
        let comparison = 0;
        if (column.includes('매출') || column.includes('금액') || column.includes('가격')) {
            const aNum = parseFloat(aValue.replace(/[^\d.-]/g, '')) || 0;
            const bNum = parseFloat(bValue.replace(/[^\d.-]/g, '')) || 0;
            comparison = aNum - bNum;
        } else if (column.includes('날짜') || column.includes('일정')) {
            const aDate = parseDate(aValue);
            const bDate = parseDate(bValue);
            comparison = (aDate || 0) - (bDate || 0);
        } else {
            comparison = aValue.localeCompare(bValue, 'ko');
        }
        return direction === 'asc' ? comparison : -comparison;
    });
    rows.forEach(row => entryTbody.appendChild(row));
}

function sortTable(column, direction) {
    
    // 실제 테이블 구조 검증
    const actualColumns = validateTableStructure();
    
    // 정렬하려는 컬럼이 실제로 표시되는지 확인
    const targetColumn = actualColumns.find(col => col.name === column);
    if (!targetColumn) {
        return;
    }
    
    const tbody = document.getElementById('entryTbody');
    if (!tbody) {
        return;
    }

    // 토글 기능: 같은 컬럼과 방향을 다시 클릭하면 정렬 해제
    if (window.currentSort.column === column && window.currentSort.direction === direction) {
        // 정렬 해제
        window.currentSort = { column: null, direction: null };
        updateSortButtonStates();
        
        // 원래 순서로 복원 (필터링된 행들만)
        restoreOriginalOrder();
    } else {
        // 새로운 정렬 적용
        window.currentSort = { column, direction };
        updateSortButtonStates(column, direction);
        
        const rows = Array.from(tbody.querySelectorAll('tr'));
        if (rows.length === 0) {
            return;
        }

        rows.sort((a, b) => {
            const aValue = getCellValue(a, column);
            const bValue = getCellValue(b, column);
            
            // 빈 값 체크 (공백, null, undefined 등)
            const aIsEmpty = !aValue || aValue.trim() === '';
            const bIsEmpty = !bValue || bValue.trim() === '';
            
            // 빈 값은 항상 아래쪽에 배치
            if (aIsEmpty && !bIsEmpty) return 1;  // a가 빈 값이면 b보다 뒤로
            if (!aIsEmpty && bIsEmpty) return -1; // b가 빈 값이면 a보다 뒤로
            if (aIsEmpty && bIsEmpty) return 0;   // 둘 다 빈 값이면 순서 유지
            
            // 둘 다 값이 있는 경우에만 정렬 수행
            let comparison = 0;
            
            // 숫자 필드인지 확인 (매출 관련 필드)
            if (column.includes('매출') || column.includes('금액') || column.includes('가격')) {
                const aNum = parseFloat(aValue.replace(/[^\d.-]/g, '')) || 0;
                const bNum = parseFloat(bValue.replace(/[^\d.-]/g, '')) || 0;
                comparison = aNum - bNum;
            } else if (column.includes('날짜') || column.includes('일정')) {
                // 날짜 필드
                const aDate = parseDate(aValue);
                const bDate = parseDate(bValue);
                comparison = (aDate || 0) - (bDate || 0);
            } else {
                // 텍스트 필드
                comparison = aValue.localeCompare(bValue, 'ko');
            }
            
            return direction === 'asc' ? comparison : -comparison;
        });
        
        // 정렬된 행들을 테이블에 다시 추가
        rows.forEach(row => tbody.appendChild(row));
    }
    
    // 상태 저장
    saveTableState();
}

// 날짜 파싱 함수 추가
function parseDate(dateString) {
  if (!dateString || dateString.trim() === '') {
      return null;
  }
  
  // YYYY-MM-DD 형식 파싱
  const dateMatch = dateString.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (dateMatch) {
      const year = parseInt(dateMatch[1]);
      const month = parseInt(dateMatch[2]) - 1; // JavaScript Date는 0부터 시작
      const day = parseInt(dateMatch[3]);
      return new Date(year, month, day);
  }
  
  // 다른 날짜 형식들도 시도
  const date = new Date(dateString);
  if (!isNaN(date.getTime())) {
      return date;
  }
  
  return null;
}

// 실제 테이블의 컬럼 구조를 동적으로 파악하는 함수
function getActualTableColumns() {
    const headers = document.querySelectorAll('#entryTable thead th[data-column]');
    const actualColumns = [];
    
    headers.forEach((header, index) => {
        const columnName = header.getAttribute('data-column');
        if (columnName) {
            actualColumns.push({
                name: columnName,
                index: index,
                header: header
            });
        }
    });
    
    return actualColumns;
}

// 테이블 구조 상세 분석 함수
function analyzeTableStructure() {
    
    // 전체 헤더 분석
    const allHeaders = document.querySelectorAll('#entryTable thead th');
    
    allHeaders.forEach((header, index) => {
        const columnName = header.getAttribute('data-column');
        const headerText = header.textContent.trim();
    });
    
    // data-column 속성이 있는 헤더만 분석
    const dataColumnHeaders = document.querySelectorAll('#entryTable thead th[data-column]');
    
    dataColumnHeaders.forEach((header, index) => {
        const columnName = header.getAttribute('data-column');
        const headerText = header.textContent.trim();
    });
    
    // 첫 번째 행 분석
    const tbody = document.getElementById('entryTbody');
    if (tbody) {
        const firstRow = tbody.querySelector('tr');
        if (firstRow) {
            const cells = firstRow.querySelectorAll('td');
            
            cells.forEach((cell, index) => {
                const cellText = cell.textContent.trim();
                const hasInput = cell.querySelector('input') !== null;
                const hasSelect = cell.querySelector('select') !== null;
            });
        }
    }
    
}

// 컬럼명으로 셀을 찾는 함수 추가 (실제 테이블 구조 기반)
function getCellByColumn(row, column) {
    
    const cells = row.querySelectorAll('td');
    
    // 실제 테이블 헤더에서 컬럼 인덱스 찾기
    const header = document.querySelector(`#entryTable thead th[data-column="${column}"]`);
    if (!header) {
        return null;
    }
    
    // 헤더의 실제 위치 찾기 (전체 헤더 중에서)
    const allHeaders = document.querySelectorAll('#entryTable thead th');
    let actualColumnIndex = -1;
    
    for (let i = 0; i < allHeaders.length; i++) {
        if (allHeaders[i] === header) {
            actualColumnIndex = i;
            break;
        }
    }
    
    
    if (actualColumnIndex >= 0 && actualColumnIndex < cells.length) {
        const cell = cells[actualColumnIndex];
        
        // 셀 내용 디버깅
        const cellText = cell.textContent.trim();
        const hasInput = cell.querySelector('input') !== null;
        const hasSelect = cell.querySelector('select') !== null;
        
        return cell;
    }
    return null;
}

function getCellValue(row, column) {
    
    const cells = row.querySelectorAll('td');
    
    // 실제 테이블 헤더에서 컬럼 인덱스 찾기
    const header = document.querySelector(`#entryTable thead th[data-column="${column}"]`);
    if (!header) {
        return '';
    }
    
    // 헤더의 실제 위치 찾기 (전체 헤더 중에서)
    const allHeaders = document.querySelectorAll('#entryTable thead th');
    let actualColumnIndex = -1;
    
    for (let i = 0; i < allHeaders.length; i++) {
        if (allHeaders[i] === header) {
            actualColumnIndex = i;
            break;
        }
    }
    
    
    if (actualColumnIndex >= 0 && actualColumnIndex < cells.length) {
        const cell = cells[actualColumnIndex];
        
        // 셀 내용 상세 분석
        const cellText = cell.textContent.trim();
        const hasInput = cell.querySelector('input') !== null;
        const hasSelect = cell.querySelector('select') !== null;
        
        // 매출 컬럼이면 data-raw 사용
        if (column === '매출' && cell.hasAttribute('data-raw')) {
            const value = cell.getAttribute('data-raw');
            return value;
        }
        
        // 텍스트 입력 필드가 있는 경우
        const input = cell.querySelector('input[type="text"]');
        if (input) {
            const value = input.value || '';
            return value;
        }
        
        // 선택 필드가 있는 경우
        const select = cell.querySelector('select');
        if (select) {
            const value = select.selectedOptions[0]?.text || '';
            return value;
        }
        
        // 일반 텍스트인 경우
        return cellText;
    }
    return '';
}

// 필터링 시 실제 테이블 구조 확인 함수
function validateTableStructure() {
    const actualColumns = getActualTableColumns();
    const expectedColumns = window.ATTR_FIELDS || [];
    
    // 테이블 구조 상세 분석 추가
    analyzeTableStructure();
    
    return actualColumns;
}

function filterTable(column, filterValue) {
    
    // 실제 테이블 구조 검증
    const actualColumns = validateTableStructure();
    
    // 필터링하려는 컬럼이 실제로 표시되는지 확인
    const targetColumn = actualColumns.find(col => col.name === column);
    if (!targetColumn) {
        return;
    }
    
    
    // 필터 상태 업데이트
    if (filterValue.trim() === '') {
        delete window.filters[column];
    } else {
        window.filters[column] = filterValue;
    }
    
    const tbody = document.getElementById('entryTbody');
    if (!tbody) {
        return;
    }

    const rows = Array.from(tbody.querySelectorAll('tr'));
    let visibleCount = 0;

    rows.forEach((row, index) => {
        const cell = getCellByColumn(row, column);
        if (!cell) {
            row.style.display = 'none';
            return;
        }

        const cellValue = getCellValue(row, column).toLowerCase();
        const filterLower = filterValue.toLowerCase();
        
        // 필터 조건 확인
        let shouldShow = false;
        
        if (filterValue.trim() === '') {
            // 필터가 비어있으면 모든 행 표시
            shouldShow = true;
        } else {
            // 다양한 필터 조건 지원
            if (filterLower.startsWith('>=')) {
                // 숫자 비교 (이상)
                const numValue = parseFloat(cellValue.replace(/[^\d.-]/g, '')) || 0;
                const filterNum = parseFloat(filterLower.substring(2)) || 0;
                shouldShow = numValue >= filterNum;
            } else if (filterLower.startsWith('<=')) {
                // 숫자 비교 (이하)
                const numValue = parseFloat(cellValue.replace(/[^\d.-]/g, '')) || 0;
                const filterNum = parseFloat(filterLower.substring(2)) || 0;
                shouldShow = numValue <= filterNum;
            } else if (filterLower.startsWith('>')) {
                // 숫자 비교 (초과)
                const numValue = parseFloat(cellValue.replace(/[^\d.-]/g, '')) || 0;
                const filterNum = parseFloat(filterLower.substring(1)) || 0;
                shouldShow = numValue > filterNum;
            } else if (filterLower.startsWith('<')) {
                // 숫자 비교 (미만)
                const numValue = parseFloat(cellValue.replace(/[^\d.-]/g, '')) || 0;
                const filterNum = parseFloat(filterLower.substring(1)) || 0;
                shouldShow = numValue < filterNum;
            } else {
                // 일반 텍스트 검색
                shouldShow = cellValue.includes(filterLower);
            }
        }
        
        row.style.display = shouldShow ? '' : 'none';
        if (shouldShow) visibleCount++;
    });

    
    // 필터 상태 업데이트
    updateFilterStatus();
    
    // 상태 저장
    saveTableState();
}

function clearAllFilters() {
    
    // 모든 필터 입력 필드 초기화
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.value = '';
    });
    
    // 모든 행 표시
    const tbody = document.getElementById('entryTbody');
    if (tbody) {
        const rows = tbody.querySelectorAll('tr');
        rows.forEach(row => {
            row.style.display = '';
        });
    }
    
    // 정렬 상태도 초기화
    window.currentSort = { column: null, direction: null };
    updateSortButtonStates();
    
    // 필터 상태 초기화
    window.filters = {};
    
    // 필터 상태 업데이트
    updateFilterStatus();
    
    // 상태 저장
    saveTableState();
}

function updateSortButtonStates(activeColumn = null, activeDirection = null) {
    
    // 모든 정렬 버튼 초기화
    const sortButtons = document.querySelectorAll('.sort-btn');
    sortButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 활성 정렬 버튼 강조 - 더 정확한 선택자 사용
    if (activeColumn && activeDirection) {
        // onclick 속성에서 정확한 컬럼명과 방향을 찾는 정규식 사용
        const activeButtons = document.querySelectorAll('.sort-btn').forEach(btn => {
            const onclickAttr = btn.getAttribute('onclick') || '';
            // 정확한 컬럼명과 방향이 모두 포함된 버튼만 선택
            const columnMatch = onclickAttr.includes(`'${activeColumn}'`) || onclickAttr.includes(`"${activeColumn}"`);
            const directionMatch = onclickAttr.includes(`'${activeDirection}'`) || onclickAttr.includes(`"${activeDirection}"`);
            
            if (columnMatch && directionMatch) {
                btn.classList.add('active');
            }
        });
    }
    
    // 정렬 상태가 변경되었을 때 실제 정렬 적용
    if (activeColumn && activeDirection && window.currentSort) {
        // 현재 정렬 상태와 다른 경우에만 정렬 적용
        if (window.currentSort.column !== activeColumn || window.currentSort.direction !== activeDirection) {
            window.currentSort = { column: activeColumn, direction: activeDirection };
            // 실제 정렬 적용
            const tbody = document.getElementById('entryTbody');
            if (tbody) {
                const rows = Array.from(tbody.querySelectorAll('tr'));
                if (rows.length > 0) {
                    rows.sort((a, b) => {
                        const aValue = getCellValue(a, activeColumn);
                        const bValue = getCellValue(b, activeColumn);
                        
                        // 빈 값 체크 (공백, null, undefined 등)
                        const aIsEmpty = !aValue || aValue.trim() === '';
                        const bIsEmpty = !bValue || bValue.trim() === '';
                        
                        // 빈 값은 항상 아래쪽에 배치
                        if (aIsEmpty && !bIsEmpty) return 1;  // a가 빈 값이면 b보다 뒤로
                        if (!aIsEmpty && bIsEmpty) return -1; // b가 빈 값이면 a보다 뒤로
                        if (aIsEmpty && bIsEmpty) return 0;   // 둘 다 빈 값이면 순서 유지
                        
                        // 둘 다 값이 있는 경우에만 정렬 수행
                        let comparison = 0;
                        
                        // 숫자 필드인지 확인 (매출 관련 필드)
                        if (activeColumn.includes('매출') || activeColumn.includes('금액') || activeColumn.includes('가격')) {
                            const aNum = parseFloat(aValue.replace(/[^\d.-]/g, '')) || 0;
                            const bNum = parseFloat(bValue.replace(/[^\d.-]/g, '')) || 0;
                            comparison = aNum - bNum;
                        } else if (activeColumn.includes('날짜') || activeColumn.includes('일정')) {
                            // 날짜 필드
                            const aDate = parseDate(aValue);
                            const bDate = parseDate(bValue);
                            comparison = (aDate || 0) - (bDate || 0);
                        } else {
                            // 텍스트 필드
                            comparison = aValue.localeCompare(bValue, 'ko');
                        }
                        
                        return activeDirection === 'asc' ? comparison : -comparison;
                    });
                    
                    // 정렬된 행들을 테이블에 다시 추가
                    rows.forEach(row => tbody.appendChild(row));
                }
            }
        } else {
            console.log('정렬 상태가 동일함, 실제 정렬 생략');
        }
    }
}

function updateFilterStatus(someObj) {
    const filterStatus = document.getElementById('filterStatus');
    if (!filterStatus) return;
    
    let statusText = '전체 데이터 표시 중';
    let hasFilters = false;
    
    // 활성 필터 확인
    if (window.filters) {
        const activeFilters = Object.keys(window.filters).filter(key => 
            window.filters[key] && window.filters[key].trim() !== ''
        );
        
        if (activeFilters.length > 0) {
            hasFilters = true;
            const filterDescriptions = activeFilters.map(key => 
                `${key}: ${window.filters[key]}`
            );
            statusText = `필터 적용 중: ${filterDescriptions.join(', ')}`;
        }
    }
    
    // 정렬 상태 확인
    if (window.currentSort && window.currentSort.column) {
        const sortText = `${window.currentSort.column} ${window.currentSort.direction === 'asc' ? '오름차순' : '내림차순'}`;
        if (hasFilters) {
            statusText += ` | 정렬: ${sortText}`;
        } else {
            statusText = `정렬: ${sortText}`;
        }
    }
    
    filterStatus.textContent = statusText;
}

// 원래 순서로 복원 (필터링된 행들만)
function restoreOriginalOrder() {
    const tbody = document.getElementById('entryTbody');
    if (!tbody || !window.originalRows) return;
    
    // 현재 표시된 행들만 원래 순서로 정렬
    const visibleRows = Array.from(tbody.querySelectorAll('tr')).filter(row => 
        row.style.display !== 'none'
    );
    
    // 원래 순서에 따라 정렬
    visibleRows.sort((a, b) => {
        const aIndex = window.originalRows.findIndex(row => row.getAttribute('data-id') === a.getAttribute('data-id'));
        const bIndex = window.originalRows.findIndex(row => row.getAttribute('data-id') === b.getAttribute('data-id'));
        return aIndex - bIndex;
    });
    
    // 정렬된 행들을 테이블에 다시 추가
    visibleRows.forEach(row => tbody.appendChild(row));
}

// 디버깅을 위한 상태 확인 함수
function debugTableState() {
  
  const tbody = document.getElementById('entryTbody');
  if (tbody) {
    const rows = tbody.querySelectorAll('tr');
    
    // 정렬 버튼 상태 확인
    const sortButtons = document.querySelectorAll('.sort-btn');
    const activeButtons = document.querySelectorAll('.sort-btn.active');
    
    if (window.currentSort && window.currentSort.column) {
      const expectedButtons = document.querySelectorAll(`.sort-btn[onclick*="${window.currentSort.column}"][onclick*="${window.currentSort.direction}"]`);
    }
  } else {
    console.log('tbody를 찾을 수 없음');
  }
}



// 테이블 새로고침 후 상태 복원을 위한 함수
function restoreTableStateAfterRefresh() {
  
  // 약간의 지연 후 상태 복원 (DOM이 완전히 로드된 후)
  setTimeout(() => {
    try {
      // 사용자별 고유 키로 상태 조회
      const userId = getCurrentUserId();
      const stateKey = `tableState_${userId}`;
      const savedState = localStorage.getItem(stateKey);
      
      if (savedState) {
        const state = JSON.parse(savedState);
        
        // 1시간 이내의 상태만 복원 (오래된 상태는 무시)
        const oneHour = 60 * 60 * 1000;
        if (Date.now() - state.timestamp < oneHour) {
          window.currentSort = state.currentSort || { column: null, direction: null };
          window.filters = state.filters || {};
          
          
          // 저장된 필터 상태 복원
          restoreFilters();
          
          // 저장된 정렬 상태 복원 (필터 복원 후)
          setTimeout(() => {
            if (window.currentSort && window.currentSort.column && window.currentSort.direction) {
              // 정렬 버튼 상태 업데이트
              updateSortButtonStates(window.currentSort.column, window.currentSort.direction);
              
              // 실제 정렬 적용
              const tbody = document.getElementById('entryTbody');
              if (tbody) {
                const rows = Array.from(tbody.querySelectorAll('tr'));
                if (rows.length > 0) {
                  
                  // 행들을 정렬
                  rows.sort((a, b) => {
                    const aValue = getCellValue(a, window.currentSort.column);
                    const bValue = getCellValue(b, window.currentSort.column);
                    let comparison = 0;
                    
                    if (window.currentSort.column.includes('매출') || window.currentSort.column.includes('금액') || window.currentSort.column.includes('가격')) {
                      const aNum = parseFloat(aValue.replace(/[^\d.-]/g, '')) || 0;
                      const bNum = parseFloat(bValue.replace(/[^\d.-]/g, '')) || 0;
                      comparison = aNum - bNum;
                    } else if (window.currentSort.column.includes('날짜') || window.currentSort.column.includes('일정')) {
                      const aDate = parseDate(aValue);
                      const bDate = parseDate(bValue);
                      comparison = (aDate || 0) - (bDate || 0);
                    } else {
                      comparison = aValue.localeCompare(bValue, 'ko');
                    }
                    
                    return window.currentSort.direction === 'asc' ? comparison : -comparison;
                  });
                  
                  // 정렬된 행들을 테이블에 다시 추가
                  rows.forEach(row => tbody.appendChild(row));
                }
              }
            }
            
            // 디버깅 정보 출력
            setTimeout(() => {
              debugTableState();
            }, 500);
          }, 500);
          
        } else {
          localStorage.removeItem(stateKey);
        }
      } else {
        console.log('저장된 테이블 상태가 없음');
      }
    } catch (error) {
      localStorage.removeItem('tableState'); // 이 부분은 사용자별 키로 변경되었으므로 제거
    }
  }, 500);
}

// 페이지 로드 시 상태 복원
document.addEventListener('DOMContentLoaded', function() {
  // 초기 테이블 데이터 로드
  initializeTableData();
  
  // 상태 복원
  restoreTableStateAfterRefresh();
});

// 테이블 리랜더링 후 상태 복원을 위한 전역 함수
window.restoreTableStateAfterRefresh = restoreTableStateAfterRefresh;
window.debugTableState = debugTableState;

// 리랜더링 후 정렬/필터 상태 복원 함수
function reinitializeTableFilters() {
  
  // 테이블 데이터 초기화
  initializeTableData();
  
  // 저장된 상태 복원
  restoreTableState();
  
  // 정렬 버튼 상태 업데이트
  if (window.currentSort && window.currentSort.column && window.currentSort.direction) {
    updateSortButtonStates(window.currentSort.column, window.currentSort.direction);
  }
  
  // 필터 상태 업데이트
  updateFilterStatus();
  
}

// 전역 함수로 노출
window.reinitializeTableFilters = reinitializeTableFilters;