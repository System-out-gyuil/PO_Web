// 통합된 드롭다운 관리 시스템

// 전역 변수로 현재 열린 드롭다운 추적
let currentOpenDropdown = null;
let currentTriggerElement = null;

// 중복 요청 방지를 위한 전역 변수
let pendingRequests = new Map();
let requestTimeout = 5000; // 5초로 증가
let isProcessingRequest = false; // 전역 처리 상태 플래그

function closeAllDropdowns() {
    console.log('모든 드롭다운 닫기 실행');
    console.trace('closeAllDropdowns 호출 스택');
    
    // 지역/상세지역 드롭다운 보호 로직
    const regionDropdowns = document.querySelectorAll('.dropdown-edit[data-region-type]');
    if (regionDropdowns.length > 0) {
        console.log('지역/상세지역 드롭다운이 열려있음, 보호 모드로 닫기');
        console.log('현재 열린 지역 드롭다운들:', regionDropdowns);
        // 지역 드롭다운은 즉시 닫지 않고 약간의 지연 후 닫기
        setTimeout(() => {
            console.log('지연 후 지역 드롭다운 닫기 실행');
            // 전역 dropdown 변수 정리
            if (window.dropdown && window.dropdown.parentNode) {
                console.log('window.dropdown 제거');
                window.dropdown.parentNode.removeChild(window.dropdown);
                window.dropdown = null;
            }
            
            // 모든 드롭다운 요소들 제거
            document.querySelectorAll('.dropdown-edit').forEach(el => {
                if (el.parentNode) {
                    console.log('드롭다운 요소 제거:', el);
                    el.parentNode.removeChild(el);
                }
            });
            
            // 모든 모달 드롭다운 제거
            document.querySelectorAll('[id^="modal-"]').forEach(el => {
                if (el.parentNode) {
                    console.log('모달 드롭다운 제거:', el);
                    el.parentNode.removeChild(el);
                }
            });
            
            // 전역 변수 초기화
            currentOpenDropdown = null;
            currentTriggerElement = null;
            
            // 전역 클릭 핸들러 제거
            removeGlobalClickHandler();
        }, 100);
        return;
    }
    
    // 전역 dropdown 변수 정리
    if (window.dropdown && window.dropdown.parentNode) {
        console.log('window.dropdown 제거 (일반 모드)');
        window.dropdown.parentNode.removeChild(window.dropdown);
        window.dropdown = null;
    }
    
    // 모든 드롭다운 요소들 제거
    document.querySelectorAll('.dropdown-edit').forEach(el => {
        if (el.parentNode) {
            console.log('드롭다운 요소 제거 (일반 모드):', el);
            el.parentNode.removeChild(el);
        }
    });
    
    // 모든 모달 드롭다운 제거
    document.querySelectorAll('[id^="modal-"]').forEach(el => {
        if (el.parentNode) {
            console.log('모달 드롭다운 제거 (일반 모드):', el);
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
        // 지역/상세지역 드롭다운인 경우 특별한 보호 로직 적용
        const isRegionDropdown = dropdown && dropdown.getAttribute('data-region-type');
        
        console.log('전역 클릭 핸들러 실행:', {
            target: e.target,
            isRegionDropdown: isRegionDropdown,
            dropdown: dropdown,
            triggerElement: triggerElement,
            dropdownContainsTarget: dropdown && dropdown.contains(e.target),
            triggerContainsTarget: triggerElement && triggerElement.contains(e.target)
        });
        
        // 드롭다운이나 트리거 요소 내부 클릭이 아닌 경우에만 닫기
        if (dropdown && !dropdown.contains(e.target) && 
            (!triggerElement || !triggerElement.contains(e.target))) {
            
            // 지역/상세지역 드롭다운인 경우 약간의 지연 후 닫기
            if (isRegionDropdown) {
                console.log('지역 드롭다운 외부 클릭 감지, 지연 후 닫기');
                console.log('클릭된 요소:', e.target);
                console.log('드롭다운 요소:', dropdown);
                console.log('트리거 요소:', triggerElement);
                
                // 지역 드롭다운의 경우 더 긴 지연 시간 적용
                setTimeout(() => {
                    console.log('지연 후 지역 드롭다운 닫기 실행');
                    closeAllDropdowns();
                }, 500);
            } else {
                console.log('외부 클릭으로 드롭다운 닫기');
                closeAllDropdowns();
            }
        } else {
            console.log('드롭다운 내부 클릭이므로 닫지 않음');
        }
    };
    
    // 지역/상세지역 드롭다운인 경우 더 긴 지연 시간 적용
    const delay = dropdown && dropdown.getAttribute('data-region-type') ? 500 : 100; // 300ms에서 500ms로 증가
    
    console.log('전역 클릭 핸들러 등록:', {delay, isRegionDropdown: dropdown && dropdown.getAttribute('data-region-type')});
    
    setTimeout(() => {
        document.addEventListener('mousedown', globalClickHandler);
    }, delay);
}

function openDropdown(td, type, id, currentId, currentSubregion) {
    console.log('openDropdown 호출됨:', {td, type, id, currentId, currentSubregion});
    
    // 이미 같은 셀에서 드롭다운이 열려있는지 확인
    if (currentOpenDropdown && currentTriggerElement === td) {
        console.log('같은 셀에서 이미 드롭다운이 열려있음, 닫기만 실행');
        closeAllDropdowns();
        return;
    }
    
    // 기존 드롭다운이 열려있고 다른 셀에서 클릭한 경우, 기존 드롭다운을 먼저 닫고 새 드롭다운 생성
    if (currentOpenDropdown && currentTriggerElement !== td) {
        console.log('다른 셀에서 드롭다운 클릭, 기존 드롭다운 닫고 새 드롭다운 생성');
        // 기존 드롭다운을 즉시 닫기
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
        
        // 약간의 지연 후 새 드롭다운 생성 (기존 드롭다운이 완전히 제거된 후)
        setTimeout(() => {
            createNewDropdown(td, type, id, currentId, currentSubregion);
        }, 50);
        return;
    }
    
    // 기존 모든 드롭다운 닫기 (첫 번째 드롭다운 생성 시)
    closeAllDropdowns();
    
    // 새 드롭다운 생성
    createNewDropdown(td, type, id, currentId, currentSubregion);
}

// 새 드롭다운 생성 함수
function createNewDropdown(td, type, id, currentId, currentSubregion) {
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
        
        // 드롭다운이 성공적으로 추가되었는지 확인
        console.log('지역 드롭다운 DOM에 추가됨:', currentDropdown);
        
        // MutationObserver를 사용하여 드롭다운 제거 감지
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.removedNodes.forEach((node) => {
                        if (node === currentDropdown) {
                            console.error('지역 드롭다운이 MutationObserver에 의해 제거됨:', {
                                mutation: mutation,
                                target: mutation.target,
                                addedNodes: mutation.addedNodes,
                                removedNodes: mutation.removedNodes
                            });
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // 지역 선택 이벤트 리스너
        currentDropdown.querySelectorAll('.dropdown-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                const selectedRegion = this.getAttribute('data-option-id');
                
                // 중복 요청 방지
                const requestKey = `${id}_지역_${selectedRegion}`;
                if (pendingRequests.has(requestKey)) {
                    console.log('지역 중복 요청 방지:', requestKey);
                    return;
                }
                
                // 요청 상태 설정
                pendingRequests.set(requestKey, Date.now());
                
                // 타임아웃 설정
                setTimeout(() => {
                    pendingRequests.delete(requestKey);
                }, requestTimeout);
                
                // UI 업데이트
                if (td) { 
                    td.innerHTML = selectedRegion; 
                    td.setAttribute('data-value', selectedRegion); 
                }
                
                // 서버 업데이트
                if (id && id.startsWith('temp_')) {
                    saveNewRowField(td.parentElement, '지역', selectedRegion);
                } else {
                    console.log('update_row_field_modal3');
                    fetch('/sales/update_row_field/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id='+id+'&field=지역&value='+encodeURIComponent(selectedRegion)
                    })
                    .then(response => response.json())
                    .then(data => {
                        pendingRequests.delete(requestKey);
                        isProcessingRequest = false;
                        if (data.success) {
                            console.log('지역 업데이트 성공');
                            // 종속된 행들 찾아서 업데이트
                            if (typeof updateDependentRows === 'function') {
                                updateDependentRows(id, '지역', selectedRegion);
                            }
                            // 실시간 동기화
                            if (typeof syncTableAndKanban === 'function') {
                                syncTableAndKanban('지역');
                            } else {
                                // syncTableAndKanban이 없는 경우 triggerKanbanRefreshIfNeeded 사용
                                if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                                    triggerKanbanRefreshIfNeeded();
                                }
                            }
                        } else {
                            throw new Error(data.error || '업데이트 실패');
                        }
                    })
                    .catch(error => {
                        pendingRequests.delete(requestKey);
                        isProcessingRequest = false;
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
        
        // getSubregions 함수가 정의되지 않은 경우를 대비한 임시 함수
        if (typeof getSubregions === 'undefined') {
            window.getSubregions = function(region) {
                console.log('getSubregions 함수가 정의되지 않음, 기본값 반환');
                const defaultSubregions = {
                    '서울': ['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'],
                    '경기': ['수원시', '성남시', '의정부시', '안양시', '부천시', '광명시', '평택시', '동두천시', '안산시', '고양시', '과천시', '구리시', '남양주시', '오산시', '시흥시', '군포시', '의왕시', '하남시', '용인시', '파주시', '이천시', '안성시', '김포시', '화성시', '광주시', '여주시', '양평군', '고양군', '연천군', '가평군', '포천군'],
                    '인천': ['중구', '동구', '미추홀구', '연수구', '남동구', '부평구', '계양구', '서구', '강화군', '옹진군'],
                    '대구': ['중구', '동구', '서구', '남구', '북구', '수성구', '달서구', '달성군'],
                    '경북': ['포항시', '경주시', '김천시', '안동시', '구미시', '영주시', '영천시', '상주시', '문경시', '경산시', '군위군', '의성군', '청송군', '영양군', '영덕군', '청도군', '고령군', '성주군', '칠곡군', '예천군', '봉화군', '울진군', '울릉군'],
                    '경남': ['창원시', '진주시', '통영시', '사천시', '김해시', '밀양시', '거제시', '양산시', '의령군', '함안군', '창녕군', '고성군', '남해군', '하동군', '산청군', '함양군', '거창군', '합천군'],
                    '부산': ['중구', '서구', '동구', '영도구', '부산진구', '동래구', '남구', '북구', '해운대구', '사하구', '금정구', '강서구', '연제구', '수영구', '사상구', '기장군'],
                    '광주': ['동구', '서구', '남구', '북구', '광산구'],
                    '대전': ['동구', '중구', '서구', '유성구', '대덕구'],
                    '울산': ['중구', '남구', '동구', '북구', '울주군'],
                    '세종': ['세종특별자치시'],
                    '강원': ['춘천시', '원주시', '강릉시', '동해시', '태백시', '속초시', '삼척시', '홍천군', '횡성군', '영월군', '평창군', '정선군', '철원군', '화천군', '양구군', '인제군', '고성군', '양양군'],
                    '충북': ['청주시', '충주시', '제천시', '보은군', '옥천군', '영동군', '증평군', '진천군', '괴산군', '음성군', '단양군'],
                    '충남': ['천안시', '공주시', '보령시', '아산시', '서산시', '논산시', '계룡시', '당진시', '금산군', '부여군', '서천군', '청양군', '홍성군', '예산군', '태안군'],
                    '전북': ['전주시', '군산시', '익산시', '정읍시', '남원시', '김제시', '완주군', '진안군', '무주군', '장수군', '임실군', '순창군', '고창군', '부안군'],
                    '전남': ['목포시', '여수시', '순천시', '나주시', '광양시', '담양군', '곡성군', '구례군', '고흥군', '보성군', '화순군', '장흥군', '강진군', '해남군', '영암군', '무안군', '함평군', '영광군', '장성군', '완도군', '진도군', '신안군']
                };
                return defaultSubregions[region] || ['기타'];
            };
        }
        
        const subregions = getSubregions(currentRegion);
        console.log('상세지역 옵션 로드됨:', {currentRegion, subregions});
        
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
        
        // 드롭다운이 성공적으로 추가되었는지 확인
        console.log('상세지역 드롭다운 DOM에 추가됨:', currentDropdown);
        
        // MutationObserver를 사용하여 드롭다운 제거 감지
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.removedNodes.forEach((node) => {
                        if (node === currentDropdown) {
                            console.error('상세지역 드롭다운이 MutationObserver에 의해 제거됨:', {
                                mutation: mutation,
                                target: mutation.target,
                                addedNodes: mutation.addedNodes,
                                removedNodes: mutation.removedNodes
                            });
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // 지역 드롭다운 보호를 위한 추가 이벤트 리스너
        const protectDropdown = (e) => {
            if (e.target === currentDropdown || currentDropdown.contains(e.target)) {
                console.log('상세지역 드롭다운 내부 클릭, 보호됨');
                e.stopPropagation();
                return false;
            }
        };
        
        // 이벤트 캡처링 단계에서 보호
        document.addEventListener('mousedown', protectDropdown, true);
        
        // 드롭다운이 즉시 닫히는 것을 방지하기 위한 추가 보호 로직
        setTimeout(() => {
            if (currentDropdown && currentDropdown.parentNode) {
                console.log('상세지역 드롭다운이 성공적으로 유지됨');
                observer.disconnect(); // 성공적으로 유지되면 observer 해제
                document.removeEventListener('mousedown', protectDropdown, true); // 보호 리스너 제거
            } else {
                console.error('상세지역 드롭다운이 예상치 못하게 제거됨');
                observer.disconnect(); // 제거되면 observer 해제
                document.removeEventListener('mousedown', protectDropdown, true); // 보호 리스너 제거
            }
        }, 500);
        
        // 상세지역 선택 이벤트 리스너
        currentDropdown.querySelectorAll('.dropdown-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                const selectedSubregion = this.getAttribute('data-option-id');
                
                // 중복 요청 방지
                const requestKey = `${id}_상세지역_${selectedSubregion}`;
                if (pendingRequests.has(requestKey)) {
                    console.log('상세지역 중복 요청 방지:', requestKey);
                    return;
                }
                
                // 요청 상태 설정
                pendingRequests.set(requestKey, Date.now());
                
                // 타임아웃 설정
                setTimeout(() => {
                    pendingRequests.delete(requestKey);
                }, requestTimeout);
                
                // UI 업데이트
                if (td) { 
                    td.innerHTML = selectedSubregion; 
                    td.setAttribute('data-value', selectedSubregion); 
                }
                
                // 서버 업데이트
                if (id && id.startsWith('temp_')) {
                    saveNewRowField(td.parentElement, '상세지역', selectedSubregion);
                } else {
                    fetch('/sales/update_row_field/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id='+id+'&field=상세지역&value='+encodeURIComponent(selectedSubregion)
                    })
                    .then(response => response.json())
                    .then(data => {
                        pendingRequests.delete(requestKey);
                        isProcessingRequest = false;
                        if (data.success) {
                            console.log('상세지역 업데이트 성공');
                            // 종속된 행들 찾아서 업데이트
                            if (typeof updateDependentRows === 'function') {
                                updateDependentRows(id, '상세지역', selectedSubregion);
                            }
                            // 실시간 동기화
                            if (typeof syncTableAndKanban === 'function') {
                                syncTableAndKanban('상세지역');
                            } else {
                                // syncTableAndKanban이 없는 경우 triggerKanbanRefreshIfNeeded 사용
                                if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                                    triggerKanbanRefreshIfNeeded();
                                }
                            }
                        } else {
                            throw new Error(data.error || '업데이트 실패');
                        }
                    })
                    .catch(error => {
                        pendingRequests.delete(requestKey);
                        isProcessingRequest = false;
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

// 모달용 일반 드롭다운 옵션 표시 함수
function showModalDropdownOptions(rowId, fieldName, btn) {
    console.log('showModalDropdownOptions 호출됨:', rowId, fieldName, btn);
    
    // 캐싱된 데이터가 있는지 확인
    if (window.dropdownOptionsCache && window.dropdownOptionsCache[fieldName]) {
        // 캐시된 데이터 사용
        const data = window.dropdownOptionsCache[fieldName];
        processModalDropdownOptions(data, rowId, fieldName, btn);
    } else {
        // 캐시에 없는 경우에만 API 요청
        fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName))
            .then(r => r.json())
            .then(function(data) {
                // 캐시에 저장
                if (!window.dropdownOptionsCache) {
                    window.dropdownOptionsCache = {};
                }
                window.dropdownOptionsCache[fieldName] = data;
                
                processModalDropdownOptions(data, rowId, fieldName, btn);
            })
            .catch(error => {
                console.error('모달 드롭다운 옵션 로드 실패:', error);
                alert('드롭다운 옵션을 불러올 수 없습니다.');
            });
    }
}

// 모달 드롭다운 옵션 처리를 위한 별도 함수
function processModalDropdownOptions(data, rowId, fieldName, btn) {
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
    
    // "선택 없음" 옵션 추가
    html += `
      <div class="dropdown-item" data-option-id="" data-option-text="선택 없음" data-color=""
           style="padding: 8px 12px; 
                  cursor: pointer; 
                  border-bottom: 1px solid #f0f0f0;
                  background: #f8f9fa;
                  color: #999;
                  font-style: italic;
                  transition: background-color 0.2s;">
        선택 없음
      </div>
    `;
    
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
            
            // 전역 처리 상태 확인
            if (isProcessingRequest) {
                console.log('전역 처리 중이므로 클릭 무시');
                return;
            }
            
            // 이미 처리 중인지 확인
            if (this.dataset.processing === 'true') {
                console.log('이미 처리 중인 옵션 클릭 무시');
                return;
            }
            
            // 전역 처리 상태 설정
            isProcessingRequest = true;
            
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
                isProcessingRequest = false;
            }, 1000);
        });
    });
    
    // 드롭다운 외부 클릭 시 닫기
    addGlobalClickHandler(dropdown, btn);
}

// 모달용 드롭다운 옵션 선택 함수
function selectModalDropdownOption(rowId, fieldName, optionId, optionText, btn, color) {
    console.log('selectModalDropdownOption 호출됨:', rowId, fieldName, optionId, optionText);
    
    // 중복 요청 방지를 위한 디바운싱
    const requestKey = `${rowId}_${fieldName}_${optionId}`;
    if (pendingRequests.has(requestKey)) {
      console.log('중복 요청 방지:', requestKey);
      return;
    }
    
    // 요청 상태 추적
    pendingRequests.set(requestKey, Date.now());
    
    // 타임아웃 설정
    setTimeout(() => {
      pendingRequests.delete(requestKey);
    }, requestTimeout);
    
    // 버튼 텍스트 즉시 업데이트
    if (optionId === '') {
        // "선택 없음"이 선택된 경우 "선택 없음"으로 표시
        btn.textContent = '선택 없음';
        btn.style.background = '#f8f9fa';
        btn.style.color = '#999';
        btn.style.fontStyle = 'italic';
    } else {
        btn.textContent = optionText;
        btn.style.background = color ? hexToRgba(color, 0.18) : '#f8f9fa';
        btn.style.color = '#333';
        btn.style.fontStyle = 'normal';
    }
    
    // 업종이 선택되면 빨간 테두리 제거
    if (fieldName === '업종') {
      highlightRequiredField(btn, false);
    }
    
      // 서버에 업데이트 요청
    console.log('update_row_filed_modal');
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
        pendingRequests.delete(requestKey);
        isProcessingRequest = false;
        
        if (data.success) {
            console.log('모달 드롭다운 업데이트 성공:', fieldName, optionId);
            
            // 종속된 행들 찾아서 업데이트
            if (typeof updateDependentRows === 'function') {
                updateDependentRows(rowId, fieldName, optionId);
            }
            
            // 실시간 동기화
            if (typeof syncTableAndKanban === 'function') {
                syncTableAndKanban(fieldName);
            } else {
                // syncTableAndKanban이 없는 경우 triggerKanbanRefreshIfNeeded 사용
                if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                    triggerKanbanRefreshIfNeeded(fieldName);
                }
            }
            
            // 칸반보드 설정 확인 및 리프레시
            checkKanbanAndRefresh(fieldName);
            
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
        pendingRequests.delete(requestKey);
        isProcessingRequest = false;
        
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
    // 지역과 상세지역은 특별 처리
    if (fieldName === '지역') {
        showModalRegionDropdown(rowId, fieldName, btn);
        return;
    } else if (fieldName === '상세지역') {
        showModalSubregionDropdown(rowId, fieldName, btn);
        return;
    }
    
    // 캐시된 사용자 속성이 있는지 확인
    if (window.userAttributesCache) {
        // 캐시된 데이터 사용
        const attr = window.userAttributesCache.find(a => a.name === fieldName);
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
    } else {
        // 캐시에 없는 경우에만 API 요청
        fetch('/sales/get_user_attributes/')
            .then(r => r.json())
            .then(function(attributesData) {
                if (!attributesData.success) {
                    alert('속성 정보를 불러올 수 없습니다.');
                    return;
                }
                
                // 캐시에 저장
                window.userAttributesCache = attributesData.attributes;
                
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
            })
            .catch(error => {
                console.error('사용자 속성 로드 실패:', error);
                alert('속성 정보를 불러오는 중 오류가 발생했습니다.');
            });
    }
  }
  
  // 모달용 상세지역 드롭다운 표시 함수
  function showModalSubregionDropdown(rowId, fieldName, btn) {
    // 캐시된 행 데이터가 있는지 확인 (상세모달에서 이미 가져온 데이터 재사용)
    if (window.currentDetailRowId === rowId && window.currentDetailRowData) {
        // 캐시된 데이터로 처리
        processSubregionDropdown(window.currentDetailRowData, rowId, fieldName, btn);
    } else {
        // 서버에서 현재 지역 가져오기
        fetch(`/sales/get_row_details/${rowId}/`)
          .then(response => response.json())
          .then(data => {
            if (data.success && data.row_data) {
                // 캐시에 저장
                window.currentDetailRowData = data.row_data;
                processSubregionDropdown(data.row_data, rowId, fieldName, btn);
            } else {
                alert('행 데이터를 불러올 수 없습니다.');
            }
          })
          .catch(error => {
            console.error('상세지역 드롭다운 로딩 오류:', error);
            alert('상세지역 정보를 불러오는 중 오류가 발생했습니다.');
          });
    }
  }
  
  // 상세지역 드롭다운 처리를 위한 별도 함수
  function processSubregionDropdown(rowData, rowId, fieldName, btn) {
    // 현재 지역과 상세지역 정보 추출
    let currentRegion = '';
    let currentSubregion = '';
    
    currentRegion = rowData['지역'] || '';
    currentSubregion = rowData['상세지역'] || '';
    
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
  }
  
  // 드롭다운 셀 값 변경 후 항상 칸반보드 새로고침 (최적화: debounce)
  async function triggerKanbanRefreshIfNeeded(fieldName) {
      // 칸반보드 설정이 로드되지 않았을 경우 로드
      if (!window.kanbanSettings) {
          try {
              const resp = await fetch('/sales/get_kanban_settings/');
              const data = await resp.json();
              if (data.success && data.settings) {
                  window.kanbanSettings = data.settings;
              }
          } catch (e) { 
              console.error('칸반보드 설정 로드 실패:', e);
          }
      }
      
      // 필드명이 전달된 경우 해당 필드가 관련 속성인지 확인
      if (fieldName) {
          // 메인 칸반보드 속성 확인
          let currentAttr = document.getElementById('kanbanAttributeSelect')?.value;
          if (!currentAttr) {
              currentAttr = window.kanbanSettings?.main_attr;
          }
          
          // 조건부 필터에서 사용되는 속성들 확인
          let filterAttrs = [];
          if (window.kanbanSettings?.filters) {
              filterAttrs = window.kanbanSettings.filters.map(filter => filter.attribute).filter(attr => attr && attr !== '');
          }
          
          // 커스텀 규칙에서 사용되는 속성들도 확인
          let customRuleAttrs = [];
          if (window.kanbanSettings?.custom_rules) {
              window.kanbanSettings.custom_rules.forEach(rule => {
                  if (rule.conditions) {
                      rule.conditions.forEach(condition => {
                          if (condition.attribute && condition.attribute !== '') {
                              customRuleAttrs.push(condition.attribute);
                          }
                      });
                  }
              });
          }
          
          // 모든 관련 속성들을 하나의 배열로 합치고 중복 제거
          let allRelevantAttrs = [currentAttr, ...filterAttrs, ...customRuleAttrs].filter(attr => attr && attr !== 'undefined');
          allRelevantAttrs = [...new Set(allRelevantAttrs)]; // 중복 제거
          
          // 해당 필드가 관련 속성이 아니면 리턴
          if (!allRelevantAttrs.includes(fieldName)) {
              return;
          }
      } else {
          // 필드명이 전달되지 않은 경우 기존 로직 유지
          let currentAttr = document.getElementById('kanbanAttributeSelect')?.value;
          if (!currentAttr) {
              currentAttr = window.kanbanSettings?.main_attr;
          }
          if (!currentAttr || currentAttr === 'undefined') return;
      }
      
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
            <div class="dropdown-item" data-option-id="" 
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
            <input type="text" placeholder="새 옵션 추가" class="new-option-input"
                   style="flex: 1; padding: 4px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
            <button class="add-option-btn" 
                    style="padding: 4px 12px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px; transition: background-color 0.2s;"
                    onmouseover="this.style.background='#0056b3'"
                    onmouseout="this.style.background='#007bff'">추가</button>
          </div>
        </div>`;
    }
    
    currentDropdown.innerHTML = html;
    document.body.appendChild(currentDropdown);
    
    // 새 옵션 추가 이벤트 바인딩
    if (type !== 'region' && type !== 'region_detail') {
        const addBtn = currentDropdown.querySelector('.add-option-btn');
        const inputField = currentDropdown.querySelector('.new-option-input');
        
        if (addBtn && inputField) {
            const handleAddOption = () => {
                const newOptionName = inputField.value.trim();
                if (newOptionName) {
                    addDropdownOption(type, newOptionName, td, currentDropdown);
                    inputField.value = '';
                }
            };
            
            // mousedown 이벤트 추가 - 글로벌 핸들러보다 먼저 실행되도록
            addBtn.addEventListener('mousedown', function(e) {
                e.stopPropagation();
                e.preventDefault();
            });
            
            addBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                handleAddOption();
            });
            
            inputField.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.stopPropagation();
                    e.preventDefault();
                    handleAddOption();
                }
            });
            
            // 입력 필드 클릭 시 드롭다운이 닫히지 않도록
            inputField.addEventListener('click', function(e) {
                e.stopPropagation();
            });
            
            // 입력 필드 mousedown 이벤트도 추가
            inputField.addEventListener('mousedown', function(e) {
                e.stopPropagation();
            });
        }
    }
    
    // 단일선택: 옵션 클릭 시 바로 선택
    currentDropdown.querySelectorAll('.dropdown-item[data-option-id]').forEach(function(item) {
        // 기존 이벤트 리스너 제거 (중복 방지)
        const newItem = item.cloneNode(true);
        item.parentNode.replaceChild(newItem, item);
        
        newItem.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            
            // 전역 처리 상태 확인
            if (isProcessingRequest) {
                console.log('전역 처리 중이므로 클릭 무시');
                return;
            }
            
            // 이미 처리 중인지 확인
            if (this.dataset.processing === 'true') {
                console.log('이미 처리 중인 옵션 클릭 무시');
                return;
            }
            
            // 전역 처리 상태 설정
            isProcessingRequest = true;
            
            // 처리 중 상태로 설정
            this.dataset.processing = 'true';
            
            const optionId = this.getAttribute('data-option-id');
            
            // 중복 요청 방지
            const requestKey = `${id}_${type}_${optionId}`;
            if (pendingRequests.has(requestKey)) {
                console.log('중복 요청 방지:', requestKey);
                this.dataset.processing = 'false';
                isProcessingRequest = false;
                return;
            }
            
            // 요청 상태 설정
            pendingRequests.set(requestKey, Date.now());
            
            // 타임아웃 설정
            setTimeout(() => {
                pendingRequests.delete(requestKey);
                isProcessingRequest = false;
            }, requestTimeout);
            
            const option = options.find(o => String(o.id) === String(optionId));
            // UI 업데이트 - 즉시 실행
            if (optionId === '') {
                // "선택 없음"이 선택된 경우 "선택 없음" pill로 표시
                if (td) { 
                    td.innerHTML = `<div class="dropdown-pill dropdown-pill-empty">선택 없음</div>`; 
                    td.setAttribute('data-value', ''); 
                }
                
                // 커스텀 이벤트 발생으로 실시간 업데이트 보장
                const rowId = td.parentElement.getAttribute('data-id');
                document.dispatchEvent(new CustomEvent('dropdownOptionChanged', {
                    detail: {
                        fieldName: type,
                        newValue: '',
                        rowId: rowId
                    }
                }));
            } else if (option) {
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
                this.dataset.processing = 'false';
            } else {
                console.log('update_row_field_modal2');
                console.log('전송할 값:', {optionId, type, id});
                console.log('optionId 타입:', typeof optionId);
                console.log('optionId 길이:', optionId.length);
                console.log('optionId === "":', optionId === '');
                
                fetch('/sales/update_row_field/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(optionId)
                })
                .then(response => response.json())
                .then(data => {
                    pendingRequests.delete(requestKey);
                    this.dataset.processing = 'false';
                    isProcessingRequest = false;
                    if (data.success) {
                        // 종속된 행들 찾아서 업데이트 (ID 전달)
                        if (typeof updateDependentRows === 'function') {
                            updateDependentRows(id, type, optionId);
                        }
                        
                        // 실시간 동기화
                        if (typeof syncTableAndKanban === 'function') {
                            syncTableAndKanban(type);
                        } else {
                            // syncTableAndKanban이 없는 경우 triggerKanbanRefreshIfNeeded 사용
                            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                                triggerKanbanRefreshIfNeeded(type);
                            }
                        }
                        
                        // 칸반보드 설정 확인 및 리프레시
                        checkKanbanAndRefresh(type);
                        
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
                    pendingRequests.delete(requestKey);
                    this.dataset.processing = 'false';
                    isProcessingRequest = false;
                    console.error('드롭다운 옵션 업데이트 실패:', error);
                    alert('업데이트 중 오류가 발생했습니다: ' + error.message);
                });
            }
        });
    });
    
    // 컨트롤 버튼들에 대한 별도 이벤트 핸들러 추가
    if (type !== 'region' && type !== 'region_detail') {
        // 색상 변경 버튼 이벤트
        currentDropdown.querySelectorAll('input[data-color-edit]').forEach(function(colorInput) {
            colorInput.addEventListener('click', function(e) {
                e.stopPropagation();
                // e.preventDefault() 제거 - 컬러피커가 열리도록 함
                console.log('색상 변경 버튼 클릭됨:', this.getAttribute('data-color-edit'));
                // 컬러피커가 자동으로 열림 (input type="color"의 기본 동작)
            });
            
            colorInput.addEventListener('change', function(e) {
                e.stopPropagation();
                const optionId = this.getAttribute('data-color-edit');
                const newColor = this.value;
                console.log('색상 변경됨:', optionId, newColor);
                
                // 서버에 색상 업데이트 요청
                updateDropdownOptionColor(type, optionId, newColor, td, currentDropdown);
            });
        });
        
        // 수정 버튼 이벤트
        currentDropdown.querySelectorAll('button[data-edit]').forEach(function(editBtn) {
            // mousedown 이벤트 추가 - 글로벌 핸들러보다 먼저 실행되도록
            editBtn.addEventListener('mousedown', function(e) {
                e.stopPropagation();
                e.preventDefault();
            });
            
            editBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                const optionId = this.getAttribute('data-edit');
                console.log('수정 버튼 클릭됨:', optionId);
                
                // 옵션 수정 처리
                editDropdownOption(type, optionId, td, currentDropdown);
            });
        });
        
        // 삭제 버튼 이벤트
        currentDropdown.querySelectorAll('button[data-del]').forEach(function(delBtn) {
            // mousedown 이벤트 추가 - 글로벌 핸들러보다 먼저 실행되도록
            delBtn.addEventListener('mousedown', function(e) {
                e.stopPropagation();
                e.preventDefault();
            });
            
            delBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                const optionId = this.getAttribute('data-del');
                console.log('삭제 버튼 클릭됨:', optionId);
                
                // 삭제 확인 후 처리
                if (confirm('이 옵션을 삭제하시겠습니까? 테이블의 관련 데이터도 함께 업데이트됩니다.')) {
                    deleteDropdownOption(type, optionId, td, currentDropdown);
                }
            });
        });
    }
    
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

// 중복 레코드 정리 유틸리티 함수
function cleanupDuplicateRecords() {
    console.log('중복 레코드 정리 시작...');
    
    fetch('/sales/cleanup_duplicates/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('중복 레코드 정리 완료:', data.message);
            alert(`중복 레코드 정리 완료: ${data.deleted_count}개 레코드가 정리되었습니다.`);
        } else {
            console.error('중복 레코드 정리 실패:', data.error);
            alert('중복 레코드 정리 실패: ' + data.error);
        }
    })
    .catch(error => {
        console.error('중복 레코드 정리 요청 오류:', error);
        alert('중복 레코드 정리 중 오류가 발생했습니다.');
    });
}

// CSRF 토큰 가져오기 함수 (이미 정의되어 있지 않은 경우)
function getCsrfToken() {
    const name = 'csrftoken';
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

// 드롭다운 옵션 수정 시 칸반보드 리프레시 함수
async function checkKanbanAndRefresh(fieldName) {
    // 칸반보드 설정이 로드되지 않았을 경우 로드
    if (!window.kanbanSettings) {
        try {
            const resp = await fetch('/sales/get_kanban_settings/');
            const data = await resp.json();
            if (data.success && data.settings) {
                window.kanbanSettings = data.settings;
            }
        } catch (e) { 
            console.error('칸반보드 설정 로드 실패:', e);
            return;
        }
    }
    
    // 메인 칸반보드 속성 확인
    let currentAttr = document.getElementById('kanbanAttributeSelect')?.value;
    if (!currentAttr) {
        currentAttr = window.kanbanSettings?.main_attr;
    }
    
    // 조건부 필터에서 사용되는 속성들 확인
    let filterAttrs = [];
    if (window.kanbanSettings?.filters) {
        filterAttrs = window.kanbanSettings.filters.map(filter => filter.attribute).filter(attr => attr && attr !== '');
    }
    
    // 커스텀 규칙에서 사용되는 속성들도 확인
    let customRuleAttrs = [];
    if (window.kanbanSettings?.custom_rules) {
        window.kanbanSettings.custom_rules.forEach(rule => {
            if (rule.conditions) {
                rule.conditions.forEach(condition => {
                    if (condition.attribute && condition.attribute !== '') {
                        customRuleAttrs.push(condition.attribute);
                    }
                });
            }
        });
    }
    
    // 모든 관련 속성들을 하나의 배열로 합치고 중복 제거
    let allRelevantAttrs = [currentAttr, ...filterAttrs, ...customRuleAttrs].filter(attr => attr && attr !== 'undefined');
    allRelevantAttrs = [...new Set(allRelevantAttrs)]; // 중복 제거
    
    // 해당 필드가 관련 속성인 경우 칸반보드 리프레시
    if (allRelevantAttrs.includes(fieldName)) {
        console.log('칸반보드 관련 속성이 변경되어 새로고침합니다:', fieldName);
        if (typeof refreshKanban === 'function') {
            refreshKanban();
        }
    }
}

// 드롭다운 옵션 색상 업데이트 함수
function updateDropdownOptionColor(fieldName, optionId, newColor) {
    console.log('색상 업데이트 요청:', fieldName, optionId, newColor);
    
    fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName) + '&id=' + optionId + '&color=' + encodeURIComponent(newColor), {
        method: 'PUT',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('색상 업데이트 성공');
            // 드롭다운 새로고침
            if (typeof updateTableDropdownOptions === 'function') {
                updateTableDropdownOptions(fieldName);
            }
            // 칸반보드 리프레시
            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                triggerKanbanRefreshIfNeeded(fieldName);
            }
        } else {
            throw new Error(data.error || '색상 업데이트 실패');
        }
    })
    .catch(error => {
        console.error('색상 업데이트 실패:', error);
        alert('색상 업데이트 중 오류가 발생했습니다: ' + error.message);
    });
}

// 드롭다운 옵션 수정 함수
function editDropdownOption(fieldName, optionId, td, currentDropdown) {
    console.log('옵션 수정 요청:', fieldName, optionId);
    
    // 현재 옵션 정보 가져오기
    fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldName)}`)
        .then(response => response.json())
        .then(data => {
            if (data.options) {
                const option = data.options.find(opt => opt.id == optionId);
                if (option) {
                    const newName = prompt('옵션 이름을 수정하세요:', option.option);
                    
                    if (newName && newName.trim() !== '' && newName.trim() !== option.option) {
                        updateDropdownOptionName(fieldName, optionId, newName.trim(), option.option, td, currentDropdown);
                    }
                } else {
                    alert('옵션을 찾을 수 없습니다.');
                }
            } else {
                throw new Error(data.error || '옵션 정보를 가져올 수 없습니다.');
            }
        })
        .catch(error => {
            console.error('옵션 정보 가져오기 실패:', error);
            alert('옵션 정보를 가져오는 중 오류가 발생했습니다.');
        });
}

// 드롭다운 옵션 이름 업데이트 함수
function updateDropdownOptionName(fieldName, optionId, newName) {
    console.log('옵션 이름 업데이트 요청:', fieldName, optionId, newName);
    
    fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName) + '&id=' + optionId + '&name=' + encodeURIComponent(newName), {
        method: 'PUT',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('옵션 이름 업데이트 성공');
            // 드롭다운 새로고침
            if (typeof updateTableDropdownOptions === 'function') {
                updateTableDropdownOptions(fieldName);
            }
            // 칸반보드 리프레시
            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                triggerKanbanRefreshIfNeeded(fieldName);
            }
        } else {
            throw new Error(data.error || '옵션 이름 업데이트 실패');
        }
    })
    .catch(error => {
        console.error('옵션 이름 업데이트 실패:', error);
        alert('옵션 이름 업데이트 중 오류가 발생했습니다: ' + error.message);
    });
}

