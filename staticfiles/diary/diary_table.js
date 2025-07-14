// CSRF 토큰 가져오기 함수
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// 드롭다운 닫기 함수
function closeDropdown() {
    if (window.dropdown && window.dropdown.parentNode) {
        window.dropdown.parentNode.removeChild(window.dropdown);
        window.dropdown = null;
    }
    // 모든 기존 드롭다운 요소들 제거
    document.querySelectorAll('.dropdown-edit').forEach(el => el.remove());
}

// hex 색상을 rgba로 변환하는 함수
function hexToRgba(hex, alpha) {
    // # 제거
    hex = hex.replace('#', '');
    
    // 3자리 hex를 6자리로 확장
    if (hex.length === 3) {
        hex = hex.split('').map(char => char + char).join('');
    }
    
    // RGB 값 추출
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function openDropdown(td, type, id, currentId, currentSubregion) {
    console.log('openDropdown 호출됨:', {td, type, id, currentId, currentSubregion});
    
    // 기존 드롭다운 완전히 제거
    if (window.dropdown && window.dropdown.parentNode) {
      window.dropdown.parentNode.removeChild(window.dropdown);
      window.dropdown = null;
    }
    
    // 모든 기존 드롭다운 요소들 제거
    document.querySelectorAll('.dropdown-edit').forEach(el => el.remove());
    
    // 클릭된 셀의 위치 정보 가져오기
    const rect = td.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    
    // 새 드롭다운 생성 - select 태그처럼 자연스럽게
    window.dropdown = document.createElement('div');
    window.dropdown.className = 'dropdown-edit';
    window.dropdown.id = 'current-dropdown-' + Date.now();
    
    // 셀 바로 아래에 위치하도록 계산
    const topPosition = rect.bottom + scrollTop + 2;
    const leftPosition = rect.left + scrollLeft;
    
    // select 태그처럼 자연스러운 스타일 적용
    window.dropdown.setAttribute('style', `
      position: absolute !important;
      background: white !important;
      border: 1px solid #ccc !important;
      border-radius: 4px !important;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
      z-index: 1000 !important;
      min-width: ${rect.width}px !important;
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
    
    console.log('드롭다운 위치 설정:', {top: topPosition, left: leftPosition, cellWidth: rect.width});
  
    if(type === 'region') {
        // 지역 드롭다운
        var regionNames = ['서울','경기','인천','대구','경북', '경남', '부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
        let selectedRegion = currentId || '서울';
        
        let html = '';
        regionNames.forEach(function(region) {
            const isSelected = region === selectedRegion;
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
        
        window.dropdown.innerHTML = html;
        
        console.log('지역 드롭다운 HTML 생성 완료');
        
        // DOM에 추가
        document.body.appendChild(window.dropdown);
        
        console.log('지역 드롭다운 DOM 추가 완료');
        
        // 호버 효과와 클릭 이벤트 바인딩
        window.dropdown.querySelectorAll('.dropdown-item[data-region]').forEach(function(item) {
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
                
                console.log('지역 클릭됨:', this.getAttribute('data-region'));
                const selectedRegion = this.getAttribute('data-region');
                
                // UI 업데이트
                td.innerHTML = `<div style="display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${selectedRegion}</div>`;
                td.setAttribute('data-value', selectedRegion);
                
                // 상세지역 td도 같이 변경 (첫 번째 값으로 초기화)
                var subTd = td.parentElement.querySelector('td[data-field="상세지역"]');
                if(subTd) {
                    var regionMap = {
                        '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
                        '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
                        '인천': ['계양구','남동구','동구','미추홀구','부평구','서구','연수구','중구','강화군','옹진군'],
                        '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
                        '경북': ['포항시','경주시','김천시','안동시','구미시','영주시','영천시','상주시','문경시','경산시','군위군','의성군','청송군','영양군','영덕군','청도군','고령군','성주군','칠곡군','예천군','봉화군','울진군','울릉군'],
                        '경남': ['창원시','진주시','통영시','사천시','김해시','밀양시','거제시','양산시','의령군','함안군','창녕군','고성군','남해군','하동군','산청군','함양군','거창군','합천군'],
                        '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
                        '광주': ['동구','서구','남구','북구','광산구'],
                        '대전': ['동구','중구','서구','유성구','대덕구'],
                        '울산': ['중구','남구','동구','북구','울주군'],
                        '세종': ['세종특별자치시'],
                        '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
                        '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
                        '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
                        '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
                        '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군']
                    };
                    var firstSubregion = (regionMap[selectedRegion] || [])[0] || '';
                    subTd.innerText = firstSubregion;
                }
                
                // 드롭다운 제거
                if (window.dropdown && window.dropdown.parentNode) {
                  window.dropdown.parentNode.removeChild(window.dropdown);
                  window.dropdown = null;
                }
                
                // 서버 업데이트
                console.log('서버 업데이트 시작:', {id, selectedRegion});
                
                // 새 행인 경우
                if (id && id.startsWith('temp_')) {
                    saveNewRowField(td.parentElement, '지역', selectedRegion);
                } else {
                    // 기존 행인 경우
                    fetch('/600/update/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id='+id+'&field=지역&value='+encodeURIComponent(selectedRegion)
                    })
                    .then(response => {
                        console.log('서버 응답 상태:', response.status);
                        return response.json();
                    })
                    .then(data => {
                        console.log('서버 응답 데이터:', data);
                        if (data.success) {
                            // 부분 업데이트로 변경
                            updateTableCell(id, '지역', selectedRegion);
                            
                            // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우
                            if (window.currentStatusTab !== null && '지역' === window.statusAttributeName) {
                                // 해당 행의 상태 셀 업데이트
                                const row = document.querySelector(`tr[data-id="${id}"]`);
                                if (row) {
                                    const statusCell = row.querySelector(`td[data-field="지역"]`);
                                    if (statusCell) {
                                        // 새로운 값으로 data-value 업데이트
                                        statusCell.setAttribute('data-value', selectedRegion);
                                        
                                        // 상태 필터 즉시 재적용
                                        setTimeout(() => {
                                            if (typeof applyStatusFilter === 'function') {
                                                applyStatusFilter();
                                            }
                                        }, 50);
                                    }
                                }
                            }
                            
                            // 모달 업데이트 콜백이 있는 경우 실행
                            if (typeof window._modalAfterUpdateAll === 'function') {
                                window._modalAfterUpdateAll(id); 
                                window._modalAfterUpdateAll = null; 
                            }
                        } else {
                            throw new Error(data.error || '업데이트 실패');
                        }
                    })
                    .catch(error => {
                        console.error('업데이트 실패:', error);
                        alert('업데이트 중 오류가 발생했습니다: ' + error.message);
                    });
                }
            });
        });
        
        // 외부 클릭 시 드롭다운 닫기
        setTimeout(() => {
            document.addEventListener('click', function closeHandler(e) {
                if (window.dropdown && !window.dropdown.contains(e.target) && !td.contains(e.target)) {
                    if (window.dropdown.parentNode) {
                        window.dropdown.parentNode.removeChild(window.dropdown);
                        window.dropdown = null;
                    }
                    document.removeEventListener('click', closeHandler);
                }
            });
        }, 100);
        
        return;
        
    } else if(type === 'region_detail') {
        // 상세지역 드롭다운
        var regionMap = {
            '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
            '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
            '인천': ['계양구','남동구','동구','미추홀구','부평구','서구','연수구','중구','강화군','옹진군'],
            '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
            '경북': ['포항시','경주시','김천시','안동시','구미시','영주시','영천시','상주시','문경시','경산시','군위군','의성군','청송군','영양군','영덕군','청도군','고령군','성주군','칠곡군','예천군','봉화군','울진군','울릉군'],
            '경남': ['창원시','진주시','통영시','사천시','김해시','밀양시','거제시','양산시','의령군','함안군','창녕군','고성군','남해군','하동군','산청군','함양군','거창군','합천군'],
            '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
            '광주': ['동구','서구','남구','북구','광산구'],
            '대전': ['동구','중구','서구','유성구','대덕구'],
            '울산': ['중구','남구','동구','북구','울주군'],
            '세종': ['세종특별자치시'],
            '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
            '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
            '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
            '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
            '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군']
        };
        var currentRegion = td.parentElement.querySelector('td[data-field="지역"]').innerText.trim();
        var subregions = regionMap[currentRegion] || [];
        let selectedSubregion = currentSubregion || '';
        
        let html = '';
        subregions.forEach(function(sub) {
            const isSelected = sub === selectedSubregion;
            html += `
              <div class="dropdown-item" data-subregion="${sub}" 
                   style="padding: 8px 12px !important; 
                          cursor: pointer !important; 
                          border-bottom: 1px solid #f0f0f0 !important;
                          ${isSelected ? 'background: #007bff !important; color: white !important;' : 'background: white !important; color: #333 !important;'}
                          transition: background-color 0.2s !important;">
                ${sub}
              </div>
            `;
        });
        
        window.dropdown.innerHTML = html;
        
        console.log('상세지역 드롭다운 HTML 생성 완료');
        
        // DOM에 추가
        document.body.appendChild(window.dropdown);
        
        console.log('상세지역 드롭다운 DOM 추가 완료');
        
        // 호버 효과와 클릭 이벤트 바인딩
        window.dropdown.querySelectorAll('.dropdown-item[data-subregion]').forEach(function(item) {
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
                
                console.log('상세지역 클릭됨:', this.getAttribute('data-subregion'));
                const selectedSubregion = this.getAttribute('data-subregion');
                
                // UI 업데이트
                td.innerHTML = `<div style="display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${selectedSubregion}</div>`;
                td.setAttribute('data-value', selectedSubregion);
                
                // 드롭다운 제거
                if (window.dropdown && window.dropdown.parentNode) {
                  window.dropdown.parentNode.removeChild(window.dropdown);
                  window.dropdown = null;
                }
                
                // 서버 업데이트
                console.log('서버 업데이트 시작:', {id, selectedSubregion});
                
                // 새 행인 경우
                if (id && id.startsWith('temp_')) {
                    saveNewRowField(td.parentElement, '상세지역', selectedSubregion);
                } else {
                    // 기존 행인 경우
                    fetch('/600/update/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'id='+id+'&field=상세지역&value='+encodeURIComponent(selectedSubregion)
                    })
                    .then(response => {
                        console.log('서버 응답 상태:', response.status);
                        return response.json();
                    })
                    .then(data => {
                        console.log('서버 응답 데이터:', data);
                        if (data.success) {
                            // 실시간 동기화
                            syncTableAndKanban('상세지역');
                            
                            // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우
                            if (window.currentStatusTab !== null && '상세지역' === window.statusAttributeName) {
                                // 해당 행의 상태 셀 업데이트
                                const row = document.querySelector(`tr[data-id="${id}"]`);
                                if (row) {
                                    const statusCell = row.querySelector(`td[data-field="상세지역"]`);
                                    if (statusCell) {
                                        // 새로운 값으로 data-value 업데이트
                                        statusCell.setAttribute('data-value', selectedSubregion);
                                        
                                        // 상태 필터 즉시 재적용
                                        setTimeout(() => {
                                            if (typeof applyStatusFilter === 'function') {
                                                applyStatusFilter();
                                            }
                                        }, 50);
                                    }
                                }
                            }
                            
                            // 모달 업데이트 콜백이 있는 경우 실행
                            if (typeof window._modalAfterUpdateAll === 'function') {
                                window._modalAfterUpdateAll(id); 
                                window._modalAfterUpdateAll = null; 
                            }
                        } else {
                            throw new Error(data.error || '업데이트 실패');
                        }
                    })
                    .catch(error => {
                        console.error('업데이트 실패:', error);
                        alert('업데이트 중 오류가 발생했습니다: ' + error.message);
                    });
                }
            });
        });
        
        // 외부 클릭 시 드롭다운 닫기
        setTimeout(() => {
            document.addEventListener('click', function closeHandler(e) {
                if (window.dropdown && !window.dropdown.contains(e.target) && !td.contains(e.target)) {
                    if (window.dropdown.parentNode) {
                        window.dropdown.parentNode.removeChild(window.dropdown);
                        window.dropdown = null;
                    }
                    document.removeEventListener('click', closeHandler);
                }
            });
        }, 100);
        
        return;
    } else {
        // 일반 드롭다운 (구분, 영업진행 등) 처리
        console.log('일반 드롭다운 처리 시작:', {type, id});
        
        fetch('/600/dropdown_options/?field=' + encodeURIComponent(type))
            .then(r => r.json())
            .then(function(data) {
                console.log('드롭다운 옵션 로드됨:', data);
                if (data.options) {
                    const options = data.options;
                    const currentValue = td.getAttribute('data-value') || '';
                    
                    // 모달과 동일한 깔끔한 구조로 변경
                    let html = `<div style="padding: 8px; border-bottom: 1px solid #eee;"><b>${type} 선택</b></div>`;
                    
                    // 옵션 목록 컨테이너
                    html += '<div style="max-height: 150px; overflow-y: auto;">';
                    
                    options.forEach(function(opt) {
                        // 단일선택 값 처리
                        let isSelected = false;
                        const currentValue = td.getAttribute('data-value') || '';
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
                          <div class="dropdown-option-container" style="padding: 4px 8px; border-bottom: 1px solid #f0f0f0;">
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
                                <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${opt.option}</span>
                              </div>
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
                            </div>
                          </div>
                        `;
                    });
                    html += '</div>';
                    // 새 옵션 추가 영역은 그대로 유지
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
                    window.dropdown.innerHTML = html;
                    document.body.appendChild(window.dropdown);
                    
                    // === 드롭다운 모달 이벤트 바인딩 추가 ===
                    bindDropdownModalEvents(window.dropdown, type, options);
                    
                    // 단일선택: 옵션 클릭 시 바로 선택
                    window.dropdown.querySelectorAll('.dropdown-item[data-option-id]').forEach(function(item) {
                        item.addEventListener('click', function(e) {
                            e.stopPropagation();
                            const optionId = this.getAttribute('data-option-id');
                            const option = options.find(o => String(o.id) === String(optionId));
                            // UI 업데이트
                            const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                            td.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                            td.setAttribute('data-value', optionId);
                            // 서버 업데이트 - 단일 값으로 저장
                            if (id && id.startsWith('temp_')) {
                                saveNewRowField(td.parentElement, type, optionId);
                            } else {
                                fetch('/600/update_row_field/', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                    body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(optionId)
                                })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        syncTableAndKanban(type);
                                    } else {
                                        throw new Error(data.error || '업데이트 실패');
                                    }
                                })
                                .catch(error => {
                                    console.error('업데이트 실패:', error);
                                    alert('업데이트 중 오류가 발생했습니다: ' + error.message);
                                });
                            }
                            // 드롭다운 닫기
                            if (window.dropdown && window.dropdown.parentNode) {
                                window.dropdown.parentNode.removeChild(window.dropdown);
                                window.dropdown = null;
                            }
                        });
                    });
                }
            })
            .catch(function(error) {
                console.error('드롭다운 옵션 로드 실패:', error);
                alert('드롭다운 옵션을 불러오는데 실패했습니다: ' + error.message);
            });
    }
  }
  
  // Sticky 헤더 기능 초기화
  function initializeStickyHeader() {
      console.log('Sticky 헤더 초기화 시작');
      
      const tableView = document.getElementById('tableView');
      const table = document.getElementById('entryTable');
      
      if (!tableView || !table) {
          console.error('테이블 요소를 찾을 수 없습니다.');
          return;
      }
      
      console.log('테이블 요소 찾음:', { tableView: !!tableView, table: !!table });
      
      // 기존 스크롤 이벤트 리스너 제거
      const newTableView = tableView.cloneNode(true);
      tableView.parentNode.replaceChild(newTableView, tableView);
      
      // 새로운 tableView 참조 가져오기
      const updatedTableView = document.getElementById('tableView');
      const updatedTable = document.getElementById('entryTable');
      
      if (!updatedTableView || !updatedTable) {
          console.error('업데이트된 테이블 요소를 찾을 수 없습니다.');
          return;
      }
      
      // 현재 스크롤 위치 확인 및 sticky 클래스 강제 적용
      const thead = updatedTable.querySelector('thead');
      if (thead) {
          const scrollTop = updatedTableView.scrollTop;
          console.log('현재 스크롤 위치:', scrollTop);
          
          // 스크롤이 있을 때 sticky 클래스 강제 적용
          if (scrollTop > 0) {
              console.log('thead 요소:', thead);
              console.log('sticky 클래스 추가');
              thead.classList.add('sticky');
              thead.classList.remove('out-of-view');
              console.log('스크롤 위치에 따라 sticky 클래스 강제 적용');
          } else {
              thead.classList.remove('sticky');
              thead.classList.remove('out-of-view');
              console.log('스크롤 위치에 따라 sticky 클래스 제거');
          }
      }
      
      // 테이블 컨테이너에 스크롤 이벤트 리스너 추가
      updatedTableView.addEventListener('scroll', function() {
          const thead = updatedTable.querySelector('thead');
          if (!thead) {
              console.log('thead 요소를 찾을 수 없습니다.');
              return;
          }
          
          const scrollTop = updatedTableView.scrollTop;
          console.log('스크롤 이벤트:', { scrollTop, theadClasses: thead.className });
          
          // 스크롤이 있을 때 sticky 적용
          if (scrollTop > 0) {
              console.log('thead 요소:', thead);
              console.log('sticky 클래스 추가');
              thead.classList.add('sticky');
              thead.classList.remove('out-of-view');
              console.log('sticky 클래스 추가 후:', thead.className);
          } else {
              console.log('sticky 클래스 제거');
              // 스크롤이 없을 때는 기본 상태로 복원
              thead.classList.remove('sticky');
              thead.classList.remove('out-of-view');
              console.log('sticky 클래스 제거 후:', thead.className);
          }
      });
      
      // 윈도우 스크롤 이벤트도 추가하여 테이블이 뷰포트를 벗어날 때 처리
      window.addEventListener('scroll', function() {
          const thead = updatedTable.querySelector('thead');
          if (!thead) return;
          
          const tableViewRect = updatedTableView.getBoundingClientRect();
          
          // 테이블이 뷰포트를 벗어났는지 확인
          const isTableOutOfView = (
              tableViewRect.bottom < 0 ||
              tableViewRect.top > window.innerHeight
          );
          
          // 테이블이 뷰포트를 벗어났을 때 sticky 제거
          if (isTableOutOfView) {
              thead.classList.remove('sticky');
              thead.classList.add('out-of-view');
          } else {
              thead.classList.remove('out-of-view');
          }
      });
      
      // 윈도우 리사이즈 시 헤더 위치 재조정
      window.addEventListener('resize', function() {
          const thead = updatedTable.querySelector('thead');
          if (thead && thead.classList.contains('sticky')) {
              // sticky 상태 유지하되 위치 재조정
              const tableViewRect = updatedTableView.getBoundingClientRect();
              
              const isTableOutOfView = (
                  tableViewRect.bottom < 0 ||
                  tableViewRect.top > window.innerHeight
              );
              
              if (isTableOutOfView) {
                  thead.classList.remove('sticky');
                  thead.classList.add('out-of-view');
              } else {
                  thead.classList.remove('out-of-view');
              }
          }
      });
      
      console.log('Sticky 헤더 초기화 완료');
  }
  
  function bindTableCellEvents() {
      document.querySelectorAll('td[data-field]').forEach(function(td) {
          const type = td.getAttribute('data-field');
          const dataType = td.getAttribute('data-type');
          
          if (dataType === 'datetime') {
              const input = td.querySelector('input[type="date"]');
              if (input) {
                  input.onchange = function() {
                      const id = td.parentElement.getAttribute('data-id');
                      const newValue = input.value;
                      
                      // 새 행인 경우
                      if (id && id.startsWith('temp_')) {
                          saveNewRowField(td.parentElement, type, newValue);
                      } else {
                          // 기존 행인 경우
                          fetch('/600/update/', {
                              method: 'POST',
                              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                              body: 'id=' + id + '&field=' + type + '&value=' + encodeURIComponent(newValue)
                          }).then(function(response) {
                              return response.json();
                          }).then(function(data) {
                              if (!data.success) alert('수정 실패: ' + data.error);
                              // 필요시 테이블/보드 갱신
                              refreshCalendarSettings();
                          });
                      }
                  };
              } else {
                  // input이 없는 경우 클릭 시 생성
                  td.onclick = function() {
                      if (td.querySelector('input')) return;
                      td.style.width = td.offsetWidth + 'px';
                      
                      const oldValue = td.innerText.trim();
                      const id = td.parentElement.getAttribute('data-id');
                      
                      const input = document.createElement('input');
                      input.type = 'date';
                      input.value = oldValue ? oldValue.slice(0,10) : '';
                      input.className = 'table-edit-input';
                      input.style.position = 'absolute';
                      input.style.left = '0';
                      input.style.top = '0';
                      input.style.width = 'max-content';
                      input.style.minWidth = '100%';
                      input.style.background = '#fffbe6';
                      input.style.zIndex = '10';
                      input.style.border = 'none';
                      input.style.fontSize = 'inherit';
                      input.style.fontFamily = 'inherit';
                      input.style.lineHeight = 'inherit';
                      input.style.padding = '0';
                      input.style.margin = '0';
                      
                      td.appendChild(input);
                      input.focus();
                      
                      input.onblur = function() {
                          const newValue = input.value;
                          td.innerText = newValue;
                          td.style.width = '';
                          
                          // 새 행인 경우
                          if (id && id.startsWith('temp_')) {
                              saveNewRowField(td.parentElement, type, newValue);
                          } else {
                              // 기존 행인 경우
                              fetch('/600/update/', {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                              }).then(function(response) {
                                  return response.json();
                              }).then(function(data) {
                                  if (!data.success) alert('수정 실패: ' + (data.error || ''));
                              }).catch(function(error) {
                                  console.error('업데이트 중 오류:', error);
                              });
                          }
                      };
                      
                      input.onkeydown = function(e) {
                          if (e.key === 'Enter') input.blur();
                          if (e.key === 'Escape') restoreCell(oldValue);
                      };
                  };
              }
          } 
          // 드롭다운 타입이거나 지역/상세지역 필드인 경우
          else if(dataType === 'dropdown' || dataType === 'region' || dataType === 'region_detail' || type === '지역' || type === '상세지역') {
              td.style.cursor = 'pointer';
              td.onclick = function(e) {
                  e.stopPropagation();
                  
                  const id = td.parentElement.getAttribute('data-id');
                  
                  if(dataType === 'region' || type === '지역') {
                      // 회사명 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                      const currentValue = (type === '회사명') ? 
                          (td.querySelector('.name-text')?.innerText.trim() || '') : 
                          td.innerText.trim();
                      const regionValue = td.parentElement.querySelector('td[data-field="지역"]');
                      const regionText = regionValue ? 
                          (regionValue.getAttribute('data-field') === '회사명' ? 
                              (regionValue.querySelector('.name-text')?.innerText.trim() || '') : 
                              regionValue.innerText.trim()) : '';
                      openDropdown(td, 'region', id, currentValue, regionText);
                  } else if(dataType === 'region_detail' || type === '상세지역') {
                      console.log('상세지역 드롭다운 처리');
                      const regionTd = td.parentElement.querySelector('td[data-field="지역"]');
                      const regionValue = regionTd ? 
                          (regionTd.getAttribute('data-field') === '회사명' ? 
                              (regionTd.querySelector('.name-text')?.innerText.trim() || '') : 
                              regionTd.innerText.trim()) : '';
                      const currentValue = (type === '회사명') ? 
                          (td.querySelector('.name-text')?.innerText.trim() || '') : 
                          td.innerText.trim();
                      console.log('상세지역 드롭다운 파라미터:', {regionValue, currentValue, id});
                      // openDropdown(td, type, id, currentId, currentSubregion) 형식에 맞춰 호출
                      openDropdown(td, 'region_detail', id, regionValue, currentValue);
                  } else if(dataType === 'dropdown') {
                      console.log('일반 드롭다운 처리');
                      openDropdown(td, type, id, td.getAttribute('data-value'));
                  }
              };
          } else {
              td.onclick = function() {
                  if (td.querySelector('input')) return;
                  td.style.width = td.offsetWidth + 'px';
                  if(type === '회사명') {
                      // ...버튼 이벤트 항상 바인딩
                      const moreBtn = td.querySelector('.more-btn');
                      if (moreBtn) {
                          moreBtn.onclick = function(e) {
                              e.stopPropagation();
                              const tr = td.closest('tr');
                              const id = tr.getAttribute('data-id');
                              if (!id) { alert('ID 정보가 없습니다.'); return; }
                              fetch('/600/get_row_details/' + id + '/')
                                  .then(r => r.json())
                                  .then(function(data) {
                                      if (data.success) showDetailModal(data.row_data, data.row_id);
                                      else alert('상세정보 불러오기 실패: ' + (data.error || ''));
                                  })
                                  .catch(function(err) {
                                      alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                                      console.error(err);
                                  });
                          };
                      }
                      td.onclick = function(e) {
                          if (e.target.classList.contains('more-btn')) return;
                          if (td.querySelector('input')) return;
                          td.style.width = td.offsetWidth + 'px';
                          const nameDiv = td.querySelector('.name-text');
                          if (!nameDiv) return;
                          const oldValue = nameDiv.innerText;
                          const id = td.parentElement.getAttribute('data-id');
                          const input = document.createElement('input');
                          input.type = 'text';
                          input.value = oldValue;
                          input.className = 'table-edit-input';
                          nameDiv.innerHTML = '';
                          nameDiv.appendChild(input);
                          const moreBtnWrapper = td.querySelector('.more-btn-wrapper');
                          if (moreBtnWrapper) moreBtnWrapper.style.visibility = 'hidden';
                          input.focus();
                          function restoreCell(value) {
                              td.innerHTML = `
                                <div class="name-container">
                                  <div class="name-text">${value}</div>
                                  <div class="more-btn-wrapper"><div class="more-btn" style="cursor:pointer;">⋯</div></div>
                                </div>
                              `;
                              // ...버튼 이벤트 재바인딩
                              const newMoreBtn = td.querySelector('.more-btn');
                              if (newMoreBtn) {
                                  newMoreBtn.onclick = function(e) {
                                      e.stopPropagation();
                                      const tr = td.closest('tr');
                                      const id = tr.getAttribute('data-id');
                                      if (!id) { alert('ID 정보가 없습니다.'); return; }
                                      fetch('/600/get_row_details/' + id + '/')
                                          .then(r => r.json())
                                          .then(function(data) {
                                              if (data.success) showDetailModal(data.row_data, data.row_id);
                                              else alert('상세정보 불러오기 실패: ' + (data.error || ''));
                                          })
                                          .catch(function(err) {
                                              alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                                              console.error(err);
                                          });
                                  };
                              }
                              // td.onclick도 재바인딩 (more-btn 체크)
                              td.onclick = function(e) {
                                  if (e.target.classList.contains('more-btn')) return;
                                  if (td.querySelector('input')) return;
                                  td.style.width = td.offsetWidth + 'px';
                                  const nameDiv = td.querySelector('.name-text');
                                  if (!nameDiv) return;
                                  const oldValue = nameDiv.innerText;
                                  const id = td.parentElement.getAttribute('data-id');
                                  const input = document.createElement('input');
                                  input.type = 'text';
                                  input.value = oldValue;
                                  input.className = 'table-edit-input';
                                  nameDiv.innerHTML = '';
                                  nameDiv.appendChild(input);
                                  const moreBtnWrapper = td.querySelector('.more-btn-wrapper');
                                  if (moreBtnWrapper) moreBtnWrapper.style.visibility = 'hidden';
                                  input.focus();
                                  input.onblur = function() {
                                      const newValue = input.value;
                                      restoreCell(newValue);
                                      if (id && id.startsWith('temp_')) {
                                          saveNewRowField(td.parentElement, '회사명', newValue);
                                      } else {
                                          fetch('/600/update/', {
                                              method: 'POST',
                                              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                              body: 'id=' + id + '&field=회사명&value=' + encodeURIComponent(newValue)
                                          });
                                      }
                                  };
                                  input.onkeydown = function(e) {
                                      if (e.key === 'Enter') input.blur();
                                      if (e.key === 'Escape') restoreCell(oldValue);
                                  };
                              };
                              td.style.width = '';
                          }
                          input.onblur = function() {
                              const newValue = input.value;
                              restoreCell(newValue);
                              if (id && id.startsWith('temp_')) {
                                  saveNewRowField(td.parentElement, '회사명', newValue);
                              } else {
                                  fetch('/600/update/', {
                                      method: 'POST',
                                      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                      body: 'id=' + id + '&field=회사명&value=' + encodeURIComponent(newValue)
                                  });
                              }
                          };
                          input.onkeydown = function(e) {
                              if (e.key === 'Enter') input.blur();
                              if (e.key === 'Escape') restoreCell(oldValue);
                          };
                      };
                  } else {
                      // 일반 텍스트 필드들 처리
                      // 회사명 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                      const oldValue = (type === '회사명') ? 
                          (td.querySelector('.name-text')?.innerText || '') : 
                          td.innerText;
                      const id = td.parentElement.getAttribute('data-id');
                      
                      let inputType = 'text';
                      // 날짜 필드들은 date input 사용
                      if (["TA","미팅","F/U 일정"].includes(type) || dataType === 'datetime') {
                          inputType = 'date';
                      }
                      
                      const input = document.createElement('input');
                      input.type = inputType;
                      // 매출 필드라면 한글 단위로 표시, 아니면 기존 값
                      if (type === '매출' || type.includes('매출')) {
                          const raw = td.getAttribute('data-raw');
                          let initialValue = '';
                          if (raw && !isNaN(parseInt(raw, 10))) {
                              initialValue = formatNumberWithComma(parseInt(raw, 10));
                          }
                          input.value = initialValue;
                          input.oninput = function(e) {
                              // 숫자만 추출 후 콤마 포맷팅
                              let val = this.value.replace(/[^0-9]/g, '');
                              this.value = formatNumberWithComma(val);
                          };
                          input.onblur = function() {
                              const cleanValue = removeCommaFromNumber(this.value);
                              updateCellValue(id, type, cleanValue, td);
                          };
                      } else {
                          input.value = (inputType==='date' && oldValue) ? oldValue.trim().slice(0,10) : oldValue.trim();
                          input.onblur = function() {
                              const newValue = input.value;
                              if(type === '회사명') {
                                  const nameTextDiv = td.querySelector('.name-text');
                                  if(nameTextDiv) nameTextDiv.innerText = newValue;
                                  if(input.parentNode) input.parentNode.removeChild(input);
                              } else {
                                  td.innerText = newValue;
                              }
                              td.style.width = '';
                              fetch('/600/update/', {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                              }).then(function(response) {
                                  return response.json();
                              }).then(function(data) {
                                  if (!data.success) alert('수정 실패: ' + (data.error || ''));
                              }).catch(function(error) {
                                  console.error('업데이트 중 오류:', error);
                              });
                          };
                      }
                      input.className = 'table-edit-input';
                      td.innerHTML = '';
                      td.appendChild(input);
                      input.focus();
                      if(inputType === 'text') input.select();
                      
                      // input 높이 자동 조정 함수
                      function adjustInputHeight() {
                          if (inputType === 'text' && !(type === '매출' || type.includes('매출'))) {
                              // 텍스트 길이에 따라 높이 조정
                              const textLength = input.value.length;
                              if (textLength > 50) {
                                  const lines = Math.ceil(textLength / 50);
                                  const newHeight = Math.min(36 + (lines - 1) * 20, 200);
                                  input.style.height = newHeight + 'px';
                              } else {
                                  input.style.height = '36px';
                              }
                          }
                      }
                      
                      // 초기 높이 조정
                      adjustInputHeight();
                      
                      // 입력 시 높이 조정
                      if (inputType === 'text' && !(type === '매출' || type.includes('매출'))) {
                          input.addEventListener('input', adjustInputHeight);
                      }
                      
                      input.onkeydown = function(e) {
                          if (e.key === 'Enter') input.blur();
                          if (e.key === 'Escape') {
                              if(type === '회사명') {
                                  const nameTextDiv = td.querySelector('.name-text');
                                  if(nameTextDiv) nameTextDiv.innerText = oldValue;
                                  if(input.parentNode) input.parentNode.removeChild(input);
                              } else {
                                  td.innerText = oldValue;
                              }
                              td.style.width = '';
                          }
                      };
                  }
              };
          }
      });
  }
  
  // 부분 업데이트 함수 - 특정 셀만 업데이트
  function updateTableCell(rowId, field, value) {
      const row = document.querySelector(`tr[data-id="${rowId}"]`);
      if (!row) return;
      
      const cell = row.querySelector(`td[data-field="${field}"]`);
      if (!cell) return;
      
      // 셀 내용만 업데이트 (전체 테이블 새로고침 없이)
      if (field === '매출' || field.includes('매출')) {
          cell.textContent = formatToKoreanCurrency(value);
      } else if (field === '개업년월') {
          // 개업년월 특별 처리
          try {
              if (typeof value === 'string' && value.startsWith('{')) {
                  const data = JSON.parse(value);
                  if (data.opening_date) {
                      cell.textContent = data.opening_date;
                  } else if (data.years_ago) {
                      cell.textContent = `${data.years_ago}년전`;
                  } else {
                      cell.textContent = value;
                  }
              } else {
                  cell.textContent = value;
              }
          } catch (e) {
              cell.textContent = value;
          }
      } else {
          cell.textContent = value;
      }
      
      // 실시간 동기화 (캘린더만)
      if (field === 'F/U 일정' && window.calendar) {
          window.calendar.refetchEvents();
      }
  }
  
  // 기존 refreshTable 함수를 최적화된 버전으로 수정
  function refreshTable() {
      console.log('refreshTable 함수 시작');
      
      // 현재 스크롤 위치 저장
      const tableView = document.getElementById('tableView');
      const scrollTop = tableView ? tableView.scrollTop : 0;
      const scrollLeft = tableView ? tableView.scrollLeft : 0;
      
      fetch('/600/entry_table_partial/')
      .then(r => {
          console.log('fetch 응답 상태:', r.status);
          if (!r.ok) {
              throw new Error('Network response was not ok: ' + r.status);
          }
          return r.text();
      })
      .then(html => {
          console.log('HTML 받음, 길이:', html.length);
          const temp = document.createElement('div');
          temp.innerHTML = html;
          const newTable = temp.querySelector('#entryTable');
          console.log('새 테이블 찾음:', !!newTable);
          
          if (newTable) {
              const currentTable = document.getElementById('entryTable');
              console.log('현재 테이블 찾음:', !!currentTable);
              
              if (currentTable) {
                  currentTable.innerHTML = newTable.innerHTML;
                  console.log('테이블 내용 교체 완료');
                  
                  // 스크롤 위치 복원
                  const tableView = document.getElementById('tableView');
                  if (tableView) {
                      tableView.scrollTop = scrollTop;
                      tableView.scrollLeft = scrollLeft;
                  }
                  
                  bindTableCellEvents(); // 테이블 이벤트 복구
                  console.log('테이블 이벤트 바인딩 완료');
                  
                  // 컬럼 드래그앤드롭 재초기화
                  if (typeof reinitializeDragDrop === 'function') {
                      reinitializeDragDrop();
                      console.log('드래그앤드롭 재초기화 완료');
                  }
                  
                  // 정렬/필터 데이터 재초기화
                  if (typeof initializeTableData === 'function') {
                      initializeTableData();
                      console.log('테이블 데이터 초기화 완료');
                  }
                  
                  // 현재 필터 상태 재적용
                  if (window.filters && Object.keys(window.filters).length > 0) {
                      Object.entries(window.filters).forEach(([column, filterValue]) => {
                          // 필터 입력창에 값 복원
                          const filterInput = document.querySelector(`input[data-column="${column}"]`);
                          if (filterInput) {
                              filterInput.value = filterValue;
                          }
                          
                          // 필터 재적용
                          if (window.originalRows) {
                              window.originalRows.forEach(row => {
                                  let shouldShow = true;
                                  
                                  for (const [filterColumn, filterVal] of Object.entries(window.filters)) {
                                      const cellValue = getCellValue(row, filterColumn).toLowerCase();
                                      if (!cellValue.includes(filterVal)) {
                                          shouldShow = false;
                                          break;
                                      }
                                  }
                                  
                                  row.style.display = shouldShow ? '' : 'none';
                              });
                          }
                      });
                      console.log('필터 상태 재적용 완료');
                  }
                  
                  // 현재 정렬 상태 재적용
                  if (window.currentSort && window.currentSort.column) {
                      if (typeof sortTable === 'function') {
                          sortTable(window.currentSort.column, window.currentSort.direction);
                          console.log('정렬 상태 재적용 완료');
                      }
                  }
                  
                  if (typeof updateFilterStatus === 'function') {
                      updateFilterStatus();
                      console.log('필터 상태 업데이트 완료');
                  }
                  
                  // Sticky 헤더 재초기화 - 여러 번 시도
                  if (typeof initializeStickyHeader === 'function') {
                      // 즉시 실행
                      initializeStickyHeader();
                      console.log('Sticky 헤더 재초기화 완료');
                      
                      // 50ms 후 재시도
                      setTimeout(() => {
                          initializeStickyHeader();
                          console.log('Sticky 헤더 재초기화 1차 재시도 완료');
                      }, 50);
                      
                      // 150ms 후 재시도
                      setTimeout(() => {
                          initializeStickyHeader();
                          console.log('Sticky 헤더 재초기화 2차 재시도 완료');
                      }, 150);
                      
                      // 300ms 후 재시도
                      setTimeout(() => {
                          initializeStickyHeader();
                          console.log('Sticky 헤더 재초기화 3차 재시도 완료');
                      }, 300);
                  }
                  
                  // === pill 렌더링 추가 ===
                  renderDropdownPills();
                  
                  console.log('refreshTable 완료');
              } else {
                  console.error('현재 테이블을 찾을 수 없음');
              }
          } else {
              console.error('새 테이블을 찾을 수 없음');
          }
      })
      .catch(error => {
          console.error('refreshTable 오류:', error);
          // 실패 시 페이지 새로고침으로 폴백
          console.log('페이지 새로고침으로 폴백');
          location.reload();
      });
  }
  
  
  // 새로운 필드 업데이트 함수
  function updateRowField(rowId, field, value) {
      fetch('/600/update/', {
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: 'id=' + encodeURIComponent(rowId) + '&field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(value)
      })
      .then(function(response) {
          return response.json();
      })
      .then(function(data) {
          if (!data.success) {
              alert('수정 실패: ' + data.error);
              return;
          }
          // datetime 타입 속성이 수정된 경우 캘린더 새로고침
          if (window.ATTR_FIELDS) {
              const attr = window.ATTR_FIELDS.find(a => a.name === field);
              if ((attr && attr.type === 'datetime') || field.includes('일') || field.includes('날짜') || field.includes('시간')) {
                  if (window.calendar) window.calendar.refetchEvents();
              }
          }
          // 테이블과 칸반보드 실시간 업데이트
          if (typeof refreshTable === 'function') {
              refreshTable();
          }
          
          // 칸반보드 실시간 업데이트 - 현재 칸반보드 속성과 일치하는 경우
          const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
              document.getElementById('kanbanAttributeSelect').value : 
              window.SELECTED_KANBAN_ATTR || window.kanbanAttribute;
              
          if (currentKanbanAttr && field === currentKanbanAttr) {
              if (typeof refreshKanban === 'function') {
                  refreshKanban();
              }
          }
      })
      .catch(function(error) {
          console.error('업데이트 오류:', error);
          alert('수정 실패: 네트워크 오류');
      });
  }
  
  
  // 새 행용 Attribute 시스템 이벤트 바인딩
  function bindNewRowAttributeEvents(tr) {
      tr.querySelectorAll('td[data-field]').forEach(function(td) {
          const field = td.getAttribute('data-field');
          const type = td.getAttribute('data-type');
          
          console.log(`새 행 필드 "${field}" 이벤트 바인딩, type: ${type}`);
          
          // datetime 타입 필드들
          if (type === 'datetime') {
              const input = td.querySelector('input[type="date"]');
              if (input) {
                  input.onchange = function() {
                      const newValue = input.value;
                      console.log(`새 행 datetime 필드 "${field}" 값 변경:`, newValue);
                      // 새 행 필드 저장
                      saveNewRowField(tr, field, newValue);
                  };
              }
          }
          // dropdown 타입이나 특수 지역 필드들
          else if(type === 'dropdown' || field === '지역' || field === '상세지역') {
              td.style.cursor = 'pointer';
              td.onclick = function(e) {
                  console.log(`새 행 드롭다운 클릭됨 - 필드: ${field}, type: ${type}`);
                  e.stopPropagation();
                  
                  let dropdownType = '';
                  if(type === 'dropdown') {
                      // 필드명을 그대로 사용 (영어 매핑 제거)
                      dropdownType = field;
                      console.log(`dropdown 타입: ${field}`);
                  } else if(field === '지역') {
                      dropdownType = 'region';
                      console.log('지역 드롭다운으로 설정');
                  } else if(field === '상세지역') {
                      dropdownType = 'region_detail';
                      console.log('상세지역 드롭다운으로 설정');
                  }
                  
                  if(dropdownType) {
                      // 회사명 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                      const currentValue = (field === '회사명') ? 
                          (td.querySelector('.name-text')?.innerText || '') : 
                          (td.innerText || '');
                      const currentSubregion = dropdownType === 'region_detail' ? 
                          tr.querySelector('td[data-field="상세지역"]').innerText : '';
                      
                      // 새 행용 드롭다운 열기
                      openNewRowAttributeDropdown(td, dropdownType, currentValue, currentSubregion, tr);
                  }
              };
          }
          // 회사명 필드 특별 처리
          else if(field === '회사명') {
              td.onclick = function(e) {
                  e.stopPropagation();
                  if(e.target.classList.contains('more-btn')) return;
                  
                  const nameTextDiv = td.querySelector('.name-text');
                  const oldValue = nameTextDiv.innerText;
                  
                  const input = document.createElement('input');
                  input.type = 'text';
                  input.value = oldValue;
                  input.className = 'table-edit-input';
                  input.style.position = 'absolute';
                  input.style.left = '0';
                  input.style.top = '0';
                  input.style.width = 'max-content';
                  input.style.minWidth = '100%';
                  input.style.background = '#fffbe6';
                  input.style.zIndex = '10';
                  input.style.border = 'none';
                  input.style.fontSize = 'inherit';
                  input.style.fontFamily = 'inherit';
                  input.style.lineHeight = 'inherit';
                  input.style.padding = '0';
                  input.style.margin = '0';
                  
                  td.appendChild(input);
                  input.focus();
                  input.select();
                  
                  function restoreCell(newValue) {
                      nameTextDiv.innerText = newValue;
                      if(input.parentNode) input.parentNode.removeChild(input);
                  }
                  
                  input.onblur = function() {
                      const newValue = input.value;
                      restoreCell(newValue);
                      console.log(`새 행 회사명 필드 값 변경:`, newValue);
                      // 새 행 필드 저장
                      saveNewRowField(tr, field, newValue);
                  };
                  
                  input.onkeydown = function(e) {
                      if (e.key === 'Enter') input.blur();
                      if (e.key === 'Escape') restoreCell(oldValue);
                  };
              };
          }
          // 일반 텍스트 필드들
          else {
              td.onclick = function(e) {
                  e.stopPropagation();
                  const oldValue = td.innerText;
                  
                  let inputType = 'text';
                  // 날짜 필드들은 date input 사용
                  if (["TA","미팅","F/U 일정"].includes(field) || type === 'datetime') {
                      inputType = 'date';
                  }
                  
                  const input = document.createElement('input');
                  input.type = inputType;
                  input.value = (inputType==='date' && oldValue) ? oldValue.trim().slice(0,10) : oldValue.trim();
                  input.className = 'table-edit-input';
                  
                  td.innerHTML = '';
                  td.appendChild(input);
                  input.focus();
                  if(inputType === 'text') input.select();
                  
                  input.onblur = function() {
                      const newValue = input.value;
                      // 회사명 필드인 경우 .name-text 업데이트, 다른 필드는 td.innerText 업데이트
                      if(type === '회사명') {
                          const nameTextDiv = td.querySelector('.name-text');
                          if(nameTextDiv) nameTextDiv.innerText = newValue;
                          if(input.parentNode) input.parentNode.removeChild(input);
                      } else {
                          td.innerText = newValue;
                      }
                      // 편집 종료 시 td width 해제
                      td.style.width = '';
                      
                      // 서버에 업데이트
                      fetch('/600/update/', {
                          method: 'POST',
                          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                          body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                      }).then(function(response) {
                          return response.json();
                      }).then(function(data) {
                          if (!data.success) alert('수정 실패: ' + (data.error || ''));
                      }).catch(function(error) {
                          console.error('업데이트 중 오류:', error);
                      });
                  };
                  
                  input.onkeydown = function(e) {
                      if (e.key === 'Enter') input.blur();
                      if (e.key === 'Escape') { 
                          // 회사명 필드인 경우 .name-text 복원, 다른 필드는 td.innerText 복원
                          if(type === '회사명') {
                              const nameTextDiv = td.querySelector('.name-text');
                              if(nameTextDiv) nameTextDiv.innerText = oldValue;
                              if(input.parentNode) input.parentNode.removeChild(input);
                          } else {
                              td.innerText = oldValue;
                          }
                          td.style.width = '';
                      }
                  };
              };
          }
      });
  }
  
  // 새 행 필드 값 저장 함수 (수정됨)
  function saveNewRowField(tr, field, value) {
      const currentId = tr.getAttribute('data-id');
      console.log(`새 행 필드 저장: ${field} = ${value}, 현재 ID: ${currentId}`);
      
      // 매출 필드인 경우 한국어 단위를 숫자로 변환
      let processedValue = value;
      if (field === '매출' || field.includes('매출')) {
          processedValue = parseKoreanCurrency(value).toString();
      }
      
      // 임시 ID인 경우 (새 행 생성)
      if (currentId && currentId.startsWith('temp_')) {
          console.log('새 행 생성 중...');
          fetch('/600/create_new_row/', {
              method: 'POST',
              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
              body: 'field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(processedValue)
          }).then(function(response) {
              console.log(`새 행 생성 응답 상태:`, response.status);
              return response.json();
          }).then(function(data) {
              console.log(`새 행 생성 응답:`, data);
              if (data.success && data.id) {
                  // 임시 ID를 실제 ID로 변경
                  tr.setAttribute('data-id', data.id);
                  tr.removeAttribute('data-is-new');
                  console.log(`새 행 ID 업데이트: ${currentId} -> ${data.id}`);
                  
                  // 실시간 동기화
                  syncTableAndKanban(field);
                  
                  // F/U 일정 필드인 경우 캘린더 새로고침
                  if (field === 'F/U 일정' && window.calendar) {
                      window.calendar.refetchEvents();
                  }
              }
          }).catch(function(error) {
              console.error(`새 행 생성 중 오류:`, error);
              alert('새 행 생성 중 오류 발생: ' + error.message);
          });
      }
      // 실제 ID가 있는 경우 (기존 행 업데이트)
      else if (currentId && !currentId.startsWith('temp_')) {
          console.log('기존 행 업데이트 중...');
          fetch('/600/update_row_field/', {
              method: 'POST',
              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
              body: 'id=' + encodeURIComponent(currentId) + '&field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(processedValue)
          }).then(function(response) {
              console.log(`${field} 필드 업데이트 응답 상태:`, response.status);
              return response.json();
          }).then(function(data) {
              console.log(`${field} 필드 업데이트 응답:`, data);
              if (data.success) {
                  // 실시간 동기화
                  syncTableAndKanban(field);
                  
                  // F/U 일정 필드인 경우 캘린더 새로고침
                  if (field === 'F/U 일정' && window.calendar) {
                      window.calendar.refetchEvents();
                  }
              } else {
                  console.error(`${field} 필드 업데이트 실패:`, data.error);
                  alert('업데이트 실패: ' + (data.error || ''));
              }
          }).catch(function(error) {
              console.error(`${field} 필드 업데이트 중 오류:`, error);
              alert('업데이트 중 오류 발생: ' + error.message);
          });
      } else {
          console.error('유효하지 않은 행 ID:', currentId);
      }
  }
  
  // 새 행용 드롭다운 함수 (Attribute 시스템)
  function openNewRowAttributeDropdown(td, type, currentValue, currentSubregion, tr) {
      console.log('새 행 attribute 드롭다운 호출됨');
      console.log('파라미터:', {type, currentValue, currentSubregion});
      
      closeDropdown();
      dropdown = document.createElement('div');
      dropdown.className = 'dropdown-edit';
      dropdown.style.top = (td.getBoundingClientRect().top + window.scrollY + td.offsetHeight) + 'px';
      dropdown.style.left = (td.getBoundingClientRect().left + window.scrollX) + 'px';
      
      if(type === 'region') {
          // 지역 드롭다운 (하드코딩된 값들)
          var regionNames = ['서울','경기','인천','대구','부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
          let selectedRegion = currentValue || '서울';
          let html = '<div><b>지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
          regionNames.forEach(function(region) {
              html += '<li style="margin-bottom:2px;"><span data-region="'+region+'" style="cursor:pointer;'+(region==selectedRegion?'font-weight:bold;color:#007bff;':'')+'">'+region+'</span></li>';
          });
          html += '</ul></div>';
          dropdown.innerHTML = html;
          document.body.appendChild(dropdown);
          
          dropdown.querySelectorAll('span[data-region]').forEach(function(span) {
              span.onclick = function() {
                  selectedRegion = this.getAttribute('data-region');
                  td.innerHTML = `<div class="dropdown-pill" style="display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${selectedRegion}</div>`;
                  td.setAttribute('data-value', selectedRegion);
                  // 상세지역도 업데이트
                  var subTd = tr.querySelector('td[data-field="상세지역"]');
                  if(subTd) {
                      var regionMap = {
                          '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
                          '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
                          '인천': ['계양구','남동구','동구','미추홀구','부평구','서구','연수구','중구','강화군','옹진군'],
                          '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
                          '경북': ['포항시','경주시','김천시','안동시','구미시','영주시','영천시','상주시','문경시','경산시','군위군','의성군','청송군','영양군','영덕군','청도군','고령군','성주군','칠곡군','예천군','봉화군','울진군','울릉군'],
                          '경남': ['창원시','진주시','통영시','사천시','김해시','밀양시','거제시','양산시','의령군','함안군','창녕군','고성군','남해군','하동군','산청군','함양군','거창군','합천군'],
                          '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
                          '광주': ['동구','서구','남구','북구','광산구'],
                          '대전': ['동구','중구','서구','유성구','대덕구'],
                          '울산': ['중구','남구','동구','북구','울주군'],
                          '세종': ['세종특별자치시'],
                          '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
                          '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
                          '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
                          '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
                          '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군']
                      };
                      var firstSubregion = (regionMap[selectedRegion] || [])[0] || '';
                      subTd.innerText = firstSubregion;
                  }
                  closeDropdown();
                  // 지역 값 저장
                  saveNewRowField(tr, '지역', selectedRegion);
              };
          });
      } else if(type === 'region_detail') {
          // 상세지역 드롭다운 (하드코딩된 값들)
          var regionMap = {
              '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
              '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군']
          };
          var currentRegion = tr.querySelector('td[data-field="지역"]').innerText.trim();
          var subregions = regionMap[currentRegion] || [];
          let selectedSubregion = currentSubregion || '';
          let html = '<div><b>상세지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
          subregions.forEach(function(sub) {
              html += '<li style="margin-bottom:2px;"><span data-subregion="'+sub+'" style="cursor:pointer;padding:2px 4px;border-radius:3px;'+(sub==selectedSubregion?'font-weight:bold;color:#007bff;':'')+'">'+sub+'</span></li>';
          });
          html += '</ul></div>';
          dropdown.innerHTML = html;
          document.body.appendChild(dropdown);
          
          dropdown.querySelectorAll('span[data-subregion]').forEach(function(span) {
              span.onclick = function() {
                  selectedSubregion = this.getAttribute('data-subregion');
                  td.innerHTML = `<div class="dropdown-pill" style="display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${selectedSubregion}</div>`;
                  td.setAttribute('data-value', selectedSubregion);
                  closeDropdown();
                  // 상세지역 값 저장
                  saveNewRowField(tr, '상세지역', selectedSubregion);
              };
          });
      } else {
          // dropdown_options API를 사용하는 드롭다운 (구분, 영업진행, 가능성 등)
          fetch('/600/dropdown_options/?field=' + encodeURIComponent(type))
              .then(r => r.json())
              .then(function(data) {
                  if (data.options) {
                      const options = data.options;
                      const currentValue = td.getAttribute('data-value') || '';
                      
                      // 모달과 동일한 깔끔한 구조로 변경
                      let html = `<div style="padding: 8px; border-bottom: 1px solid #eee;"><b>${type} 선택</b></div>`;
                      
                      // 옵션 목록 컨테이너
                      html += '<div style="max-height: 150px; overflow-y: auto;">';
                      
                      options.forEach(function(opt) {
                          // 단일선택 값 처리
                          let isSelected = false;
                          const currentValue = td.getAttribute('data-value') || '';
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
                            <div class="dropdown-option-container" style="padding: 4px 8px; border-bottom: 1px solid #f0f0f0;">
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
                                  <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${opt.option}</span>
                                </div>
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
                              </div>
                            </div>
                          `;
                      });
                      html += '</div>';
                      // 새 옵션 추가 영역은 그대로 유지
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
                      window.dropdown.innerHTML = html;
                      document.body.appendChild(window.dropdown);
                      
                      // === 드롭다운 모달 이벤트 바인딩 추가 ===
                      bindDropdownModalEvents(window.dropdown, type, options);
                      
                      // 컬러피커 미리보기 클릭 시 input[type=color]을 해당 위치에 띄우기
                      window.dropdown.querySelectorAll('.color-preview').forEach(function(preview) {
                        preview.addEventListener('click', function(e) {
                          e.stopPropagation();
                          const colorInput = this.parentNode.querySelector('input[type=color][data-color-edit]');
                          const rect = this.getBoundingClientRect();
                          colorInput.style.display = 'block';
                          colorInput.style.position = 'fixed';
                          colorInput.style.left = rect.left + 'px';
                          colorInput.style.top = rect.top + 'px';
                          colorInput.focus();
                        });
                      });
                      window.dropdown.querySelectorAll('input[type=color][data-color-edit]').forEach(function(input) {
                        input.addEventListener('blur', function() {
                          setTimeout(() => { input.style.display = 'none'; }, 200);
                        });
                      });
                  }
              })
              .catch(function(error) {
                  console.error('드롭다운 옵션 로드 실패:', error);
              });
      }
      
      // 외부 클릭 시 드롭다운 닫기
      document.addEventListener('mousedown', function(e) {
          if(dropdown && !dropdown.contains(e.target)) { 
              closeDropdown(); 
              document.removeEventListener('mousedown', handler); 
          }
      });
  }
  
  // 새 행 드롭다운 항목에 이벤트 바인딩하는 함수
  function bindNewRowDropdownItemEvents(li, type, tr) {
      // 컬러피커 이벤트
      const colorInput = li.querySelector('input[data-color-edit]');
      if(colorInput) {
          colorInput.onchange = function(e){
              fetch('/600/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + colorInput.getAttribute('data-color-edit') + '&color=' + encodeURIComponent(colorInput.value), {
                  method: 'PUT'
              }).then(r => r.json()).then(data => {
                  if(data.success) {
                      // 색상 변경 즉시 반영
                      const span = li.querySelector('span[data-option-id]');
                      span.style.background = hexToRgba(colorInput.value, 0.18);
                      
                      // 실시간 동기화 - 드롭다운 옵션 색상 변경도 테이블과 칸반보드에 반영
                      syncTableAndKanban(type);
                  }
              }).catch(error => {
                  console.error('색상 변경 실패:', error);
              });
          };
      }
      
      // 삭제 버튼 이벤트
      const delBtn = li.querySelector('button[data-del]');
      if(delBtn) {
          delBtn.onclick = function(e){
              e.stopPropagation();
              if(confirm('삭제할까요?')) {
                  fetch('/600/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + delBtn.getAttribute('data-del'), {
                      method: 'DELETE'
                  }).then(r => r.json()).then(data => {
                      if(data.success) {
                          li.remove();
                          
                          // 실시간 동기화 - 드롭다운 옵션 삭제도 테이블과 칸반보드에 반영
                          syncTableAndKanban(type);
                      }
                  }).catch(error => {
                      console.error('삭제 실패:', error);
                      alert('삭제에 실패했습니다.');
                  });
              }
          };
      }
      
      // 수정 버튼 이벤트
      const editBtn = li.querySelector('button[data-edit]');
      if(editBtn) {
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
                  
                  fetch(`/600/dropdown_options/?field=${encodeURIComponent(type)}&id=${optionId}&name=${encodeURIComponent(newText)}`, {
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
                          syncTableAndKanban(type);
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
      }
  }
  
  // 테이블 초기화 시 외부 클릭 이벤트 리스너 추가
  document.addEventListener('click', function(event) {
      // 드롭다운이 열려있고, 클릭한 위치가 드롭다운 외부인 경우에만 닫기
      if (window.dropdown && !window.dropdown.contains(event.target)) {
          // 드롭다운을 여는 버튼을 클릭한 경우는 제외
          const clickedElement = event.target;
          const isDropdownButton = clickedElement.classList.contains('add-btn') || 
                                   clickedElement.onclick && clickedElement.onclick.toString().includes('openDropdown');
          
          if (!isDropdownButton) {
              closeDropdown();
          }
      }
  });
  
  // ESC 키로 드롭다운 닫기
  document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape' && window.dropdown) {
          closeDropdown();
      }
  });
  
  // 숫자 필드 업데이트 시 콤마 포맷팅 적용
  function updateCellValue(id, fieldName, value, element) {
      console.log('updateCellValue 호출:', {id, fieldName, value});
      
      // 새 행인 경우
      if (id && id.startsWith('temp_')) {
          saveNewRowField(element.parentElement, fieldName, value);
          return;
      }
      
      // 기존 행인 경우
      fetch('/600/update/', {
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: 'id=' + id + '&field=' + encodeURIComponent(fieldName) + '&value=' + encodeURIComponent(value)
      })
      .then(function(response) {
          return response.json();
      })
      .then(function(data) {
          if (!data.success) {
              alert('수정 실패: ' + (data.error || ''));
              return;
          }
          
          // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우에만 즉시 필터 적용
          if (window.currentStatusTab !== null && fieldName === window.statusAttributeName) {
              // 해당 행의 상태 셀 업데이트
              const row = document.querySelector(`tr[data-id="${id}"]`);
              if (row) {
                  const statusCell = row.querySelector(`td[data-field="${fieldName}"]`);
                  if (statusCell) {
                      // 새로운 값으로 data-value 업데이트
                      statusCell.setAttribute('data-value', value);
                      
                      // 상태 필터 즉시 재적용
                      setTimeout(() => {
                          if (typeof applyStatusFilter === 'function') {
                              applyStatusFilter();
                          }
                      }, 50);
                  }
              }
          }
          
          // 테이블과 칸반보드 새로고침
          if (typeof refreshTable === 'function') {
              refreshTable();
          }
          
          // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
          if (window.kanbanAttribute && fieldName === window.kanbanAttribute) {
              if (typeof refreshKanban === 'function') {
                  refreshKanban();
              }
          }
          
          // F/U 일정 필드인 경우 캘린더도 새로고침
          if (fieldName === 'F/U 일정' && window.calendar) {
              window.calendar.refetchEvents();
          }
          
          // 모든 필드 변경 시 캘린더 업데이트
          if (typeof refreshCalendar === 'function') {
              refreshCalendar();
          }
          
          // 드롭다운 옵션 동기화
          if (typeof syncTableAndKanban === 'function') {
              syncTableAndKanban(fieldName);
          }
      })
      .catch(function(error) {
          console.error('업데이트 중 오류:', error);
          alert('업데이트 중 오류가 발생했습니다.');
      });
  }
  
  // 테이블과 칸반보드 실시간 동기화 함수
  function syncTableAndKanban(fieldName) {
      // 드롭다운 옵션이 수정된 경우 모든 관련 셀 즉시 업데이트
      // 하드코딩 대신 동적으로 dropdown 속성명 추출
      const dropdownFields = (window.ATTR_FIELDS || [])
          .filter(attr => attr.attributeType_name === 'dropdown')
          .map(attr => attr.name);
      if (fieldName && dropdownFields.includes(fieldName)) {
          console.log('드롭다운 옵션 동기화 시작:', fieldName);
          
          // 서버에서 최신 옵션 정보 가져와서 모든 관련 셀 업데이트
          fetch('/600/dropdown_options/?field=' + encodeURIComponent(fieldName))
              .then(response => response.json())
              .then(data => {
                  if (data.options) {
                      console.log('최신 옵션 정보 로드됨:', data.options);
                      
                      // 해당 필드를 사용하는 모든 셀 찾기
                      const cells = document.querySelectorAll(`td[data-field="${fieldName}"]`);
                      console.log(`업데이트할 셀 개수: ${cells.length}`);
                      
                      cells.forEach(cell => {
                          const currentValue = cell.getAttribute('data-value');
                          const currentText = cell.textContent.trim();
                          
                          if (currentValue) {
                              try {
                                  // JSON 형태로 저장된 다중선택 값인지 확인
                                  const parsed = JSON.parse(currentValue);
                                  if (Array.isArray(parsed) && parsed.length > 0) {
                                      // 다중선택 값 처리 - 숫자 비교로 수정
                                      const selectedOptions = data.options.filter(opt => parsed.includes(Number(opt.id)));
                                      let htmlContent = '';
                                      selectedOptions.forEach((opt, index) => {
                                          const color = opt.color ? hexToRgba(opt.color, 0.18) : '#eee';
                                          htmlContent += `<div class="dropdown-pill" style="background:${color}; color:#333; display:block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; margin-bottom:2px;">${opt.option}</div>`;
                                      });
                                      
                                      if (htmlContent) {
                                          cell.innerHTML = htmlContent;
                                          cell.setAttribute('data-value', JSON.stringify(parsed));
                                      } else {
                                          cell.innerHTML = '<div style="color: #999; font-style: italic;">선택 없음</div>';
                                          cell.setAttribute('data-value', '');
                                      }
                                  } else if (Array.isArray(parsed) && parsed.length === 0) {
                                      // 빈 배열인 경우
                                      cell.innerHTML = '<div style="color: #999; font-style: italic;">선택 없음</div>';
                                      cell.setAttribute('data-value', '');
                                  } else {
                                      // 단일 선택 값 처리 (기존 로직)
                                      const option = data.options.find(opt => opt.id == currentValue);
                                      if (option) {
                                          console.log(`셀 업데이트: ${currentText} -> ${option.option} (색상: ${option.color})`);
                                          const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                                          cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                                          cell.setAttribute('data-value', option.id);
                                      } else {
                                          // data-value가 일치하지 않으면 텍스트로 찾기
                                          const textOption = data.options.find(opt => opt.option === currentText);
                                          if (textOption) {
                                              console.log(`텍스트로 셀 업데이트: ${currentText} (색상: ${textOption.color})`);
                                              const color = textOption.color ? hexToRgba(textOption.color, 0.18) : '#eee';
                                              cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${textOption.option}</div>`;
                                              cell.setAttribute('data-value', textOption.id);
                                          }
                                      }
                                  }
                              } catch (e) {
                                  // JSON 파싱 실패 시 단일 값으로 처리
                                  const option = data.options.find(opt => opt.id == currentValue);
                                  if (option) {
                                      console.log(`셀 업데이트: ${currentText} -> ${option.option} (색상: ${option.color})`);
                                      const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                                      cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                                      cell.setAttribute('data-value', option.id);
                                  }
                              }
                          }
                      });
                      
                      console.log('드롭다운 옵션 동기화 완료');
                  }
              })
              .catch(error => {
                  console.error('드롭다운 옵션 업데이트 실패:', error);
              });
      }
      
      // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우 새로고침
      const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
          document.getElementById('kanbanAttributeSelect').value : 
          window.SELECTED_KANBAN_ATTR;
      
      if (currentKanbanAttr && fieldName === currentKanbanAttr) {
          console.log('칸반보드 속성이 변경되어 새로고침합니다:', fieldName);
          if (typeof refreshKanban === 'function') {
              refreshKanban();
          }
      }
  }
  
  // CSRF 토큰 가져오기 함수
  function getCookie(name) {
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
  
  // 행 삭제 함수
  function deleteRow(rowId) {
      if (!confirm('이 행을 삭제하시겠습니까?\n\n삭제된 데이터는 복구할 수 없습니다.')) {
          return;
      }
      
      fetch('/600/delete_row/', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({
              row_id: rowId
          })
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              // 테이블에서 행 제거
              const row = document.querySelector(`tr[data-id="${rowId}"]`);
              if (row) {
                  row.remove();
              }
              
              // 칸반 보드와 캘린더 동기화
              syncTableAndKanban();
              
              alert('행이 성공적으로 삭제되었습니다.');
          } else {
              alert('오류: ' + data.error);
          }
      })
      .catch(error => {
          console.error('Error:', error);
          alert('행 삭제 중 오류가 발생했습니다.');
      });
  }
  
  // 매출 필드 실시간 변환 함수 (테이블용)
  function formatSalesInputRealtimeTable(input) {
      const value = input.value.replace(/[^\d]/g, '');
      const numericValue = parseInt(value) || 0;
      
      if (numericValue >= 1000000) {
          const convertedValue = Math.floor(numericValue / 10000);
          if (convertedValue >= 1) {
              input.value = convertedValue;
          } else {
              input.value = numericValue.toLocaleString();
          }
      } else if (numericValue > 0) {
          input.value = numericValue.toLocaleString();
      }
  }

  // 새로 만들기 버튼 이벤트 바인딩
  document.addEventListener('DOMContentLoaded', function() {
      const addRowBtn = document.getElementById('addRowBtn');
      let isAdding = false;
      
      if (addRowBtn) {
          addRowBtn.onclick = function() {
              if(isAdding) return;
              isAdding = true;

              // 현재 선택된 상태 탭 확인
              let statusField = null;
              let statusValue = null;
              
              if (window.currentStatusTab !== null && window.statusAttributeName) {
                  statusField = window.statusAttributeName;
                  statusValue = window.currentStatusTab;
                  console.log('상태 탭이 선택됨:', { field: statusField, value: statusValue });
              }

              // 서버에 새 행 생성 요청
              let requestBody = 'field=' + encodeURIComponent('회사명') + '&value=' + encodeURIComponent('새 항목');
              
              // 상태 필드가 있으면 추가
              if (statusField && statusValue) {
                  requestBody += '&status_field=' + encodeURIComponent(statusField) + '&status_value=' + encodeURIComponent(statusValue);
              }

              fetch('/600/create_new_row/', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: requestBody
              })
              .then(function(response) { 
                  if (!response.ok) {
                      throw new Error('Network response was not ok');
                  }
                  return response.json(); 
              })
              .then(function(data) {
                  if (data.success) {
                      console.log('새 행 생성 성공:', data);
                      // 기존 refreshTable 함수 사용
                      if (typeof refreshTable === 'function') {
                          refreshTable();
                      } else {
                          console.error('refreshTable 함수가 정의되지 않음');
                          location.reload();
                      }
                  } else {
                      console.error('새 행 생성 실패:', data.error);
                      alert('새 행 생성 실패: ' + (data.error || ''));
                  }
              })
              .catch(function(error) {
                  console.error('새 행 생성 중 오류:', error);
                  alert('새 행 생성 중 오류: ' + error.message);
              })
              .finally(function() {
                  isAdding = false;
              });
          };
      }
      
      // Sticky 헤더 초기화
      initializeStickyHeader();
      renderDropdownPills();
  });

  // 매출 셀 더블클릭/수정 시 한글 단위 → 숫자(콤마)로 입력
  function showNumberForEdit(input) {
      const value = input.value;
      const number = parseKoreanCurrency(value);
      input.value = formatNumberWithComma(number);
      input.select();
  }

  // === dropdown 속성명 동적 추출 함수 ===
  function getDropdownFields() {
      return (window.ATTR_FIELDS || [])
          .filter(attr => attr.attributeType_name === 'dropdown')
          .map(attr => attr.name);
  }

  // 기존 데이터 정리 함수
  function cleanupExistingData() {
      console.log('기존 데이터 정리 시작');
      // 모든 드롭다운 필드의 data-value를 확인하고 정리
      const dropdownFields = getDropdownFields();
      dropdownFields.forEach(field => {
          const cells = document.querySelectorAll(`td[data-field="${field}"]`);
          cells.forEach(cell => {
              const currentValue = cell.getAttribute('data-value');
              if (currentValue) {
                  try {
                      // JSON 형태인지 확인
                      const parsed = JSON.parse(currentValue);
                      if (Array.isArray(parsed) && parsed.length > 0) {
                          // 배열인 경우 첫 번째 값만 사용
                          console.log(`${field} 필드 정리: ${currentValue} -> ${parsed[0]}`);
                          cell.setAttribute('data-value', parsed[0]);
                          // UI도 업데이트
                          const optionId = parsed[0];
                          // 서버에서 옵션 정보 가져와서 UI 업데이트
                          fetch('/600/dropdown_options/?field=' + encodeURIComponent(field))
                              .then(response => response.json())
                              .then(data => {
                                  if (data.options) {
                                      const option = data.options.find(opt => opt.id == optionId);
                                      if (option) {
                                          const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                                          cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                                      }
                                  }
                              })
                              .catch(error => {
                                  console.error('옵션 정보 가져오기 실패:', error);
                              });
                      }
                  } catch (e) {
                      // JSON이 아닌 경우 그대로 유지
                      console.log(`${field} 필드 유지: ${currentValue}`);
                  }
              }
          });
      });
      console.log('기존 데이터 정리 완료');
  }

  // 페이지 로드 시 데이터 정리
  document.addEventListener('DOMContentLoaded', function() {
      // 기존 데이터 정리 함수 제거 - 다중선택 값들이 단일 값으로 변환되는 것을 방지
      // setTimeout(() => {
      //     cleanupExistingData();
      // }, 1000);
  });

  // === 다중선택 드롭다운 셀을 옵션명 pill로 변환하는 함수 ===
  function renderDropdownPills() {
      // 다중선택 드롭다운 필드 목록 동적 추출
      const dropdownFields = getDropdownFields();
      dropdownFields.forEach(field => {
          document.querySelectorAll(`td[data-field="${field}"]`).forEach(cell => {
              const currentValue = cell.getAttribute('data-value');
              if (!currentValue) {
                  cell.innerHTML = '<div style="color: #999; font-style: italic;">선택 없음</div>';
                  return;
              }
              let parsed = null;
              try {
                  parsed = JSON.parse(currentValue);
              } catch (e) {
                  parsed = currentValue;
              }
              fetch('/600/dropdown_options/?field=' + encodeURIComponent(field))
                  .then(response => response.json())
                  .then(data => {
                      if (!data.options) return;
                      let htmlContent = '';
                      if (Array.isArray(parsed)) {
                          const selectedOptions = data.options.filter(opt => parsed.includes(Number(opt.id)));
                          selectedOptions.forEach(opt => {
                              const color = opt.color ? hexToRgba(opt.color, 0.18) : '#eee';
                              htmlContent += `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; margin-bottom:2px;">${opt.option}</div>`;
                          });
                      } else {
                          const opt = data.options.find(opt => opt.id == parsed);
                          if (opt) {
                              const color = opt.color ? hexToRgba(opt.color, 0.18) : '#eee';
                              htmlContent = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${opt.option}</div>`;
                          }
                      }
                      cell.innerHTML = htmlContent || '<div style="color: #999; font-style: italic;">선택 없음</div>';
                  });
          });
      });
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
              fetch('/600/dropdown_options/', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'X-CSRFToken': getCsrfToken()
                  },
                  body: `field=${encodeURIComponent(fieldType)}&name=${encodeURIComponent(newOptionName)}&color=${encodeURIComponent('#007bff')}`
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
          colorInput.addEventListener('change', function(e) {
              e.stopPropagation();
              const optionId = this.getAttribute('data-color-edit');
              const newColor = this.value;
              fetch(`/600/dropdown_options/?field=${encodeURIComponent(fieldType)}&id=${optionId}&color=${encodeURIComponent(newColor)}`, {
                  method: 'PUT',
                  headers: {
                      'X-CSRFToken': getCsrfToken()
                  }
              })
              .then(response => response.json())
              .then(data => {
                  if (data.success) {
                      console.log('색상 변경 성공:', data);
                      const optionContainer = this.closest('.dropdown-option-container');
                      const dropdownItem = optionContainer.querySelector('.dropdown-item');
                      if (dropdownItem) {
                          dropdownItem.style.background = hexToRgba(newColor, 0.18);
                      }
                      syncTableAndKanban(fieldType);
                  } else {
                      alert('색상 변경 실패: ' + (data.error || ''));
                  }
              })
              .catch(error => {
                  console.error('색상 변경 실패:', error);
                  alert('색상 변경 중 오류가 발생했습니다: ' + error.message);
              });
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
                  
                  fetch(`/600/dropdown_options/?field=${encodeURIComponent(fieldType)}&id=${optionId}&name=${encodeURIComponent(newText)}`, {
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
                  fetch(`/600/dropdown_options/?field=${encodeURIComponent(fieldType)}&id=${optionId}`, {
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