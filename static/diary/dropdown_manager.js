// 통합된 드롭다운 관리 시스템

// 전역 변수로 현재 열린 드롭다운 추적
let currentOpenDropdown = null;
let currentTriggerElement = null;

function closeAllDropdowns() {
    console.log('모든 드롭다운 닫기 실행');
    
    // 전역 dropdown 변수 정리
    if (window.dropdown && window.dropdown.parentNode) {
        window.dropdown.parentNode.removeChild(window.dropdown);
        window.dropdown = null;
    }
    
    // 모든 드롭다운 요소들 제거
    document.querySelectorAll('.dropdown-edit').forEach(el => {
        if (el.parentNode) {
            el.parentNode.removeChild(el);
        }
    });
    
    // 모든 모달 드롭다운 제거
    document.querySelectorAll('[id^="modal-"]').forEach(el => {
        if (el.parentNode) {
            el.parentNode.removeChild(el);
        }
    });
    
    // 전역 변수 초기화
    currentOpenDropdown = null;
    currentTriggerElement = null;
    
    // 전역 클릭 핸들러 제거
    removeGlobalClickHandler();
}

function closeDropdown() {
    console.log('closeDropdown 함수 실행');
    closeAllDropdowns();
}

function isDropdownOpen() {
    return document.querySelectorAll('.dropdown-edit').length > 0 || 
           document.querySelectorAll('[id^="modal-"]').length > 0 ||
           (window.dropdown && window.dropdown.parentNode) ||
           currentOpenDropdown !== null;
}

// 외부 클릭 이벤트 리스너 관리
let globalClickHandler = null;

function removeGlobalClickHandler() {
    if (globalClickHandler) {
        document.removeEventListener('mousedown', globalClickHandler);
        globalClickHandler = null;
    }
}

function addGlobalClickHandler(dropdown, triggerElement) {
    removeGlobalClickHandler();
    
    globalClickHandler = function(e) {
        // 드롭다운이나 트리거 요소 내부 클릭이 아닌 경우에만 닫기
        if (dropdown && !dropdown.contains(e.target) && 
            (!triggerElement || !triggerElement.contains(e.target))) {
            console.log('외부 클릭으로 드롭다운 닫기');
            closeAllDropdowns();
        }
    };
    
    // 약간의 지연 후 이벤트 리스너 추가 (즉시 닫히는 것을 방지)
    setTimeout(() => {
        document.addEventListener('mousedown', globalClickHandler);
    }, 100);
}