// 드롭다운 옵션 삭제 함수
function deleteDropdownOption(fieldName, optionId) {
    console.log('옵션 삭제 요청:', fieldName, optionId);
    
    fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName) + '&id=' + optionId, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('옵션 삭제 성공');
            // 드롭다운 새로고침
            if (typeof updateTableDropdownOptions === 'function') {
                updateTableDropdownOptions(fieldName);
            }
            // 칸반보드 리프레시
            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                triggerKanbanRefreshIfNeeded(fieldName);
            }
        } else {
            throw new Error(data.error || '옵션 삭제 실패');
        }
    })
    .catch(error => {
        console.error('옵션 삭제 실패:', error);
        alert('옵션 삭제 중 오류가 발생했습니다: ' + error.message);
    });
}

// 새 드롭다운 옵션 추가 함수
function addDropdownOption(fieldName, optionName, td, currentDropdown) {
    console.log('새 옵션 추가 요청:', fieldName, optionName);
    
    fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldName)}&name=${encodeURIComponent(optionName)}&color=${encodeURIComponent('#e3f2fd')}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('옵션 추가 성공');
            // 드롭다운 캐시 초기화
            if (window.dropdownOptionsCache && window.dropdownOptionsCache[fieldName]) {
                delete window.dropdownOptionsCache[fieldName];
            }
            // 드롭다운 새로고침
            refreshCurrentDropdown(fieldName, td, currentDropdown);
            // 칸반보드 리프레시
            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                triggerKanbanRefreshIfNeeded(fieldName);
            }
        } else {
            throw new Error(data.error || '옵션 추가 실패');
        }
    })
    .catch(error => {
        console.error('옵션 추가 실패:', error);
        alert('옵션 추가 중 오류가 발생했습니다: ' + error.message);
    });
}

