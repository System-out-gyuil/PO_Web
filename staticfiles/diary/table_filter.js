
// 정렬/필터 기능
function initializeTableData() {
  const tbody = document.getElementById('entryTbody');
  if (tbody) {
      window.originalRows = Array.from(tbody.querySelectorAll('tr'));
  }
}

function sortTable(column, direction) {
    console.log("sortTable 호출됨");
  const tbody = document.getElementById('entryTbody');
  if (!tbody) return;

  // 토글 기능: 같은 컬럼과 방향을 다시 클릭하면 정렬 해제
  if (window.currentSort.column === column && window.currentSort.direction === direction) {
      // 정렬 해제
      window.currentSort = { column: null, direction: null };
      updateSortButtonStates();
      
      // 원래 순서로 복원 (필터링된 행들만)
      const visibleRows = window.originalRows.filter(row => row.style.display !== 'none');
      visibleRows.forEach(row => tbody.appendChild(row));
      
      updateFilterStatus();
      return;
  }

  // 현재 정렬 상태 업데이트
  window.currentSort = { column, direction };
  
  // 정렬 버튼 활성화 상태 업데이트
  updateSortButtonStates(column, direction);

  // 현재 표시된 행들을 가져오기
  const rows = Array.from(tbody.querySelectorAll('tr:not([style*="display: none"])'));
  
  // 정렬 실행
  rows.sort((a, b) => {
      const aValue = getCellValue(a, column);
      const bValue = getCellValue(b, column);
      
      let comparison = 0;
      
      // 빈 값 체크 (공백, null, undefined, 빈 문자열, 한 칸 공백 등)
      const aIsEmpty = !aValue || aValue.trim() === '' || aValue === ' ';
      const bIsEmpty = !bValue || bValue.trim() === '' || bValue === ' ';
      
      // 둘 다 빈 값이거나 둘 다 값이 있는 경우
      if (aIsEmpty && bIsEmpty) {
          comparison = 0; // 빈 값끼리는 순서 유지
      } else if (aIsEmpty && !bIsEmpty) {
          comparison = 1; // a가 빈 값이면 뒤로
      } else if (!aIsEmpty && bIsEmpty) {
          comparison = -1; // b가 빈 값이면 뒤로
      } else {
          // 둘 다 값이 있는 경우 기존 로직 사용
          // datetime 타입인지 확인
          const aCell = getCellByColumn(a, column);
          const bCell = getCellByColumn(b, column);
          const isDateTime = aCell && aCell.getAttribute('data-type') === 'datetime';
          
          // 매출 컬럼인 경우 특별 처리
          if (column === '매출') {
              // 숫자만 추출 (쉼표, 원, 공백 등 제거)
              const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
              const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
              
              if (!isNaN(aNum) && !isNaN(bNum)) {
                  // 숫자 크기로 비교
                  comparison = aNum - bNum;
              } else {
                  // 숫자가 아닌 경우 문자열 비교
                  comparison = aValue.localeCompare(bValue, 'ko');
              }
          } else if (isDateTime) {
              // datetime 타입인 경우 날짜 비교
              const aDate = parseDate(aValue);
              const bDate = parseDate(bValue);
              
              if (aDate && bDate) {
                  // 날짜 객체로 비교
                  comparison = aDate.getTime() - bDate.getTime();
              } else if (aDate && !bDate) {
                  // a만 유효한 날짜인 경우 a를 앞으로
                  comparison = -1;
              } else if (!aDate && bDate) {
                  // b만 유효한 날짜인 경우 b를 앞으로
                  comparison = 1;
              } else {
                  // 둘 다 유효하지 않은 경우 문자열 비교
                  comparison = aValue.localeCompare(bValue, 'ko');
              }
          } else {
              // 전화번호 형식인지 확인 (하이픈이 포함된 경우)
              const aPhoneMatch = aValue.match(/^(\d{2,3})-(\d{3,4})-(\d{4})$/);
              const bPhoneMatch = bValue.match(/^(\d{2,3})-(\d{3,4})-(\d{4})$/);
              
              if (aPhoneMatch && bPhoneMatch) {
                  // 둘 다 전화번호 형식인 경우 숫자로 비교
                  const aPhoneNum = aValue.replace(/[^0-9]/g, '');
                  const bPhoneNum = bValue.replace(/[^0-9]/g, '');
                  comparison = aPhoneNum.localeCompare(bPhoneNum);
              } else if (aPhoneMatch && !bPhoneMatch) {
                  // a만 전화번호 형식인 경우 a를 앞으로
                  comparison = -1;
              } else if (!aPhoneMatch && bPhoneMatch) {
                  // b만 전화번호 형식인 경우 b를 앞으로
                  comparison = 1;
              } else {
                  // 둘 다 전화번호 형식이 아닌 경우 기존 로직 사용
                  // 숫자인지 확인
                  const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
                  const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
                  
                  if (!isNaN(aNum) && !isNaN(bNum)) {
                      // 숫자 비교
                      comparison = aNum - bNum;
                  } else {
                      // 문자열 비교
                      comparison = aValue.localeCompare(bValue, 'ko');
                  }
              }
          }
      }
      
      // 빈 값은 항상 아래로, 나머지는 방향에 따라 정렬
      if (aIsEmpty || bIsEmpty) {
          // 빈 값이 포함된 경우는 comparison 그대로 사용 (이미 빈 값이 뒤로 가도록 설정됨)
          return comparison;
      } else {
          // 빈 값이 없는 경우만 방향 적용
          return direction === 'asc' ? comparison : -comparison;
      }
  });

  // 정렬된 행들을 다시 DOM에 추가
  rows.forEach(row => tbody.appendChild(row));
  
  updateFilterStatus();
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
  const tbody = document.getElementById('entryTbody');
  if (!tbody) return;

  // 필터 값 업데이트
  if (filterValue.trim() === '') {
      delete window.filters[column];
  } else {
      window.filters[column] = filterValue.toLowerCase();
  }

  // 모든 행에 대해 필터 적용
  window.originalRows.forEach(row => {
      let shouldShow = true;
      
      // 모든 활성 필터 검사
      for (const [filterColumn, filterVal] of Object.entries(window.filters)) {
          const cellValue = getCellValue(row, filterColumn).toLowerCase();
          if (!cellValue.includes(filterVal)) {
              shouldShow = false;
              break;
          }
      }
      
      row.style.display = shouldShow ? '' : 'none';
  });

  // 현재 정렬이 활성화되어 있으면 다시 정렬
  if (window.currentSort.column) {
      sortTable(window.currentSort.column, window.currentSort.direction);
  }
  
  updateFilterStatus();
}