function openDropdown(td, type, id, currentId, currentSubregion) {
    console.log('openDropdown 호출됨:', {td, type, id, currentId, currentSubregion});
    
    // 이미 같은 셀에서 드롭다운이 열려있는지 확인
    if (currentOpenDropdown && currentTriggerElement === td) {
        console.log('같은 셀에서 이미 드롭다운이 열려있음, 닫기만 실행');
        closeAllDropdowns();
        return;
    }
    
    // 기존 모든 드롭다운 닫기
    closeAllDropdowns();
    
    // 클릭된 셀의 위치 정보 가져오기
    const rect = td.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    
    // 새 드롭다운 생성
    window.dropdown = document.createElement('div');
    window.dropdown.className = 'dropdown-edit';
    window.dropdown.id = 'current-dropdown-' + Date.now();
    
    // 지역/상세지역 드롭다운임을 표시하는 특별한 속성 추가
    if (type === 'region' || type === 'region_detail') {
        window.dropdown.setAttribute('data-region-type', type);
        window.dropdown.setAttribute('data-protected', 'true');
    }
    
    // 드롭다운이 성공적으로 생성되었는지 확인
    if (!window.dropdown) {
        console.error('드롭다운 생성 실패');
        return;
    }
    
    // 로컬 변수로 드롭다운 참조 저장
    const currentDropdown = window.dropdown;
    
    // 전역 변수에 현재 드롭다운 정보 저장
    currentOpenDropdown = currentDropdown;
    currentTriggerElement = td;
    
    // 셀 바로 아래에 위치하도록 계산
    const topPosition = rect.bottom + scrollTop + 2;
    const leftPosition = rect.left + scrollLeft;
    
    // 화면 경계 체크 및 조정
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const dropdownWidth = Math.max(rect.width, 150);
    const dropdownHeight = 200; // max-height
    
    // 오른쪽 경계 체크
    let adjustedLeft = leftPosition;
    if (leftPosition + dropdownWidth > viewportWidth) {
        adjustedLeft = viewportWidth - dropdownWidth - 10;
    }
    
    // 아래쪽 경계 체크
    let adjustedTop = topPosition;
    if (topPosition + dropdownHeight > viewportHeight + scrollTop) {
        // 셀 위에 표시
        adjustedTop = rect.top + scrollTop - dropdownHeight - 2;
    }
    
    // 최소 위치 보장
    adjustedLeft = Math.max(10, adjustedLeft);
    adjustedTop = Math.max(10, adjustedTop);
    
    // 드롭다운 스타일 설정 - 더 명확하고 강제적인 스타일 적용
    Object.assign(currentDropdown.style, {
        position: 'absolute',
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: '4px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        zIndex: '9999',
        maxHeight: '200px',
        overflowY: 'auto',
        minWidth: '300px',
        width: dropdownWidth + 'px',
        fontSize: '14px',
        fontFamily: 'inherit',
        top: adjustedTop + 'px',
        left: adjustedLeft + 'px',
        padding: '4px 0',
        display: 'block',
        visibility: 'visible',
        opacity: '1',
        backgroundColor: 'white',
        color: '#333'
    });
    
    console.log('드롭다운 위치 설정:', {top: adjustedTop, left: adjustedLeft, cellWidth: rect.width});
    
    // 전역 클릭 핸들러 추가
    addGlobalClickHandler(currentDropdown, td);
    
    // 스크롤 시 드롭다운 위치 업데이트 함수 (지역/상세지역용)
    function updateDropdownPosition() {
        if (currentDropdown && td) {
            const rect = td.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            
            // 화면 경계 체크 및 조정
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            const dropdownWidth = Math.max(rect.width, 150);
            const dropdownHeight = 200;
            
            // 오른쪽 경계 체크
            let adjustedLeft = rect.left + scrollLeft;
            if (adjustedLeft + dropdownWidth > viewportWidth) {
                adjustedLeft = viewportWidth - dropdownWidth - 10;
            }
            
            // 아래쪽 경계 체크
            let adjustedTop = rect.bottom + scrollTop + 2;
            if (adjustedTop + dropdownHeight > viewportHeight + scrollTop) {
                // 셀 위에 표시
                adjustedTop = rect.top + scrollTop - dropdownHeight - 2;
            }
            
            // 최소 위치 보장
            adjustedLeft = Math.max(10, adjustedLeft);
            adjustedTop = Math.max(10, adjustedTop);
            
            currentDropdown.style.top = adjustedTop + 'px';
            currentDropdown.style.left = adjustedLeft + 'px';
        }
    }
    
    // 스크롤 이벤트 리스너 추가 (지역/상세지역용)
    const scrollHandler = function() {
        updateDropdownPosition();
    };
    
    window.addEventListener('scroll', scrollHandler);
    window.addEventListener('resize', scrollHandler);
    
    if (type === 'region') {
        console.log('지역 드롭다운 처리');
        // 지역 드롭다운
        var regionNames = ['서울','경기','인천','대구','경북', '경남', '부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
        let selectedRegion = currentId || '서울';
        
        let html = '';
        regionNames.forEach(function(region) {
            const isSelected = region === selectedRegion;
            html += `
              <div class="dropdown-option-container" style="padding: 6px 10px; border-bottom: 1px solid #f0f0f0;">
                <div class="dropdown-item" data-option-id="${region}" 
                     style="cursor: pointer; 
                            background: ${isSelected ? '#e3f2fd' : 'white'}; 
                            border-radius: 4px; 
                            padding: 6px 8px; 
                            margin-bottom: 4px;
                            ${isSelected ? 'border: 2px solid #007bff; font-weight: bold;' : 'border: 1px solid #ddd;'}
                            transition: all 0.2s;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            position: relative;">
                  <div style="display: flex; align-items: center; flex: 1; min-width: 0;">
                    <span style="flex: 1; word-wrap: break-word; word-break: break-all; color: #333; font-size: 14px; line-height: 1.4; padding: 2px 0;">${region}</span>
                  </div>
                </div>
              </div>
            `;
        });
        
        currentDropdown.innerHTML = html;
        document.body.appendChild(currentDropdown);
        
        // 지역 선택 이벤트 리스너
        currentDropdown.querySelectorAll('.dropdown-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                const selectedRegion = this.getAttribute('data-option-id');
                
                // UI 업데이트
                if (td) { 
                    td.innerHTML = `<div class="dropdown-pill" style="background:#e3f2fd; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${selectedRegion}</div>`; 
                    td.setAttribute('data-value', selectedRegion); 
                }
                
                // 서버 업데이트
                if (id && id.startsWith('temp_')) {
                    saveNewRowField(td.parentElement, 'region', selectedRegion);
                } else {
                    fetch('/sales/update_row_field/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id='+id+'&field=region&value='+encodeURIComponent(selectedRegion)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('지역 업데이트 성공');
                            // 종속된 행들 찾아서 업데이트
                            if (typeof updateDependentRows === 'function') {
                                updateDependentRows(id, 'region', selectedRegion);
                            }
                            // 실시간 동기화
                            if (typeof syncTableAndKanban === 'function') {
                                syncTableAndKanban('region');
                            }
                        } else {
                            throw new Error(data.error || '업데이트 실패');
                        }
                    })
                    .catch(error => {
                        console.error('지역 업데이트 실패:', error);
                        alert('업데이트 중 오류가 발생했습니다: ' + error.message);
                    });
                }
                
                // 드롭다운 닫기
                closeAllDropdowns();
            });
        });
        
        // 상세지역 드롭다운 열기
        currentDropdown.querySelectorAll('.dropdown-item').forEach(function(item) {
            item.addEventListener('dblclick', function(e) {
                e.stopPropagation();
                const selectedRegion = this.getAttribute('data-option-id');
                
                // 상세지역 드롭다운 열기
                openDetailDropdown(id, 'region_detail', td, selectedRegion);
            });
        });
        
    } else if (type === 'region_detail') {
        console.log('상세지역 드롭다운 처리');
        // 상세지역 드롭다운
        const currentRegion = currentId || '서울';
        const subregions = getSubregions(currentRegion);
        let selectedSubregion = currentSubregion || '';
        
        let html = '';
        subregions.forEach(function(subregion) {
            const isSelected = subregion === selectedSubregion;
            html += `
              <div class="dropdown-option-container" style="padding: 6px 10px; border-bottom: 1px solid #f0f0f0;">
                <div class="dropdown-item" data-option-id="${subregion}" 
                     style="cursor: pointer; 
                            background: ${isSelected ? '#e8f5e8' : 'white'}; 
                            border-radius: 4px; 
                            padding: 6px 8px; 
                            margin-bottom: 4px;
                            ${isSelected ? 'border: 2px solid #28a745; font-weight: bold;' : 'border: 1px solid #ddd;'}
                            transition: all 0.2s;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            position: relative;">
                  <div style="display: flex; align-items: center; flex: 1; min-width: 0;">
                    <span style="flex: 1; word-wrap: break-word; word-break: break-all; color: #333; font-size: 14px; line-height: 1.4; padding: 2px 0;">${subregion}</span>
                  </div>
                </div>
              </div>
            `;
        });
        
        currentDropdown.innerHTML = html;
        document.body.appendChild(currentDropdown);
        
        // 상세지역 선택 이벤트 리스너
        currentDropdown.querySelectorAll('.dropdown-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                const selectedSubregion = this.getAttribute('data-option-id');
                
                // UI 업데이트
                if (td) { 
                    td.innerHTML = `<div class="dropdown-pill" style="background:#e8f5e8; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${selectedSubregion}</div>`; 
                    td.setAttribute('data-value', selectedSubregion); 
                }
                
                // 서버 업데이트
                if (id && id.startsWith('temp_')) {
                    saveNewRowField(td.parentElement, 'region_detail', selectedSubregion);
                } else {
                    fetch('/sales/update_row_field/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id='+id+'&field=region_detail&value='+encodeURIComponent(selectedSubregion)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('상세지역 업데이트 성공');
                            // 종속된 행들 찾아서 업데이트
                            if (typeof updateDependentRows === 'function') {
                                updateDependentRows(id, 'region_detail', selectedSubregion);
                            }
                            // 실시간 동기화
                            if (typeof syncTableAndKanban === 'function') {
                                syncTableAndKanban('region_detail');
                            }
                        } else {
                            throw new Error(data.error || '업데이트 실패');
                        }
                    })
                    .catch(error => {
                        console.error('상세지역 업데이트 실패:', error);
                        alert('업데이트 중 오류가 발생했습니다: ' + error.message);
                    });
                }
                
                // 드롭다운 닫기
                closeAllDropdowns();
            });
        });
        
    } else {
        // 일반 드롭다운 (구분, 영업진행 등) 및 지역/상세지역 처리
        console.log('일반 드롭다운 처리 시작:', {type, id});
        
        let options = [];
        
        if (type === 'region') {
            // 지역 옵션 생성
            const regionNames = ['서울','경기','인천','대구','경북', '경남', '부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
            options = regionNames.map((region, index) => ({
                id: index + 1,
                option: region,
                color: '#007bff'
            }));
        } else if (type === 'region_detail') {
            // 상세지역 옵션 생성
            const currentRegion = currentId || '서울';
            const subregions = getSubregions(currentRegion);
            options = subregions.map((subregion, index) => ({
                id: index + 1,
                option: subregion,
                color: '#28a745'
            }));
        } else {
            // 서버에서 옵션 가져오기
            fetch('/sales/dropdown_options/?field=' + encodeURIComponent(type))
                .then(r => r.json())
                .then(function(data) {
                    console.log('드롭다운 옵션 로드됨:', data);
                    
                    if (data.options) {
                        options = data.options;
                        renderDropdownOptions(options, type, td, currentDropdown);
                    }
                })
                .catch(error => {
                    console.error('드롭다운 옵션 로드 실패:', error);
                });
            return;
        }
        
        // 지역/상세지역 옵션 렌더링
        renderDropdownOptions(options, type, td, currentDropdown);
    }
  }
  
  
  // === 드롭다운 모달 이벤트 바인딩 함수 추가 ===
  function bindDropdownModalEvents(dropdown, fieldType, options) {
    console.log('드롭다운 모달 이벤트 바인딩 시작:', fieldType);
    
    // 새 옵션 추가 기능
    const addBtn = dropdown.querySelector('.add-btn');
    const addInput = dropdown.querySelector('input[placeholder="새 옵션 추가"]');
    
    if (addBtn && addInput) {
        addBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const newOptionName = addInput.value.trim();
            if (!newOptionName) {
                alert('옵션명을 입력해주세요.');
                return;
            }
            
            // 새 옵션 추가 API 호출
            fetch('/sales/dropdown_options/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCsrfToken()
                },
                body: `field=${encodeURIComponent(fieldType)}&name=${encodeURIComponent(newOptionName)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('새 옵션 추가 성공:', data);
                    addInput.value = '';
                    
                    // 드롭다운 새로고침
                    const td = document.querySelector(`td[data-field="${fieldType}"]`);
                    if (td) {
                        openDropdown(td, fieldType, td.parentElement.getAttribute('data-id'), td.getAttribute('data-value'));
                    }
                    
                    // 실시간 동기화
                    syncTableAndKanban(fieldType);
                    
                    // 칸반보드 리렌더링
                    if (window.currentKanbanAttribute && window.currentKanbanAttribute === fieldType) {
                        updateKanbanBoard(fieldType);
                    }
                    
                    // 상태 속성인 경우 상태 탭 새로고침
                    if (window.statusAttributeName && fieldType === window.statusAttributeName) {
                        console.log('상태 속성 옵션 추가됨, 상태 탭 새로고침 시작');
                        // 상태 탭 새로고침 함수 호출
                        if (typeof refreshStatusTabs === 'function') {
                            setTimeout(() => {
                                refreshStatusTabs();
                            }, 100);
                        }
                    }
                } else {
                    alert('옵션 추가 실패: ' + (data.error || ''));
                }
            })
            .catch(error => {
                console.error('옵션 추가 실패:', error);
                alert('옵션 추가 중 오류가 발생했습니다: ' + error.message);
            });
        });
        
        // Enter 키로 추가
        addInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                addBtn.click();
            }
        });
    }
    
    // 색상 변경 기능
    dropdown.querySelectorAll('input[data-color-edit]').forEach(function(colorInput) {
        // 색상 변경 이벤트 (색상 선택 완료 시)
        colorInput.addEventListener('change', function(e) {
            e.stopPropagation();
            e.preventDefault();
            const optionId = this.getAttribute('data-color-edit');
            const newColor = this.value;
            
            fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldType)}&id=${optionId}&color=${encodeURIComponent(newColor)}`, {
                method: 'PUT',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('색상 변경 성공:', data);
                    
                    // 드롭다운 내부 색상 즉시 업데이트
                    const optionContainer = this.closest('.dropdown-option-container');
                    const dropdownItem = optionContainer.querySelector('.dropdown-item');
                    if (dropdownItem) {
                        dropdownItem.style.background = hexToRgba(newColor, 0.18);
                    }
                    
                    // 테이블과 칸반보드 동기화
                    syncTableAndKanban(fieldType);
                    
                    // 색상 변경 후 추가 동기화 처리
                    setTimeout(() => {
                        // 테이블 셀들의 색상 정보를 즉시 업데이트
                        const cells = document.querySelectorAll(`td[data-field="${fieldType}"]`);
                        cells.forEach(cell => {
                            const currentValue = cell.getAttribute('data-value');
                            if (currentValue) {
                                try {
                                    // JSON 형태로 저장된 다중선택 값인지 확인
                                    const parsed = JSON.parse(currentValue);
                                    if (Array.isArray(parsed) && parsed.length > 0) {
                                        // 다중선택 값 처리 - 해당 옵션 ID가 포함된 경우 색상 업데이트
                                        if (parsed.includes(Number(optionId))) {
                                            const pill = cell.querySelector('.dropdown-pill');
                                            if (pill) {
                                                pill.style.background = hexToRgba(newColor, 0.18);
                                            }
                                        }
                                    } else {
                                        // 단일 선택 값 처리
                                        if (Number(currentValue) === Number(optionId)) {
                                            const pill = cell.querySelector('.dropdown-pill');
                                            if (pill) {
                                                pill.style.background = hexToRgba(newColor, 0.18);
                                            }
                                        }
                                    }
                                } catch (e) {
                                    // JSON 파싱 실패 시 단일 값으로 처리
                                    if (Number(currentValue) === Number(optionId)) {
                                        const pill = cell.querySelector('.dropdown-pill');
                                        if (pill) {
                                            pill.style.background = hexToRgba(newColor, 0.18);
                                        }
                                    }
                                }
                            }
                        });
                    }, 50);
                    
                    // 상태 속성인 경우에만 상태 탭 새로고침 (view_select 문제 방지)
                    if (window.statusAttributeName && fieldType === window.statusAttributeName) {
                        console.log('상태 속성 색상 변경됨, 상태 탭 새로고침 시작');
                        // 상태 탭 새로고침 함수 호출 - 지연 시간을 늘려서 동기화 완료 후 실행
                        if (typeof refreshStatusTabs === 'function') {
                            // 색상 변경 후 상태 탭 새로고침을 더 안전하게 처리
                            setTimeout(() => {
                                try {
                                    // 상태 탭 새로고침 전에 현재 설정 백업
                                    const currentSettings = {};
                                    if (window.allAttributes) {
                                        window.allAttributes.forEach(attr => {
                                            if (attr.view_select) {
                                                currentSettings[attr.id] = { ...attr.view_select };
                                            }
                                        });
                                    }
                                    
                                    refreshStatusTabs();
                                    console.log('상태 탭 새로고침 완료');
                                    
                                    // 새로고침 후 설정 복원 확인
                                    setTimeout(() => {
                                        if (window.allAttributes && Object.keys(currentSettings).length > 0) {
                                            window.allAttributes.forEach(attr => {
                                                if (currentSettings[attr.id]) {
                                                    attr.view_select = { ...currentSettings[attr.id] };
                                                }
                                            });
                                            console.log('상태 탭 새로고침 후 설정 복원 완료');
                                        }
                                    }, 100);
                                } catch (error) {
                                    console.error('상태 탭 새로고침 중 오류:', error);
                                }
                            }, 1000); // 더 긴 지연 시간으로 안정성 확보
                        }
                    }
                } else {
                    alert('색상 변경 실패: ' + (data.error || ''));
                }
            })
            .catch(error => {
                console.error('색상 변경 실패:', error);
                alert('색상 변경 중 오류가 발생했습니다: ' + error.message);
            });
        });
        
        // 실시간 색상 변경 이벤트 (색상 선택 중)
        colorInput.addEventListener('input', function(e) {
            e.stopPropagation();
            const optionId = this.getAttribute('data-color-edit');
            const newColor = this.value;
            
            // 드롭다운 내부 색상 실시간 업데이트
            const optionContainer = this.closest('.dropdown-option-container');
            const dropdownItem = optionContainer.querySelector('.dropdown-item');
            if (dropdownItem) {
                dropdownItem.style.background = hexToRgba(newColor, 0.18);
            }
            
            // 테이블 셀들의 색상 정보를 실시간으로 업데이트
            const cells = document.querySelectorAll(`td[data-field="${fieldType}"]`);
            cells.forEach(cell => {
                const currentValue = cell.getAttribute('data-value');
                if (currentValue) {
                    try {
                        // JSON 형태로 저장된 다중선택 값인지 확인
                        const parsed = JSON.parse(currentValue);
                        if (Array.isArray(parsed) && parsed.length > 0) {
                            // 다중선택 값 처리 - 해당 옵션 ID가 포함된 경우 색상 업데이트
                            if (parsed.includes(Number(optionId))) {
                                const pill = cell.querySelector('.dropdown-pill');
                                if (pill) {
                                    pill.style.background = hexToRgba(newColor, 0.18);
                                }
                            }
                        } else {
                            // 단일 선택 값 처리
                            if (Number(currentValue) === Number(optionId)) {
                                const pill = cell.querySelector('.dropdown-pill');
                                if (pill) {
                                    pill.style.background = hexToRgba(newColor, 0.18);
                                }
                            }
                        }
                    } catch (e) {
                        // JSON 파싱 실패 시 단일 값으로 처리
                        if (Number(currentValue) === Number(optionId)) {
                            const pill = cell.querySelector('.dropdown-pill');
                            if (pill) {
                                pill.style.background = hexToRgba(newColor, 0.18);
                            }
                        }
                    }
                }
            });
        });
        
        // 컬러피커 클릭 시 드롭다운이 닫히지 않도록 추가 이벤트 처리
        colorInput.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        colorInput.addEventListener('mousedown', function(e) {
            e.stopPropagation();
        });
    });
    
    // 수정 기능
    dropdown.querySelectorAll('button[data-edit]').forEach(function(editBtn) {
        editBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const optionId = this.getAttribute('data-edit');
            const optionContainer = this.closest('.dropdown-option-container');
            const optionText = optionContainer.querySelector('span');
            const oldText = optionText.textContent;
            
            // 입력 필드 생성
            const input = document.createElement('input');
            input.type = 'text';
            input.value = oldText;
            input.className = 'table-edit-input';
            input.style.cssText = `
                flex: 1;
                padding: 4px 8px;
                border: 1px solid #007bff;
                border-radius: 3px;
                font-size: 12px;
                margin-right: 4px;
                background: white;
                outline: none;
            `;
            
            // 기존 텍스트를 입력 필드로 교체
            optionText.style.display = 'none';
            optionText.parentNode.insertBefore(input, optionText);
            
            // 포커스와 선택을 지연시켜 DOM 업데이트 완료 후 실행
            setTimeout(() => {
                input.focus();
                input.select();
            }, 10);
            
            // 수정 완료 처리 함수
            function saveEdit() {
                const newText = input.value.trim();
                if (!newText) {
                    alert('옵션명을 입력해주세요.');
                    return;
                }
                
                fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldType)}&id=${optionId}&name=${encodeURIComponent(newText)}`, {
                    method: 'PUT',
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('옵션 수정 성공:', data);
                        optionText.textContent = newText;
                        optionText.style.display = '';
                        input.remove();
                        
                        // 실시간 동기화
                        syncTableAndKanban(fieldType);
                        // 상태 속성인 경우 상태 탭 새로고침
                        if (window.statusAttributeName && fieldType === window.statusAttributeName && typeof refreshStatusTabs === 'function') {
                            setTimeout(() => { refreshStatusTabs(); }, 100);
                        }
                    } else {
                        alert('옵션 수정 실패: ' + (data.error || ''));
                        optionText.style.display = '';
                        input.remove();
                    }
                })
                .catch(error => {
                    console.error('옵션 수정 실패:', error);
                    alert('옵션 수정 중 오류가 발생했습니다: ' + error.message);
                    optionText.style.display = '';
                    input.remove();
                });
            }
            
            // 취소 처리 함수
            function cancelEdit() {
                optionText.style.display = '';
                input.remove();
            }
            
            input.onblur = function() {
                setTimeout(() => {
                    if (input.parentNode) {
                        saveEdit();
                    }
                }, 100);
            };
            
            input.onkeydown = function(e) {
                if (e.key === 'Enter') {
                    saveEdit();
                } else if (e.key === 'Escape') {
                    cancelEdit();
                }
            };
        });
    });
    
    // 삭제 기능
    dropdown.querySelectorAll('button[data-del]').forEach(function(delBtn) {
        delBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const optionId = this.getAttribute('data-del');
            const optionContainer = this.closest('.dropdown-option-container');
            const optionText = optionContainer.querySelector('span').textContent;
            if (confirm(`"${optionText}" 옵션을 삭제하시겠습니까?\n\n이 옵션을 사용하는 모든 데이터가 초기화됩니다.`)) {
                fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldType)}&id=${optionId}`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('옵션 삭제 성공:', data);
                        optionContainer.remove();
                        syncTableAndKanban(fieldType);
                        
                        // 칸반보드 리렌더링
                        if (window.currentKanbanAttribute && window.currentKanbanAttribute === fieldType) {
                            updateKanbanBoard(fieldType);
                        }
                        
                        // 상태 속성인 경우 상태 탭 새로고침
                        if (window.statusAttributeName && fieldType === window.statusAttributeName) {
                            console.log('상태 속성 옵션 삭제됨, 상태 탭 새로고침 시작');
                            // 상태 탭 새로고침 함수 호출
                            if (typeof refreshStatusTabs === 'function') {
                                setTimeout(() => {
                                    refreshStatusTabs();
                                }, 100);
                            }
                        }
                    } else {
                        alert('옵션 삭제 실패: ' + (data.error || ''));
                    }
                })
                .catch(error => {
                    console.error('옵션 삭제 실패:', error);
                    alert('옵션 삭제 중 오류가 발생했습니다: ' + error.message);
                });
            }
        });
    });
  }
  
  
  // 모달용 일반 드롭다운 옵션 표시 함수
  function showModalDropdownOptions(rowId, fieldName, btn) {
    console.log('showModalDropdownOptions 호출됨:', rowId, fieldName, btn);
    
    // 드롭다운 옵션 가져오기
    fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName))
        .then(r => r.json())
        .then(function(data) {
            console.log('모달 드롭다운 옵션 로드됨:', data);
            if (!data.options) {
                alert('드롭다운 옵션을 불러올 수 없습니다.');
                return;
            }
            
            // 기존 드롭다운이 있으면 닫기 - 완전한 정리
            if (typeof closeDropdown === 'function') {
              closeDropdown();
            }
            
            // 추가적으로 남아있을 수 있는 모든 드롭다운 요소들 제거
            const existingDropdowns = document.querySelectorAll('.dropdown-edit');
            existingDropdowns.forEach(function(dropdown) {
              if (dropdown.parentNode) {
                dropdown.parentNode.removeChild(dropdown);
              }
            });
            
            // 현재 선택된 값 가져오기
            const currentValue = btn.textContent.trim();
            console.log('현재 선택된 값:', currentValue);
            
            // 드롭다운 메뉴 생성 - select 태그처럼 자연스럽게
            const dropdown = document.createElement('div');
            dropdown.className = 'dropdown-edit';
            dropdown.id = 'modal-dropdown-' + Date.now();
            
            // 버튼의 위치 정보 가져오기
            const rect = btn.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            
            // 버튼 바로 아래에 위치하도록 계산
            const topPosition = rect.bottom + scrollTop + 2;
            const leftPosition = rect.left + scrollLeft;
            
            // select 태그처럼 자연스러운 스타일 적용
            dropdown.setAttribute('style', `
              position: absolute !important;
              background: white !important;
              border: 1px solid #ccc !important;
              border-radius: 4px !important;
              box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
              z-index: 10000 !important;
              min-width: ${Math.max(rect.width, 300)}px !important;
              max-height: 200px !important;
              overflow-y: auto !important;
              display: block !important;
              visibility: visible !important;
              opacity: 1 !important;
              font-size: 14px !important;
              font-family: inherit !important;
              top: ${topPosition}px !important;
              left: ${leftPosition}px !important;
              padding: 4px 0 !important;
            `);
            
            console.log('모달 드롭다운 위치 설정:', {
              top: topPosition,
              left: leftPosition,
              buttonWidth: rect.width,
              buttonRect: rect
            });
            
            // 드롭다운 항목들 생성
            let html = '';
            data.options.forEach(function(option) {
                const label = option.option || option.name; // option 또는 name 필드 사용
                if (!label) return; // 값이 없으면 스킵
                const isSelected = label === currentValue;
                const backgroundColor = option.color ? hexToRgba(option.color, 0.18) : 'white';
                html += `
                  <div class="dropdown-item" data-option-id="${option.id}" data-option-text="${label}" data-color="${option.color||''}"
                       style="padding: 8px 12px; 
                              cursor: pointer; 
                              border-bottom: 1px solid #f0f0f0;
                              background: ${backgroundColor};
                              color: #333;
                              ${isSelected ? 'border-left: 3px solid #007bff; font-weight: bold;' : ''}
                              transition: background-color 0.2s;">
                    ${label}
                  </div>
                `;
            });
            
            dropdown.innerHTML = html;
            document.body.appendChild(dropdown);
            
            // 전역 dropdown 변수에 저장 (closeDropdown 함수에서 사용)
            window.dropdown = dropdown;
            
            console.log('모달 드롭다운 생성 완료:', {
              element: dropdown,
              parentNode: dropdown.parentNode,
              offsetWidth: dropdown.offsetWidth,
              offsetHeight: dropdown.offsetHeight,
              computedDisplay: window.getComputedStyle(dropdown).display,
              computedVisibility: window.getComputedStyle(dropdown).visibility,
              computedOpacity: window.getComputedStyle(dropdown).opacity,
              computedZIndex: window.getComputedStyle(dropdown).zIndex
            });
            
            // 호버 효과와 클릭 이벤트 바인딩
            dropdown.querySelectorAll('.dropdown-item[data-option-id]').forEach(function(item) {
                // 기존 이벤트 리스너 제거 (중복 방지)
                const newItem = item.cloneNode(true);
                item.parentNode.replaceChild(newItem, item);
                
                // 호버 효과
                newItem.addEventListener('mouseenter', function() {
                    if (!this.style.borderLeft.includes('#007bff')) {
                        const color = this.getAttribute('data-color');
                        if (color && color !== 'null' && color !== 'undefined') {
                            this.style.background = hexToRgba(color, 0.3);
                        } else {
                            this.style.background = '#f8f9fa';
                        }
                    }
                });
                // mouseleave → mouseout
                newItem.addEventListener('mouseout', function() {
                    if (!this.style.borderLeft.includes('#007bff')) {
                        const color = this.getAttribute('data-color');
                        if (color && color !== 'null' && color !== 'undefined') {
                            this.style.background = hexToRgba(color, 0.18);
                        } else {
                            this.style.background = '#f8f9fa';
                        }
                    }
                });
                
                // 클릭 이벤트
                newItem.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // 이미 처리 중인지 확인
                    if (this.dataset.processing === 'true') {
                        console.log('이미 처리 중인 옵션 클릭 무시');
                        return;
                    }
                    
                    // 처리 중 상태로 설정
                    this.dataset.processing = 'true';
                    
                    const selectedOptionId = this.getAttribute('data-option-id');
                    const selectedOptionText = this.getAttribute('data-option-text');
                    const selectedColor = this.getAttribute('data-color');
                    
                    // 드롭다운 닫기
                    if (dropdown && dropdown.parentNode) {
                        dropdown.parentNode.removeChild(dropdown);
                        window.dropdown = null;
                    }
                    
                    // 버튼 배경색 변경
                    btn.textContent = selectedOptionText;
                    btn.style.background = selectedColor ? hexToRgba(selectedColor, 0.18) : '#f8f9fa';
                    btn.style.color = '#333';
                    
                    // 드롭다운 옵션 선택 처리
                    selectModalDropdownOption(rowId, fieldName, selectedOptionId, selectedOptionText, btn, selectedColor);
                    
                    // 처리 완료 후 상태 제거 (약간의 지연 후)
                    setTimeout(() => {
                        this.dataset.processing = 'false';
                    }, 1000);
                });
            });
            
            // 드롭다운 외부 클릭 시 닫기
            addGlobalClickHandler(dropdown, btn);
        })
        .catch(function(error) {
            console.error('모달 드롭다운 옵션 로드 실패:', error);
            alert('드롭다운 옵션을 불러오는데 실패했습니다: ' + error.message);
        });
  }
  
  // 모달용 드롭다운 옵션 선택 함수
  function selectModalDropdownOption(rowId, fieldName, optionId, optionText, btn, color) {
    console.log('selectModalDropdownOption 호출됨:', rowId, fieldName, optionId, optionText);
    
    // 중복 요청 방지를 위한 디바운싱
    const requestKey = `${rowId}_${fieldName}_${optionId}`;
    if (window.pendingRequests && window.pendingRequests[requestKey]) {
      console.log('중복 요청 방지:', requestKey);
      return;
    }
    
    // 요청 상태 추적
    if (!window.pendingRequests) {
      window.pendingRequests = {};
    }
    window.pendingRequests[requestKey] = true;
    
    // 버튼 텍스트 즉시 업데이트
    btn.textContent = optionText;
    btn.style.background = color ? hexToRgba(color, 0.18) : '#f8f9fa';
    btn.style.color = '#333';
    
    // 업종이 선택되면 빨간 테두리 제거
    if (fieldName === '업종') {
      highlightRequiredField(btn, false);
    }
    
    // 서버에 업데이트 요청
    fetch('/sales/update_row_field/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            row_id: rowId,
            field_name: fieldName,
            value: optionId
        })
    })
    .then(response => response.json())
    .then(data => {
        // 요청 완료 후 상태 제거
        delete window.pendingRequests[requestKey];
        
        if (data.success) {
            console.log('모달 드롭다운 업데이트 성공:', fieldName, optionId);
            
            // 종속된 행들 찾아서 업데이트
            if (typeof updateDependentRows === 'function') {
                updateDependentRows(rowId, fieldName, optionId);
            }
            
            // 실시간 동기화
            if (typeof syncTableAndKanban === 'function') {
                syncTableAndKanban(fieldName);
            }
            
            // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우
            if (window.currentStatusTab !== null && fieldName === window.statusAttributeName) {
                // 해당 행의 상태 셀 업데이트
                const row = document.querySelector(`tr[data-id="${rowId}"]`);
                if (row) {
                    const statusCell = row.querySelector(`td[data-field="${fieldName}"]`);
                    if (statusCell) {
                        // 새로운 값으로 data-value 업데이트
                        statusCell.setAttribute('data-value', optionId);
                        
                        // 상태 필터 즉시 재적용
                        setTimeout(() => {
                            if (typeof applyStatusFilter === 'function') {
                                applyStatusFilter();
                            }
                        }, 50);
                    }
                }
            }
        } else {
            throw new Error(data.error || '업데이트 실패');
        }
    })
    .catch(error => {
        // 요청 실패 시에도 상태 제거
        delete window.pendingRequests[requestKey];
        
        console.error('모달 드롭다운 업데이트 요청 오류:', error);
        showNotification('업데이트 중 오류가 발생했습니다.', 'error');
        // 실패 시 버튼 텍스트 복원
        btn.textContent = btn.textContent; // 이전 값으로 복원 (실제로는 서버에서 가져와야 함)
    });
  }
  
  // 모달용 지역 드롭다운 표시 함수
  function showModalRegionDropdown(rowId, fieldName, btn) {
    console.log('showModalRegionDropdown 호출됨:', rowId, fieldName, btn);
    
    const regionNames = ['서울','경기','인천', '경북', '경남', '대구','부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
    
    // 기존 모든 드롭다운 닫기
    closeAllDropdowns();
    
    // 추가적으로 남아있을 수 있는 모든 드롭다운 요소들 제거
    const existingDropdowns = document.querySelectorAll('.dropdown-edit');
    existingDropdowns.forEach(function(dropdown) {
      if (dropdown.parentNode) {
        dropdown.parentNode.removeChild(dropdown);
      }
    });
    
    // 현재 선택된 지역 값 가져오기
    const currentRegion = btn.previousElementSibling ? btn.previousElementSibling.textContent.trim() : '';
    console.log('현재 선택된 지역:', currentRegion);
    
    // 드롭다운 메뉴 생성 - select 태그처럼 자연스럽게
    const dropdown = document.createElement('div');
    dropdown.className = 'dropdown-edit';
    dropdown.id = 'modal-region-dropdown-' + Date.now();
    
    // 버튼의 위치 정보 가져오기
    const rect = btn.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    
    // 버튼 바로 아래에 위치하도록 계산
    const topPosition = rect.bottom + scrollTop + 2;
    const leftPosition = rect.left + scrollLeft;
    
    // select 태그처럼 자연스러운 스타일 적용
    dropdown.setAttribute('style', `
      position: absolute !important;
      background: white !important;
      border: 1px solid #ccc !important;
      border-radius: 4px !important;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
      z-index: 10000 !important;
      min-width: ${Math.max(rect.width, 300)}px !important;
      max-height: 200px !important;
      overflow-y: auto !important;
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      font-size: 14px !important;
      font-family: inherit !important;
      top: ${topPosition}px !important;
      left: ${leftPosition}px !important;
      padding: 4px 0 !important;
    `);
    
    console.log('모달 드롭다운 위치 설정:', {
      top: topPosition,
      left: leftPosition,
      buttonWidth: rect.width,
      buttonRect: rect
    });
    
    // 드롭다운 항목들 생성
    let html = '';
    regionNames.forEach(function(region) {
        const isSelected = region === currentRegion;
        html += `
          <div class="dropdown-item" data-region="${region}" 
               style="padding: 8px 12px !important; 
                      cursor: pointer !important; 
                      border-bottom: 1px solid #f0f0f0 !important;
                      ${isSelected ? 'background: #007bff !important; color: white !important;' : 'background: white !important; color: #333 !important;'}
                      transition: background-color 0.2s !important;">
            ${region}
          </div>
        `;
    });
    
    dropdown.innerHTML = html;
    document.body.appendChild(dropdown);
    
    // 전역 dropdown 변수에 저장 (closeDropdown 함수에서 사용)
    window.dropdown = dropdown;
    
    console.log('모달 지역 드롭다운 생성 완료:', {
      element: dropdown,
      parentNode: dropdown.parentNode,
      offsetWidth: dropdown.offsetWidth,
      offsetHeight: dropdown.offsetHeight,
      computedDisplay: window.getComputedStyle(dropdown).display,
      computedVisibility: window.getComputedStyle(dropdown).visibility,
      computedOpacity: window.getComputedStyle(dropdown).opacity,
      computedZIndex: window.getComputedStyle(dropdown).zIndex
    });
    
    // 호버 효과와 클릭 이벤트 바인딩
    dropdown.querySelectorAll('.dropdown-item[data-region]').forEach(function(item) {
        // 호버 효과
        item.addEventListener('mouseenter', function() {
            if (!this.style.background.includes('#007bff')) {
                this.style.background = '#f8f9fa !important';
            }
        });
        
        item.addEventListener('mouseleave', function() {
            if (!this.style.background.includes('#007bff')) {
                this.style.background = 'white !important';
            }
        });
        
        // 클릭 이벤트
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const selectedRegion = this.getAttribute('data-region');
            console.log('모달에서 지역 선택됨:', selectedRegion);
            
            // 드롭다운 제거
            if (dropdown && dropdown.parentNode) {
                dropdown.parentNode.removeChild(dropdown);
                window.dropdown = null;
            }
            
            // 지역 선택 처리
            selectModalRegionOption(rowId, selectedRegion, this);
        });
    });
    
    // 드롭다운 외부 클릭 시 닫기
    addGlobalClickHandler(dropdown, btn);
  }
  
  // 상세 모달용 드롭다운 오픈 함수
  function openDetailDropdown(rowId, fieldName, btn) {
    console.log('openDetailDropdown 호출됨:', rowId, fieldName, btn);
    
    // 지역과 상세지역은 특별 처리
    if (fieldName === '지역') {
        console.log('지역 드롭다운 호출');
        showModalRegionDropdown(rowId, fieldName, btn);
        return;
    } else if (fieldName === '상세지역') {
        console.log('상세지역 드롭다운 호출');
        showModalSubregionDropdown(rowId, fieldName, btn);
        return;
    }
    
    console.log('일반 드롭다운 처리');
    // 일반 드롭다운 속성 처리
    fetch('/sales/get_user_attributes/')
        .then(r => r.json())
        .then(function(attributesData) {
            if (!attributesData.success) {
                alert('속성 정보를 불러올 수 없습니다.');
                return;
            }
            
            const attr = attributesData.attributes.find(a => a.name === fieldName);
            if (!attr) {
                alert('해당 속성을 찾을 수 없습니다.');
                return;
            }
            
            if (attr.type === 'dropdown') {
                // 드롭다운 옵션들을 가져와서 표시
                showModalDropdownOptions(rowId, fieldName, btn);
            } else {
                alert('드롭다운 타입이 아닙니다.');
            }
        });
  }
  
  // 모달용 상세지역 드롭다운 표시 함수
  function showModalSubregionDropdown(rowId, fieldName, btn) {
    console.log('showModalSubregionDropdown 호출됨:', rowId, fieldName, btn);
    
    // 서버에서 현재 지역 가져오기
    fetch(`/sales/get_row_details/${rowId}/`)
      .then(response => response.json())
      .then(data => {
        console.log('서버 응답 데이터:', data);
        
        // 현재 지역과 상세지역 정보 추출
        let currentRegion = '';
        let currentSubregion = '';
        
        if (data.success && data.row_data) {
          currentRegion = data.row_data['지역'] || '';
          currentSubregion = data.row_data['상세지역'] || '';
        } else if (data.region) {
          currentRegion = data.region;
          currentSubregion = data.region_detail || '';
        }
        
        console.log('현재 지역:', currentRegion, '현재 상세지역:', currentSubregion);
        
        // 지역이 없으면 경고
        if (!currentRegion) {
          alert('먼저 지역을 선택해주세요.');
          return;
        }
        
        // 기존 드롭다운이 있으면 닫기 - 완전한 정리
        if (typeof closeDropdown === 'function') {
          closeDropdown();
        }
        
        // 추가적으로 남아있을 수 있는 모든 드롭다운 요소들 제거
        const existingDropdowns = document.querySelectorAll('.dropdown-edit');
        existingDropdowns.forEach(function(dropdown) {
          if (dropdown.parentNode) {
            dropdown.parentNode.removeChild(dropdown);
          }
        });
        
        // 상세지역 목록 가져오기
        const subregions = getSubregions(currentRegion);
        console.log('상세지역 목록:', subregions);
        
        if (!subregions || subregions.length === 0) {
          alert(`${currentRegion}에 대한 상세지역 정보가 없습니다.`);
          return;
        }
        
        // 드롭다운 메뉴 생성 - select 태그처럼 자연스럽게
        const dropdown = document.createElement('div');
        dropdown.className = 'dropdown-edit';
        dropdown.id = 'modal-subregion-dropdown-' + Date.now();
        
        // 버튼의 위치 정보 가져오기
        const rect = btn.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        // 버튼 바로 아래에 위치하도록 계산
        const topPosition = rect.bottom + scrollTop + 2;
        const leftPosition = rect.left + scrollLeft;
        
        // select 태그처럼 자연스러운 스타일 적용
        dropdown.setAttribute('style', `
          position: absolute !important;
          background: white !important;
          border: 1px solid #ccc !important;
          border-radius: 4px !important;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
          z-index: 10000 !important;
          min-width: ${Math.max(rect.width, 300)}px !important;
          max-height: 200px !important;
          overflow-y: auto !important;
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          font-size: 14px !important;
          font-family: inherit !important;
          top: ${topPosition}px !important;
          left: ${leftPosition}px !important;
          padding: 4px 0 !important;
        `);
        
        console.log('모달 상세지역 드롭다운 위치 설정:', {
          top: topPosition,
          left: leftPosition,
          buttonWidth: rect.width,
          buttonRect: rect
        });
        
        // 드롭다운 항목들 생성
        let html = '';
        subregions.forEach(function(subregion) {
            const isSelected = subregion === currentSubregion;
            html += `
              <div class="dropdown-item" data-subregion="${subregion}" 
                   style="padding: 8px 12px !important; 
                          cursor: pointer !important; 
                          border-bottom: 1px solid #f0f0f0 !important;
                          ${isSelected ? 'background: #007bff !important; color: white !important;' : 'background: white !important; color: #333 !important;'}
                          transition: background-color 0.2s !important;">
                ${subregion}
              </div>
            `;
        });
        
        dropdown.innerHTML = html;
        document.body.appendChild(dropdown);
        
        // 전역 dropdown 변수에 저장 (closeDropdown 함수에서 사용)
        window.dropdown = dropdown;
        
        console.log('모달 상세지역 드롭다운 생성 완료:', {
          element: dropdown,
          parentNode: dropdown.parentNode,
          offsetWidth: dropdown.offsetWidth,
          offsetHeight: dropdown.offsetHeight,
          computedDisplay: window.getComputedStyle(dropdown).display,
          computedVisibility: window.getComputedStyle(dropdown).visibility,
          computedOpacity: window.getComputedStyle(dropdown).opacity,
          computedZIndex: window.getComputedStyle(dropdown).zIndex
        });
        
        // 호버 효과와 클릭 이벤트 바인딩
        dropdown.querySelectorAll('.dropdown-item[data-subregion]').forEach(function(item) {
            // 호버 효과
            item.addEventListener('mouseenter', function() {
                if (!this.style.background.includes('#007bff')) {
                    this.style.background = '#f8f9fa !important';
                }
            });
            
            item.addEventListener('mouseleave', function() {
                if (!this.style.background.includes('#007bff')) {
                    this.style.background = 'white !important';
                }
            });
            
            // 클릭 이벤트
            item.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const selectedSubregion = this.getAttribute('data-subregion');
                console.log('모달에서 상세지역 선택됨:', selectedSubregion);
                
                // 드롭다운 제거
                if (dropdown && dropdown.parentNode) {
                    dropdown.parentNode.removeChild(dropdown);
                    window.dropdown = null;
                }
                
                // 상세지역 선택 처리
                selectModalSubregionOption(rowId, selectedSubregion, this);
            });
        });
        
        // 드롭다운 외부 클릭 시 닫기
        addGlobalClickHandler(dropdown, btn);
      })
      .catch(error => {
        console.error('상세지역 드롭다운 로딩 오류:', error);
        alert('상세지역 정보를 불러오는 중 오류가 발생했습니다.');
      });
  }
  
  // 드롭다운 셀 값 변경 후 항상 칸반보드 새로고침 (최적화: debounce)
  function triggerKanbanRefreshIfNeeded() {
      let currentAttr = document.getElementById('kanbanAttributeSelect')?.value;
      if (!currentAttr) {
          currentAttr = window.kanbanSettings?.main_attr;
      }
      if (!currentAttr || currentAttr === 'undefined') return;
      if (!window._kanbanRefreshTimeout) {
          window._kanbanRefreshTimeout = null;
      }
      if (window._kanbanRefreshTimeout) {
          clearTimeout(window._kanbanRefreshTimeout);
      }
      window._kanbanRefreshTimeout = setTimeout(() => {
          window._kanbanRefreshTimeout = null;
          if (!window._kanbanRefreshing) {
              window._kanbanRefreshing = true;
              refreshKanban();
              setTimeout(() => { window._kanbanRefreshing = false; }, 500);
          }
      }, 80);
  }
  
  // 드롭다운 옵션을 렌더링하는 공통 함수
  function renderDropdownOptions(options, type, td, currentDropdown) {
    if (!currentDropdown) {
        console.error('currentDropdown이 null입니다. 드롭다운 처리를 중단합니다.');
        return;
    }
    
    const currentValue = td.getAttribute('data-value') || '';
    const id = td.parentElement.getAttribute('data-id');
    
    // 모달과 동일한 깔끔한 구조로 변경
    let html = `<div style="padding: 8px; border-bottom: 1px solid #eee;"><b>${type} 선택</b></div>`;
    
    // 옵션 목록 컨테이너
    html += '<div style="max-height: 150px; overflow-y: auto;">';
    
    options.forEach(function(opt) {
        // 단일선택 값 처리
        let isSelected = false;
        if (currentValue) {
            try {
                const parsed = JSON.parse(currentValue);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    isSelected = Number(opt.id) === Number(parsed[0]);
                } else {
                    isSelected = Number(opt.id) === Number(parsed);
                }
            } catch (e) {
                isSelected = Number(opt.id) === Number(currentValue);
            }
        }
        const backgroundColor = opt.color ? hexToRgba(opt.color, 0.18) : 'white';
        html += `
          <div class="dropdown-option-container" style="padding: 6px 10px; border-bottom: 1px solid #f0f0f0;">
            <div class="dropdown-item" data-option-id="${opt.id}" 
                 style="cursor: pointer; 
                        background: ${backgroundColor}; 
                        border-radius: 4px; 
                        padding: 6px 8px; 
                        margin-bottom: 4px;
                        ${isSelected ? 'border: 2px solid #007bff; font-weight: bold;' : 'border: 1px solid #ddd;'}
                        transition: all 0.2s;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        position: relative;">
              <div style="display: flex; align-items: center; flex: 1; min-width: 0;">
                <span style="flex: 1; word-wrap: break-word; word-break: break-all; color: #333; font-size: 14px; line-height: 1.4; padding: 2px 0;">${opt.option}</span>
              </div>
              ${type !== 'region' && type !== 'region_detail' ? `
              <div class="option-controls" style="display: flex; gap: 4px; align-items: center; margin-left: 8px;">
                <input type="color" value="${opt.color||'#eeeeee'}" data-color-edit="${opt.id}" 
                       style="padding: 0; width: 20px; height: 20px; border: none; cursor: pointer; border-radius: 2px; background: transparent; position: relative;" title="색상 변경">
                <button data-edit="${opt.id}" 
                        style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px; color: #666; transition: color 0.2s;" 
                        title="수정"
                        onmouseover="this.style.color='#007bff'"
                        onmouseout="this.style.color='#666'">✏️</button>
                <button data-del="${opt.id}" 
                        style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px; color: #666; transition: color 0.2s;" 
                        title="삭제"
                        onmouseover="this.style.color='#dc3545'"
                        onmouseout="this.style.color='#666'">🗑️</button>
              </div>
              ` : ''}
            </div>
          </div>
        `;
    });
    
    // "선택 없음" 옵션 추가 (지역/상세지역이 아닌 경우에만)
    if (type !== 'region' && type !== 'region_detail') {
        html += `
          <div class="dropdown-option-container" style="padding: 6px 10px; border-bottom: 1px solid #f0f0f0;">
            <div class="dropdown-item" data-option-id="none" 
                 style="cursor: pointer; 
                        background: #f8f9fa; 
                        border-radius: 4px; 
                        padding: 6px 8px; 
                        margin-bottom: 4px;
                        border: 1px solid #ddd;
                        transition: all 0.2s;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        position: relative;">
              <div style="display: flex; align-items: center; flex: 1; min-width: 0;">
                <span style="flex: 1; word-wrap: break-word; word-break: break-all; color: #999; font-style: italic; font-size: 14px; line-height: 1.4; padding: 2px 0;">선택 없음</span>
              </div>
            </div>
          </div>
        `;
    }
    
    html += '</div>';
    
    // 새 옵션 추가 영역 (지역/상세지역이 아닌 경우에만)
    if (type !== 'region' && type !== 'region_detail') {
        html += `<div style="border-top: 1px solid #eee; padding: 8px; background: #f8f9fa;">
          <div style="display: flex; gap: 4px; align-items: center;">
            <input type="text" placeholder="새 옵션 추가" 
                   style="flex: 1; padding: 4px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
            <button class="add-btn" 
                    style="padding: 4px 12px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px; transition: background-color 0.2s;"
                    onmouseover="this.style.background='#0056b3'"
                    onmouseout="this.style.background='#007bff'">추가</button>
          </div>
        </div>`;
    }
    
    currentDropdown.innerHTML = html;
    document.body.appendChild(currentDropdown);
    
    // === 드롭다운 모달 이벤트 바인딩 추가 ===
    if (type !== 'region' && type !== 'region_detail') {
        bindDropdownModalEvents(currentDropdown, type, options);
    }
    
    // 단일선택: 옵션 클릭 시 바로 선택
    currentDropdown.querySelectorAll('.dropdown-item[data-option-id]').forEach(function(item) {
        item.addEventListener('click', function(e) {
            e.stopPropagation();
            const optionId = this.getAttribute('data-option-id');
            
            // "선택 없음" 옵션 처리
            if (optionId === 'none') {
                // UI 업데이트
                if (td) { td.innerHTML = `<div class="dropdown-pill" style="background:#eee; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">선택 없음</div>`; td.setAttribute('data-value', ''); }
                
                // 서버에서 해당 속성 값 삭제
                if (id && id.startsWith('temp_')) {
                    // 새 행인 경우 로컬에서만 처리
                    console.log('새 행에서 선택 없음 처리');
                } else {
                    // 기존 행인 경우 서버에서 삭제
                    fetch('/sales/delete_attribute_value/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id='+id+'&field='+encodeURIComponent(type)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('속성 값 삭제 성공');
                            
                            // 커스텀 이벤트 발생으로 실시간 업데이트 보장
                            const rowId = td.parentElement.getAttribute('data-id');
                            document.dispatchEvent(new CustomEvent('dropdownOptionChanged', {
                                detail: {
                                    fieldName: type,
                                    newValue: '',
                                    rowId: rowId
                                }
                            }));
                            
                            // 종속된 행들 찾아서 업데이트
                            if (typeof updateDependentRows === 'function') {
                                updateDependentRows(id, type, '');
                            }
                            
                            syncTableAndKanban(type);
                        } else {
                            throw new Error(data.error || '삭제 실패');
                        }
                    })
                    .catch(error => {
                        console.error('속성 값 삭제 실패:', error);
                        alert('삭제 중 오류가 발생했습니다: ' + error.message);
                    });
                }
                
                // 드롭다운 닫기
                closeAllDropdowns();
                return;
            }
            
            const option = options.find(o => String(o.id) === String(optionId));
            // UI 업데이트 - 즉시 실행
            if (option) {
                const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                if (td) { 
                    td.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`; 
                    td.setAttribute('data-value', optionId); 
                }
                
                // 커스텀 이벤트 발생으로 실시간 업데이트 보장
                const rowId = td.parentElement.getAttribute('data-id');
                document.dispatchEvent(new CustomEvent('dropdownOptionChanged', {
                    detail: {
                        fieldName: type,
                        newValue: optionId,
                        rowId: rowId
                    }
                }));
            } else {
                // 옵션을 찾지 못한 경우에도 pill 형태로 표시
                console.log(`옵션을 찾지 못함, pill 형태로 표시: ${optionId}`);
                if (td) { 
                    td.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${optionId}</div>`; 
                    td.setAttribute('data-value', optionId); 
                }
                
                // 커스텀 이벤트 발생
                const rowId = td.parentElement.getAttribute('data-id');
                document.dispatchEvent(new CustomEvent('dropdownOptionChanged', {
                    detail: {
                        fieldName: type,
                        newValue: optionId,
                        rowId: rowId
                    }
                }));
            }
            
            // 드롭다운 닫기 - 즉시 실행
            closeAllDropdowns();
            
            // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우
            if (window.currentStatusTab !== null && type === window.statusAttributeName) {
                // 해당 행의 상태 셀 업데이트
                const row = document.querySelector(`tr[data-id="${id}"]`);
                if (row) {
                    const statusCell = row.querySelector(`td[data-field="${type}"]`);
                    if (statusCell) {
                        // 새로운 값으로 data-value 업데이트
                        statusCell.setAttribute('data-value', optionId);
                        
                        // 상태 필터 즉시 재적용
                        setTimeout(() => {
                            if (typeof applyStatusFilter === 'function') {
                                applyStatusFilter();
                            }
                        }, 50);
                    }
                }
            }
            
            // 서버 업데이트 - 단일 값으로 저장
            if (id && id.startsWith('temp_')) {
                saveNewRowField(td.parentElement, type, optionId);
            } else {
                fetch('/sales/update_row_field/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(optionId)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 종속된 행들 찾아서 업데이트 (ID 전달)
                        if (typeof updateDependentRows === 'function') {
                            updateDependentRows(id, type, optionId);
                        }
                        
                        // 실시간 동기화
                        if (typeof syncTableAndKanban === 'function') {
                            syncTableAndKanban(type);
                        }
                        // 칸반보드 리렌더링
                        if (window.currentKanbanAttribute && window.currentKanbanAttribute === type) {
                            updateKanbanBoard(type);
                        }
                        // 상태 속성인 경우 상태 탭 새로고침
                        if (window.statusAttributeName && type === window.statusAttributeName && typeof refreshStatusTabs === 'function') {
                            setTimeout(() => { refreshStatusTabs(); }, 100);
                        }
                    } else {
                        throw new Error(data.error || '업데이트 실패');
                    }
                })
                .catch(error => {
                    console.error('드롭다운 옵션 업데이트 실패:', error);
                    alert('업데이트 중 오류가 발생했습니다: ' + error.message);
                });
            }
        });
    });
    
    // 전역 클릭 핸들러 추가 (이미 openDropdown에서 추가되었지만 중복 방지)
    if (!globalClickHandler) {
        addGlobalClickHandler(currentDropdown, td);
    }
    
    // 스크롤 이벤트 리스너 추가
    const scrollHandler = function() {
        if (currentDropdown && td) {
            const rect = td.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            
            const topPosition = rect.bottom + scrollTop + 2;
            const leftPosition = rect.left + scrollLeft;
            
            currentDropdown.style.top = topPosition + 'px';
            currentDropdown.style.left = leftPosition + 'px';
        }
    };
    
    document.addEventListener('scroll', scrollHandler);
    window.addEventListener('resize', scrollHandler);
}