// 현재 드롭다운 새로고침 함수
function refreshCurrentDropdown(fieldName, td, currentDropdown) {
    if (!currentDropdown || !currentDropdown.parentNode) {
        console.log('드롭다운이 이미 닫혀있어 새로고침할 수 없습니다.');
        return;
    }
    
    // 새로운 옵션 데이터 가져오기
    fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName))
        .then(r => r.json())
        .then(function(data) {
            if (data.options) {
                // 기존 드롭다운 제거
                if (currentDropdown && currentDropdown.parentNode) {
                    currentDropdown.parentNode.removeChild(currentDropdown);
                }
                
                // 새 드롭다운 생성
                const id = td.parentElement.getAttribute('data-id');
                openDropdown(td, fieldName, id);
            }
        })
        .catch(error => {
            console.error('드롭다운 새로고침 실패:', error);
        });
}

// 드롭다운 옵션 색상 업데이트 함수 (수정)
function updateDropdownOptionColor(fieldName, optionId, newColor, td, currentDropdown) {
    console.log('색상 업데이트 요청:', fieldName, optionId, newColor);
    
    fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldName)}&id=${encodeURIComponent(optionId)}&color=${encodeURIComponent(newColor)}`, {
        method: 'PUT',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('색상 업데이트 성공');
            // 테이블의 모든 관련 셀 업데이트
            updateTableCellsWithOptionColor(fieldName, optionId, newColor);
            // 드롭다운 캐시 초기화
            if (window.dropdownOptionsCache && window.dropdownOptionsCache[fieldName]) {
                delete window.dropdownOptionsCache[fieldName];
            }
            // 드롭다운 새로고침
            refreshCurrentDropdown(fieldName, td, currentDropdown);
            // 칸반보드 리프레시
            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                triggerKanbanRefreshIfNeeded(fieldName);
            }
        } else {
            throw new Error(data.error || '색상 업데이트 실패');
        }
    })
    .catch(error => {
        console.error('색상 업데이트 실패:', error);
        alert('색상 업데이트 중 오류가 발생했습니다: ' + error.message);
    });
}

// 드롭다운 옵션 수정 함수 (수정)
function editDropdownOption(fieldName, optionId, td, currentDropdown) {
    console.log('옵션 수정 요청:', fieldName, optionId);
    
    // 현재 옵션 정보 가져오기
    fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldName)}`)
        .then(response => response.json())
        .then(data => {
            if (data.options) {
                const option = data.options.find(opt => opt.id == optionId);
                if (option) {
                    const newName = prompt('옵션 이름을 수정하세요:', option.option);
                    
                    if (newName && newName.trim() !== '' && newName.trim() !== option.option) {
                        updateDropdownOptionName(fieldName, optionId, newName.trim(), option.option, td, currentDropdown);
                    }
                } else {
                    alert('옵션을 찾을 수 없습니다.');
                }
            } else {
                throw new Error(data.error || '옵션 정보를 가져올 수 없습니다.');
            }
        })
        .catch(error => {
            console.error('옵션 정보 가져오기 실패:', error);
            alert('옵션 정보를 가져오는 중 오류가 발생했습니다.');
        });
}

