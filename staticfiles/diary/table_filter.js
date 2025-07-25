
// 정렬/필터 기능
function initializeTableData() {
  const tbody = document.getElementById('entryTbody');
  if (tbody) {
      window.originalRows = Array.from(tbody.querySelectorAll('tr'));
  }
  
  // 저장된 상태 복원
  restoreTableState();
}

// 테이블 상태 저장
function saveTableState() {
  const state = {
    currentSort: window.currentSort,
    filters: window.filters,
    timestamp: Date.now()
  };
  localStorage.setItem('tableState', JSON.stringify(state));
}

// 테이블 상태 복원
function restoreTableState(retryCount = 0) {
  console.log('restoreTableState 호출됨, retryCount:', retryCount);
  
  try {
    const savedState = localStorage.getItem('tableState');
    if (savedState) {
      const state = JSON.parse(savedState);
      const oneHour = 60 * 60 * 1000;
      if (Date.now() - state.timestamp < oneHour) {
        window.currentSort = state.currentSort || { column: null, direction: null };
        window.filters = state.filters || {};
        
        console.log('저장된 상태 로드됨:', state);
        
        // tbody가 없으면 100ms 후 재시도 (최대 10회)
        const tbody = document.getElementById('entryTbody');
        if (!tbody && retryCount < 10) {
          console.log('tbody를 찾을 수 없음, 재시도:', retryCount);
          setTimeout(() => restoreTableState(retryCount + 1), 100);
          return;
        }
        
        if (tbody) {
          console.log('tbody 찾음, 필터 및 정렬 복원 시작');
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
        console.log('저장된 상태가 너무 오래되어 무시됨');
        localStorage.removeItem('tableState');
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
  
  Object.keys(window.filters).forEach(column => {
    const filterValue = window.filters[column];
    if (filterValue) {
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
      console.log(`[restoreSort] tbody나 행이 없음, 재시도... (${retry})`);
      setTimeout(() => restoreSort(retry + 1), 100);
    } else {
      console.log('[restoreSort] 5회 재시도 후 포기');
    }
    return;
  }
  console.log(`[restoreSort] ${entryTbody.rows.length}개 행에 정렬 적용, 현재 정렬:`, window.currentSort);
  if (!window.currentSort || !window.currentSort.column || !window.currentSort.direction) {
    console.log('정렬 상태가 없어서 복원하지 않음');
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
  console.log('[restoreSort] 정렬 적용 완료');
}

function sortTable(column, direction) {
    console.log("sortTable 호출됨:", column, direction);
  const tbody = document.getElementById('entryTbody');
  if (!tbody) {
    console.log('tbody를 찾을 수 없음');
    return;
  }

  // 토글 기능: 같은 컬럼과 방향을 다시 클릭하면 정렬 해제
  if (window.currentSort.column === column && window.currentSort.direction === direction) {
      console.log('정렬 해제');
      // 정렬 해제
      window.currentSort = { column: null, direction: null };
      updateSortButtonStates();
      
      // 원래 순서로 복원 (필터링된 행들만)
      restoreOriginalOrder();
  } else {
      console.log('새로운 정렬 적용:', column, direction);
      // 새로운 정렬 적용
      window.currentSort = { column, direction };
      updateSortButtonStates(column, direction);
      
      const rows = Array.from(tbody.querySelectorAll('tr'));
      if (rows.length === 0) {
        console.log('정렬할 행이 없음');
        return;
      }

      rows.sort((a, b) => {
          const aValue = getCellValue(a, column);
          const bValue = getCellValue(b, column);
          
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
      console.log('정렬 완료');
  }
  
  // 상태 저장
  saveTableState();
  console.log('정렬 상태 저장됨');
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

// 컬럼명으로 셀을 찾는 함수 추가
function getCellByColumn(row, column) {
  const cells = row.querySelectorAll('td');
  const attributes = window.ATTR_FIELDS || [];
  // 속성 인덱스 찾기 (드래그 셀 제외하고 시작)
  const columnIndex = attributes.findIndex(attr => attr.name === column) + 1;
  if (columnIndex > 0 && columnIndex < cells.length) {
      return cells[columnIndex];
  }
  return null;
}

function getCellValue(row, column) {
    
  const cells = row.querySelectorAll('td');
  const attributes = window.ATTR_FIELDS || [];
  // 속성 인덱스 찾기 (드래그 셀 제외하고 시작)
    const columnIndex = attributes.findIndex(attr => attr.name === column) + 1;
    console.log("column", column);
    console.log("attributes", attributes);
  console.log("columnIndex", columnIndex);
  console.log("cells.length", cells.length);
  console.log("cells", cells);
    if (columnIndex > 0 && columnIndex < cells.length) {
      console.log("들어옴")
      const cell = cells[columnIndex];
      // 매출 컬럼이면 data-raw 사용
      if (column === '매출' && cell.hasAttribute('data-raw')) {
          return cell.getAttribute('data-raw');
      }
      // 텍스트 입력 필드가 있는 경우
      const input = cell.querySelector('input[type="text"]');
      if (input) {
          return input.value || '';
      }
      // 선택 필드가 있는 경우
      const select = cell.querySelector('select');
      if (select) {
          return select.selectedOptions[0]?.text || '';
      }
      // 일반 텍스트인 경우
      return cell.textContent.trim();
  }
  return '';
}

function filterTable(column, filterValue) {
    console.log(`filterTable 호출됨: ${column} = ${filterValue}`);
    
    // 필터 상태 업데이트
    if (filterValue.trim() === '') {
        delete window.filters[column];
    } else {
        window.filters[column] = filterValue;
    }
    
    const tbody = document.getElementById('entryTbody');
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));
    let visibleCount = 0;

    rows.forEach(row => {
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
    console.log("clearAllFilters 호출됨");
    
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
    console.log('updateSortButtonStates 호출됨:', activeColumn, activeDirection);
    
    // 모든 정렬 버튼 초기화
    const sortButtons = document.querySelectorAll('.sort-btn');
    sortButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 활성 정렬 버튼 강조
    if (activeColumn && activeDirection) {
        const activeButtons = document.querySelectorAll(`.sort-btn[onclick*="${activeColumn}"][onclick*="${activeDirection}"]`);
        activeButtons.forEach(btn => {
            btn.classList.add('active');
        });
        console.log('정렬 버튼 활성화:', activeColumn, activeDirection);
    }
    
    // 정렬 상태가 변경되었을 때 실제 정렬 적용
    if (activeColumn && activeDirection && window.currentSort) {
        // 현재 정렬 상태와 다른 경우에만 정렬 적용
        if (window.currentSort.column !== activeColumn || window.currentSort.direction !== activeDirection) {
            console.log('정렬 상태 변경됨, 실제 정렬 적용');
            window.currentSort = { column: activeColumn, direction: activeDirection };
            // 실제 정렬 적용
            const tbody = document.getElementById('entryTbody');
            if (tbody) {
                const rows = Array.from(tbody.querySelectorAll('tr'));
                if (rows.length > 0) {
                    rows.sort((a, b) => {
                        const aValue = getCellValue(a, activeColumn);
                        const bValue = getCellValue(b, activeColumn);
                        
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
                    console.log('정렬 적용 완료');
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
  console.log('=== 테이블 상태 디버깅 ===');
  console.log('window.currentSort:', window.currentSort);
  console.log('window.filters:', window.filters);
  
  const tbody = document.getElementById('entryTbody');
  if (tbody) {
    const rows = tbody.querySelectorAll('tr');
    console.log('tbody 행 수:', rows.length);
    
    // 정렬 버튼 상태 확인
    const sortButtons = document.querySelectorAll('.sort-btn');
    const activeButtons = document.querySelectorAll('.sort-btn.active');
    console.log('전체 정렬 버튼 수:', sortButtons.length);
    console.log('활성 정렬 버튼 수:', activeButtons.length);
    
    if (window.currentSort && window.currentSort.column) {
      const expectedButtons = document.querySelectorAll(`.sort-btn[onclick*="${window.currentSort.column}"][onclick*="${window.currentSort.direction}"]`);
      console.log('예상 활성 버튼 수:', expectedButtons.length);
    }
  } else {
    console.log('tbody를 찾을 수 없음');
  }
  console.log('=== 디버깅 완료 ===');
}

// 수동 테스트 함수 (브라우저 콘솔에서 호출 가능)
function testSortingFunctionality() {
  console.log('=== 정렬 기능 테스트 시작 ===');
  
  // 1. 현재 상태 확인
  console.log('1. 현재 정렬 상태:', window.currentSort);
  console.log('1. 현재 필터 상태:', window.filters);
  
  // 2. 테이블 구조 확인
  const tbody = document.getElementById('entryTbody');
  if (!tbody) {
    console.error('tbody를 찾을 수 없음');
    return;
  }
  
  const rows = tbody.querySelectorAll('tr');
  console.log('2. 테이블 행 수:', rows.length);
  
  // 3. 정렬 버튼 확인
  const sortButtons = document.querySelectorAll('.sort-btn');
  console.log('3. 정렬 버튼 수:', sortButtons.length);
  
  // 4. 첫 번째 컬럼으로 정렬 테스트
  if (sortButtons.length > 0) {
    const firstButton = sortButtons[0];
    const onclick = firstButton.getAttribute('onclick');
    console.log('4. 첫 번째 정렬 버튼 onclick:', onclick);
    
    // 정렬 실행
    if (onclick && onclick.includes('sortTable')) {
      console.log('5. 정렬 테스트 실행...');
      eval(onclick);
      
      // 결과 확인
      setTimeout(() => {
        console.log('6. 정렬 후 상태:', window.currentSort);
        debugTableState();
      }, 100);
    }
  }
  
  console.log('=== 정렬 기능 테스트 완료 ===');
}

// 테이블 새로고침 후 상태 복원을 위한 함수
function restoreTableStateAfterRefresh() {
  console.log('테이블 상태 복원 시작 (새로고침 후)');
  
  // 약간의 지연 후 상태 복원 (DOM이 완전히 로드된 후)
  setTimeout(() => {
    try {
      const savedState = localStorage.getItem('tableState');
      if (savedState) {
        const state = JSON.parse(savedState);
        
        // 1시간 이내의 상태만 복원 (오래된 상태는 무시)
        const oneHour = 60 * 60 * 1000;
        if (Date.now() - state.timestamp < oneHour) {
          window.currentSort = state.currentSort || { column: null, direction: null };
          window.filters = state.filters || {};
          
          console.log('저장된 상태 복원:', state);
          
          // 저장된 필터 상태 복원
          restoreFilters();
          
          // 저장된 정렬 상태 복원 (필터 복원 후)
          setTimeout(() => {
            console.log('정렬 상태 복원 시작:', window.currentSort);
            if (window.currentSort && window.currentSort.column && window.currentSort.direction) {
              // 정렬 버튼 상태 업데이트
              updateSortButtonStates(window.currentSort.column, window.currentSort.direction);
              
              // 실제 정렬 적용
              const tbody = document.getElementById('entryTbody');
              if (tbody) {
                const rows = Array.from(tbody.querySelectorAll('tr'));
                if (rows.length > 0) {
                  console.log('정렬 적용 시작:', window.currentSort.column, window.currentSort.direction, '행 수:', rows.length);
                  
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
                  console.log('정렬 적용 완료');
                }
              }
            }
            
            // 디버깅 정보 출력
            setTimeout(() => {
              debugTableState();
            }, 100);
          }, 200);
          
          console.log('테이블 상태 복원 완료:', state);
        } else {
          console.log('저장된 상태가 너무 오래되어 무시됨');
          localStorage.removeItem('tableState');
        }
      } else {
        console.log('저장된 테이블 상태가 없음');
      }
    } catch (error) {
      console.error('테이블 상태 복원 중 오류:', error);
      localStorage.removeItem('tableState');
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
window.testSortingFunctionality = testSortingFunctionality;