function clearAllFilters() {
  // 모든 필터 입력창 초기화
  const filterInputs = document.querySelectorAll('.filter-input');
  filterInputs.forEach(input => {
      input.value = '';
  });

  // 필터 상태 초기화
  window.filters = {};

  // 모든 행 표시
  window.originalRows.forEach(row => {
      row.style.display = '';
  });

  // 정렬 상태 초기화
  window.currentSort = { column: null, direction: null };
  updateSortButtonStates();
  
  // 탭 상태 초기화
  window.currentStatusTab = null;
  document.querySelectorAll('.status-tab').forEach(tab => {
      tab.classList.remove('active');
  });
  // 전체 탭 활성화
  const allTab = document.querySelector('.status-tab');
  if (allTab) allTab.classList.add('active');
  
  updateFilterStatus();
}

function updateSortButtonStates(activeColumn = null, activeDirection = null) {
  // 모든 정렬 버튼 비활성화
  document.querySelectorAll('.sort-btn').forEach(btn => {
      btn.classList.remove('active');
  });

  // 활성 정렬 버튼 표시 (정렬이 활성화된 경우에만)
  if (activeColumn && activeDirection) {
      const headerTh = document.querySelector(`th[data-column="${activeColumn}"]`);
      if (headerTh) {
          const buttons = headerTh.querySelectorAll('.sort-btn');
          buttons.forEach(btn => {
              if ((activeDirection === 'asc' && btn.textContent === '▲') ||
                  (activeDirection === 'desc' && btn.textContent === '▼')) {
                  btn.classList.add('active');
              }
          });
      }
  }
}

function updateFilterStatus(someObj) {
    console.log("updateFilterStatus 호출됨");
    if (!someObj) return;
  const statusElement = document.getElementById('filterStatus');
  if (!statusElement) return;

  const totalRows = window.originalRows.length;
  const visibleRows = window.originalRows.filter(row => 
      row.style.display !== 'none'
  ).length;

  const activeFilters = Object.keys(window.filters).length;
  const sortActive = window.currentSort.column !== null;
  const tabActive = window.currentStatusTab !== null;

  let statusText = '';
  
  if (activeFilters === 0 && !sortActive && !tabActive) {
      statusText = `전체 데이터 표시 중 (${totalRows}건)`;
  } else {
      statusText = `${visibleRows}/${totalRows}건 표시`;
      
      if (activeFilters > 0) {
          statusText += ` (필터 ${activeFilters}개 적용)`;
      }
      
      if (sortActive) {
          statusText += ` (${window.currentSort.column} ${window.currentSort.direction === 'asc' ? '오름차순' : '내림차순'} 정렬)`;
      }
      
      if (tabActive) {
          const activeTab = document.querySelector('.status-tab.active');
          const tabName = activeTab ? activeTab.textContent : '상태';
          statusText += ` (${tabName} 탭 선택)`;
      }
  }

  statusElement.textContent = statusText;
}