// 드롭다운 옵션 이름 업데이트 함수 (수정)
function updateDropdownOptionName(fieldName, optionId, newName, oldName, td, currentDropdown) {
    console.log('옵션 이름 업데이트 요청:', fieldName, optionId, newName, oldName);
    
    fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldName)}&id=${encodeURIComponent(optionId)}&name=${encodeURIComponent(newName)}`, {
        method: 'PUT',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('옵션 이름 업데이트 성공');
            // 테이블의 모든 관련 셀 업데이트 (옵션명 변경)
            updateTableCellsWithOptionName(fieldName, optionId, newName, oldName);
            // 드롭다운 캐시 초기화
            if (window.dropdownOptionsCache && window.dropdownOptionsCache[fieldName]) {
                delete window.dropdownOptionsCache[fieldName];
            }
            // 드롭다운 새로고침
            refreshCurrentDropdown(fieldName, td, currentDropdown);
            // 칸반보드 리프레시
            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                triggerKanbanRefreshIfNeeded(fieldName);
            }
        } else {
            throw new Error(data.error || '옵션 이름 업데이트 실패');
        }
    })
    .catch(error => {
        console.error('옵션 이름 업데이트 실패:', error);
        alert('옵션 이름 업데이트 중 오류가 발생했습니다: ' + error.message);
    });
}

// 드롭다운 옵션 삭제 함수 (수정)
function deleteDropdownOption(fieldName, optionId, td, currentDropdown) {
    console.log('옵션 삭제 요청:', fieldName, optionId);
    
    fetch(`/sales/dropdown_options/?field=${encodeURIComponent(fieldName)}&id=${encodeURIComponent(optionId)}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('옵션 삭제 성공');
            // 테이블의 모든 관련 셀을 "선택 없음"으로 업데이트
            updateTableCellsAfterOptionDelete(fieldName, optionId);
            // 드롭다운 캐시 초기화
            if (window.dropdownOptionsCache && window.dropdownOptionsCache[fieldName]) {
                delete window.dropdownOptionsCache[fieldName];
            }
            // 드롭다운 새로고침
            refreshCurrentDropdown(fieldName, td, currentDropdown);
            // 칸반보드 리프레시
            if (typeof triggerKanbanRefreshIfNeeded === 'function') {
                triggerKanbanRefreshIfNeeded(fieldName);
            }
        } else {
            throw new Error(data.error || '옵션 삭제 실패');
        }
    })
    .catch(error => {
        console.error('옵션 삭제 실패:', error);
        alert('옵션 삭제 중 오류가 발생했습니다: ' + error.message);
    });
}

