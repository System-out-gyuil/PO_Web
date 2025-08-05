// 테이블 새로고침 후 모든 이벤트와 기능 재초기화
(function() {
    // 사용자 세션 초기화
    if (typeof initializeUserSession === 'function') {
      initializeUserSession().then(() => {
        console.log('사용자 세션 초기화 완료');
      });
    }
    
    // 컬럼 리사이저 재초기화
    if (typeof reinitializeColumnResizer === 'function') {
        setTimeout(() => {
            reinitializeColumnResizer();
            
            // 저장된 컬럼 너비 값들 복원 (사용자별)
            const userId = getCurrentUserId();
            const headers = document.querySelectorAll('#entryTable thead th[data-column]');
            headers.forEach((header) => {
                const attrName = header.getAttribute('data-column');
                if (attrName) {
                    const savedWidth = localStorage.getItem(`column_width_${attrName}_${userId}`);
                    const savedMaxWidth = localStorage.getItem(`column_max_width_${attrName}_${userId}`);
                    const dataWidth = header.getAttribute('data-width');
                    
                    // 우선순위: localStorage > data-width > 기본값
                    let width = null;
                    if (savedWidth) {
                        width = parseInt(savedWidth);
                        console.log(`localStorage에서 너비 복원: ${attrName} = ${width}px (사용자: ${userId})`);
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
                        console.log(`리렌더링 후 max-width 복원: ${savedMaxWidth}px`);
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
    
    // 정렬/필터 기능 재초기화 (개선된 타이밍 - 데이터 양에 관계없이 안정적)
    function initializeTableFilters() {
        console.log('정렬/필터 기능 재초기화 시작');
        
        // DOM이 완전히 로드되었는지 확인 (더 엄격한 조건)
        const tbody = document.getElementById('entryTbody');
        const filterInputs = document.querySelectorAll('.filter-input');
        const sortButtons = document.querySelectorAll('.sort-btn');
        
        console.log('DOM 상태 확인:', {
            tbody: !!tbody,
            tbodyRows: tbody ? tbody.rows.length : 0,
            filterInputs: filterInputs.length,
            sortButtons: sortButtons.length
        });
        
        // 모든 필수 요소가 로드되었는지 확인
        if (!tbody || tbody.rows.length === 0 || filterInputs.length === 0) {
            console.log('DOM이 아직 준비되지 않음, 재시도...');
            setTimeout(initializeTableFilters, 200);
            return;
        }
        
        console.log('DOM 준비 완료, 이벤트 바인딩 시작');
        
        // 리랜더링 후 정렬/필터 상태 복원
        if (typeof reinitializeTableFilters === 'function') {
            reinitializeTableFilters();
        } else {
            // 테이블 데이터 초기화
            if (typeof initializeTableData === 'function') {
                initializeTableData();
            }
            
            // 저장된 상태 복원
            if (typeof restoreTableState === 'function') {
                restoreTableState();
            }
        }
        
        // 정렬 버튼 이벤트 재바인딩 (개선된 방식)
        sortButtons.forEach(btn => {
            // 기존 이벤트 리스너 제거 (더 안전한 방식)
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            // 새로운 버튼에 이벤트 리스너 추가
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const column = this.getAttribute('data-column');
                const direction = this.getAttribute('data-direction');
                
                console.log('정렬 버튼 클릭:', column, direction);
                
                if (typeof sortTable === 'function') {
                    sortTable(column, direction);
                }
            });
        });
        
        // 필터 입력 필드 이벤트 재바인딩 (개선된 방식)
        filterInputs.forEach(input => {
            // 기존 이벤트 리스너 제거 (더 안전한 방식)
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);
            
            // 새로운 입력 필드에 이벤트 리스너 추가
            newInput.addEventListener('input', function() {
                const column = this.getAttribute('data-column');
                const value = this.value;
                
                console.log('필터 입력:', column, value);
                
                if (typeof filterTable === 'function') {
                    filterTable(column, value);
                }
            });
            
            // 추가: keyup 이벤트도 바인딩 (더 안정적인 필터링)
            newInput.addEventListener('keyup', function() {
                const column = this.getAttribute('data-column');
                const value = this.value;
                
                console.log('필터 키업:', column, value);
                
                if (typeof filterTable === 'function') {
                    filterTable(column, value);
                }
            });
        });
        
        // 필터 초기화 버튼 이벤트 재바인딩
        const clearFilterBtn = document.querySelector('#clearFiltersBtn');
        if (clearFilterBtn) {
            const newBtn = clearFilterBtn.cloneNode(true);
            clearFilterBtn.parentNode.replaceChild(newBtn, clearFilterBtn);
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('필터 초기화 버튼 클릭');
                if (typeof clearAllFilters === 'function') {
                    clearAllFilters();
                }
            });
        }
        
        // 필터 상태 업데이트
        if (typeof updateFilterStatus === 'function') {
            updateFilterStatus();
        }
        
        console.log('정렬/필터 기능 재초기화 완료');
    }
    
    // 초기 실행 (더 긴 지연 시간으로 데이터 로딩 대기)
    setTimeout(initializeTableFilters, 500);
    
    // 추가 안전장치: 1초 후 한 번 더 시도
    setTimeout(() => {
        const tbody = document.getElementById('entryTbody');
        if (tbody && tbody.rows.length > 0) {
            console.log('추가 안전장치: 필터 이벤트 재바인딩');
            const filterInputs = document.querySelectorAll('.filter-input');
            filterInputs.forEach(input => {
                // 이벤트 리스너가 이미 있는지 확인
                const hasInputListener = input._hasInputListener;
                if (!hasInputListener) {
                    input.addEventListener('input', function() {
                        const column = this.getAttribute('data-column');
                        const value = this.value;
                        console.log('안전장치 필터 입력:', column, value);
                        if (typeof filterTable === 'function') {
                            filterTable(column, value);
                        }
                    });
                    input._hasInputListener = true;
                }
            });
        }
    }, 1000);
    
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
    
    // 새로 만들기 버튼 이벤트 재바인딩
    if (typeof window.addNewRow === 'function') {
        console.log('addNewRow 함수가 이미 window에 바인딩되어 있습니다.');
    } else {
        console.log('addNewRow 함수를 window에 바인딩합니다.');
        // addNewRow 함수가 이미 window에 바인딩되어 있으므로 추가 작업 불필요
    }
    
    // 일괄 삭제 버튼 이벤트 재바인딩
    if (typeof updateBulkDeleteButton === 'function') {
        setTimeout(() => {
            updateBulkDeleteButton();
        }, 150);
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
        
        // 삭제 버튼 클릭 처리
        if (e.target.closest('.delete-row-btn')) {
            const row = e.target.closest('tr');
            const rowId = row.getAttribute('data-id');
            
            if (typeof deleteRow === 'function') {
                deleteRow(rowId);
            }
        }
        
        // 복제 버튼 클릭 처리
        if (e.target.closest('.duplicate-row-btn')) {
            const row = e.target.closest('tr');
            const rowId = row.getAttribute('data-id');
            
            if (typeof duplicateRow === 'function') {
                duplicateRow(rowId);
            }
        }
        
        // 체크박스 클릭 처리
        if (e.target.closest('.row-checkbox')) {
            if (typeof updateBulkDeleteButton === 'function') {
                updateBulkDeleteButton();
            }
        }
        
        // 전체 선택 체크박스 클릭 처리
        if (e.target.closest('#selectAllCheckbox')) {
            if (typeof toggleSelectAll === 'function') {
                toggleSelectAll(e.target);
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
    
    // 더블클릭 이벤트 위임 (셀 편집)
    document.addEventListener('dblclick', function(e) {
        // 편집 가능한 셀 더블클릭 처리
        if (e.target.closest('td[data-field]') && !e.target.closest('td[data-type="dropdown"]') && 
            !e.target.closest('.name-container') && !e.target.closest('.debt-summary') &&
            !e.target.closest('.cell-button-container')) {
            
            const cell = e.target.closest('td[data-field]');
            const fieldName = cell.getAttribute('data-field');
            
            // 편집 불가능한 필드들 제외
            const nonEditableFields = ['회사명', '기대출'];
            if (nonEditableFields.includes(fieldName)) {
                return;
            }
            
            // 편집 모드 활성화
            cell.setAttribute('contenteditable', 'true');
            cell.classList.add('editing');
            cell.setAttribute('data-original-value', cell.textContent.trim());
            cell.focus();
            
            // 텍스트 선택
            const range = document.createRange();
            range.selectNodeContents(cell);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        }
    });
    
    console.log('테이블 partial 로드 완료 - 모든 이벤트 재초기화됨');
  })();