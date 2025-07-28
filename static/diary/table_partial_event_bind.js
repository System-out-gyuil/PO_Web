// 테이블 새로고침 후 모든 이벤트와 기능 재초기화
(function() {
  // 컬럼 리사이저 재초기화
  if (typeof reinitializeColumnResizer === 'function') {
      setTimeout(() => {
          reinitializeColumnResizer();
          
          // 저장된 컬럼 너비 값들 복원
          const headers = document.querySelectorAll('#entryTable thead th[data-column]');
          headers.forEach((header) => {
              const attrName = header.getAttribute('data-column');
              if (attrName) {
                  const savedWidth = localStorage.getItem(`column_width_${attrName}`);
                  const savedMaxWidth = localStorage.getItem(`column_max_width_${attrName}`);
                  const dataWidth = header.getAttribute('data-width');
                  
                  // 우선순위: localStorage > data-width > 기본값
                  let width = null;
                  if (savedWidth) {
                      width = parseInt(savedWidth);
                      console.log(`localStorage에서 너비 복원: ${attrName} = ${width}px`);
                  } else if (dataWidth) {
                      width = parseInt(dataWidth);
                      console.log(`data-width에서 너비 적용: ${attrName} = ${width}px`);
                  }
                  
                  if (width) {
                      // 헤더에 너비 적용
                      header.style.width = width + 'px';
                      header.style.minWidth = width + 'px';
                      header.style.maxWidth = width + 'px';
                      
                      // 셀에도 너비 적용
                      const cells = document.querySelectorAll(`#entryTable td[data-field="${attrName}"]`);
                      cells.forEach(cell => {
                          cell.style.width = width + 'px';
                          cell.style.minWidth = width + 'px';
                          cell.style.maxWidth = width + 'px';
                          cell.style.overflow = 'hidden';
                          cell.style.textOverflow = 'ellipsis';
                          cell.style.whiteSpace = 'nowrap';
                      });
                      
                      console.log(`리렌더링 후 컬럼 너비 적용: ${attrName} = ${width}px`);
                  }
                  
                  // 최대 너비도 복원
                  if (savedMaxWidth) {
                      const cells = document.querySelectorAll(`#entryTable td[data-field="${attrName}"]`);
                      cells.forEach(cell => {
                          cell.style.maxWidth = savedMaxWidth + 'px';
                          cell.style.overflow = 'hidden';
                          cell.style.textOverflow = 'ellipsis';
                          cell.style.whiteSpace = 'nowrap';
                      });
                      console.log(`리렌더링 후 max-width 복원: ${attrName} = ${savedMaxWidth}px`);
                  }
              }
          });
      }, 200);
  }
  
  // 테이블 셀 이벤트 재바인딩
  if (typeof bindTableCellEvents === 'function') {
      setTimeout(() => {
          bindTableCellEvents();
      }, 100);
  }
  
  // 드롭다운 옵션 실시간 업데이트를 위한 전역 이벤트 리스너 재설정
  if (typeof setupDropdownUpdateListeners === 'function') {
      setTimeout(() => {
          setupDropdownUpdateListeners();
      }, 50);
  }
  
  // 드래그앤드롭 재초기화
  if (typeof reinitializeDragDrop === 'function') {
      setTimeout(() => {
          reinitializeDragDrop();
      }, 300);
  }
  
  // 칸반보드 정렬 재초기화
  if (typeof bindKanbanSortable === 'function') {
      setTimeout(() => {
          bindKanbanSortable();
      }, 200);
  }
  
  // 체크박스 이벤트 재바인딩
  if (typeof bindCheckboxEvents === 'function') {
      setTimeout(() => {
          bindCheckboxEvents();
      }, 150);
  }
  
  // 상세보기 버튼 이벤트 재바인딩
  if (typeof bindDetailButtonEvents === 'function') {
      setTimeout(() => {
          bindDetailButtonEvents();
      }, 200);
  }
  
  // 컬럼 드래그앤드롭 재초기화
  if (typeof initializeColumnDragDrop === 'function') {
      setTimeout(() => {
          initializeColumnDragDrop();
      }, 500);
  }
  
  // 상태 필터 재적용 (상태 탭이 활성화된 경우)
  if (window.currentStatusTab !== null && typeof applyStatusFilter === 'function') {
      setTimeout(() => {
          applyStatusFilter();
      }, 300);
  }
  
  // 필터 상태 업데이트
  if (typeof updateFilterStatus === 'function') {
      setTimeout(() => {
          updateFilterStatus();
      }, 100);
  }
  
  // 테이블 행 드래그앤드롭(SortableJS) 재초기화
  if (typeof Sortable !== 'undefined') {
      setTimeout(() => {
          const tbody = document.getElementById('entryTbody');
          if (tbody) {
              // 기존 Sortable 인스턴스가 있다면 제거
              if (window.rowSortable) {
                  window.rowSortable.destroy();
              }
              
              // 새로운 Sortable 인스턴스 생성
              window.rowSortable = new Sortable(tbody, {
                  handle: '.drag-handle',
                  animation: 150,
                  onEnd: function (evt) {
                      // 순서 변경 시 서버에 반영
                      const ids = Array.from(document.querySelectorAll('#entryTbody tr[data-id]')).map(tr => tr.getAttribute('data-id'));
                      fetch('/sales/reorder/', {
                          method: 'POST',
                          headers: {'Content-Type': 'application/json'},
                          body: JSON.stringify({order: ids})
                      }).then(res => res.json()).then(data => {
                          if(!data.success) alert('순서 저장 실패: '+data.error);
                      }).catch(() => alert('순서 저장 중 오류 발생'));
                  }
              });
              console.log('테이블 행 드래그앤드롭 재초기화 완료');
          }
      }, 400);
  }
  
  // 이벤트 위임을 통한 동적 요소 이벤트 처리
  document.addEventListener('click', function(e) {
      // 드롭다운 셀 클릭 처리 - openDropdown 함수 사용
      if (e.target.closest('td[data-type="dropdown"]')) {
          const cell = e.target.closest('td[data-type="dropdown"]');
          const rowId = cell.closest('tr').getAttribute('data-id');
          const fieldName = cell.getAttribute('data-field');
          const currentValue = cell.getAttribute('data-value') || '';
          
          // 이미 드롭다운이 열려있으면 무시
          if (document.querySelector('.dropdown-edit')) {
              return;
          }
          
          if (typeof openDropdown === 'function') {
              openDropdown(cell, fieldName, rowId, currentValue);
          }
      }
      
      // 회사명 셀 클릭 처리 (상세보기)
      if (e.target.closest('.more-btn')) {
          const row = e.target.closest('tr');
          const rowId = row.getAttribute('data-id');
          
          if (typeof showDetailModal === 'function') {
              fetch('/sales/get_row_details/' + rowId + '/')
                  .then(r => r.json())
                  .then(function(data) {
                      if (data.success) {
                          showDetailModal(data.row_data, data.row_id);
                      }
                  });
          }
      }
      
      // 기대출 상세보기 클릭 처리
      if (e.target.closest('.debt-summary')) {
          const row = e.target.closest('tr');
          const rowId = row.getAttribute('data-id');
          
          if (typeof openDebtDetailsModal === 'function') {
              openDebtDetailsModal(rowId);
          }
      }
  });
  
  // 키보드 이벤트 위임
  document.addEventListener('keydown', function(e) {
      // Enter 키로 셀 편집 완료
      if (e.key === 'Enter' && e.target.closest('td[contenteditable="true"]')) {
          e.preventDefault();
          const cell = e.target.closest('td[contenteditable="true"]');
          const rowId = cell.closest('tr').getAttribute('data-id');
          const fieldName = cell.getAttribute('data-field');
          const value = cell.textContent.trim();
          
          if (typeof updateCellValue === 'function') {
              updateCellValue(rowId, fieldName, value);
          }
      }
      
      // Escape 키로 편집 취소
      if (e.key === 'Escape' && e.target.closest('td[contenteditable="true"]')) {
          e.preventDefault();
          const cell = e.target.closest('td[contenteditable="true"]');
          cell.textContent = cell.getAttribute('data-original-value') || '';
          cell.removeAttribute('contenteditable');
          cell.classList.remove('editing');
      }
  });
  
  console.log('테이블 partial 로드 완료 - 모든 이벤트 재초기화됨');
})();