// 테이블 셀의 옵션 색상 업데이트
function updateTableCellsWithOptionColor(fieldName, optionId, newColor) {
    const cells = document.querySelectorAll(`td[data-field="${fieldName}"]`);
    cells.forEach(cell => {
        const currentValue = cell.getAttribute('data-value');
        if (currentValue && currentValue == optionId) {
            const pill = cell.querySelector('.dropdown-pill');
            if (pill) {
                pill.style.background = hexToRgba(newColor, 0.18);
            }
        }
    });
}

// 테이블 셀의 옵션명 업데이트
function updateTableCellsWithOptionName(fieldName, optionId, newName, oldName) {
    const cells = document.querySelectorAll(`td[data-field="${fieldName}"]`);
    cells.forEach(cell => {
        const currentValue = cell.getAttribute('data-value');
        if (currentValue && currentValue == optionId) {
            const pill = cell.querySelector('.dropdown-pill');
            if (pill && pill.textContent.trim() === oldName) {
                pill.textContent = newName;
            }
        }
    });
}

// 옵션 삭제 후 테이블 셀 업데이트
function updateTableCellsAfterOptionDelete(fieldName, deletedOptionId) {
    const cells = document.querySelectorAll(`td[data-field="${fieldName}"]`);
    cells.forEach(cell => {
        const currentValue = cell.getAttribute('data-value');
        if (currentValue && currentValue == deletedOptionId) {
            // "선택 없음"으로 업데이트
            cell.innerHTML = `<div class="dropdown-pill dropdown-pill-empty">선택 없음</div>`;
            cell.setAttribute('data-value', '');
            
            // 서버에도 업데이트 (백그라운드에서)
            const rowId = cell.parentElement.getAttribute('data-id');
            if (rowId && !rowId.startsWith('temp_')) {
                fetch('/sales/update_row_field/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `id=${rowId}&field=${encodeURIComponent(fieldName)}&value=`
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        console.error('옵션 삭제 후 셀 업데이트 실패:', data.error);
                    }
                })
                .catch(error => {
                    console.error('옵션 삭제 후 셀 업데이트 요청 실패:', error);
                });
            }
        }
    });
}