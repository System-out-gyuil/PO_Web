// CSRF 토큰 가져오기 함수
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
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
                        const isSelected = opt.id == currentValue;
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
                                        justify-content: space-between;">
                              <span style="flex: 1;">${opt.option}</span>
                              <div class="option-controls" style="display: flex; gap: 4px; align-items: center;">
                                <input type="color" value="${opt.color||'#eeeeee'}" data-color-edit="${opt.id}" 
                                       style="width: 20px; height: 20px; border: none; cursor: pointer; border-radius: 2px;" title="색상 변경">
                                <button data-edit="${opt.id}" 
                                        style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px;" title="수정">✏️</button>
                                <button data-del="${opt.id}" 
                                        style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px;" title="삭제">🗑️</button>
                              </div>
                            </div>
                          </div>
                        `;
                    });
                    
                    html += '</div>';
                    
                    // 새 옵션 추가 영역
                    html += `<div style="border-top: 1px solid #eee; padding: 8px; background: #f8f9fa;">
                      <div style="display: flex; gap: 4px; align-items: center;">
                        <input type="text" placeholder="새 옵션 추가" 
                               style="flex: 1; padding: 4px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                        <button class="add-btn" 
                                style="padding: 4px 12px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">추가</button>
                      </div>
                    </div>`;
                    
                    window.dropdown.innerHTML = html;
                    
                    console.log('일반 드롭다운 HTML 생성 완료');
                    
                    // DOM에 추가
                    document.body.appendChild(window.dropdown);
                    
                    console.log('일반 드롭다운 DOM 추가 완료');
                    
                    // 옵션 선택 이벤트
                    window.dropdown.querySelectorAll('.dropdown-item[data-option-id]').forEach(function(item) {
                        const optionId = item.getAttribute('data-option-id');
                        const option = options.find(opt => opt.id == optionId);
                        
                        // 호버 효과 - 모달과 동일하게
                        item.addEventListener('mouseenter', function() {
                            if (!this.style.border.includes('#007bff')) {
                                this.style.background = this.style.background.replace('0.18', '0.3');
                            }
                        });
                        
                        item.addEventListener('mouseleave', function() {
                            if (!this.style.border.includes('#007bff')) {
                                this.style.background = this.style.background.replace('0.3', '0.18');
                            }
                        });
                        
                        // 클릭 이벤트
                        item.addEventListener('click', function(e) {
                            // 컨트롤 버튼 클릭은 제외
                            if (e.target.closest('.option-controls')) {
                                return;
                            }
                            
                            e.preventDefault();
                            e.stopPropagation();
                            
                            console.log('드롭다운 옵션 클릭됨:', {optionId, option: this.querySelector('span').innerText});
                            
                            // UI 업데이트
                            const label = this.querySelector('span').innerText;
                            const color = (option && option.color) ? option.color : '';
                            td.innerHTML = `<div class="dropdown-pill" style="background:${color ? hexToRgba(color, 0.18) : '#eee'}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${label}</div>`;
                            td.setAttribute('data-value', optionId);
                            
                            // 드롭다운 제거
                            if (window.dropdown && window.dropdown.parentNode) {
                              window.dropdown.parentNode.removeChild(window.dropdown);
                              window.dropdown = null;
                            }
                            
                            // 서버 업데이트
                            console.log('서버 업데이트 시작:', {id, type, optionId});
                            
                            // 새 행인 경우
                            if (id && id.startsWith('temp_')) {
                                saveNewRowField(td.parentElement, type, optionId);
                            } else {
                                // 기존 행인 경우
                                fetch('/600/update/', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                    body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(optionId)
                                })
                                .then(response => {
                                    console.log('서버 응답 상태:', response.status);
                                    return response.json();
                                })
                                .then(data => {
                                    console.log('서버 응답 데이터:', data);
                                    if (data.success) {
                                        // 실시간 동기화
                                        syncTableAndKanban(type);
                                        
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
                    
                    // 색상 변경 이벤트
                    window.dropdown.querySelectorAll('input[data-color-edit]').forEach(function(colorInput) {
                        colorInput.addEventListener('change', function(e) {
                            e.stopPropagation();
                            const optionId = this.getAttribute('data-color-edit');
                            const newColor = this.value;
                            
                            fetch('/600/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + optionId + '&color=' + encodeURIComponent(newColor), {
                                method: 'PUT'
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    // 색상 변경 즉시 반영
                                    const item = this.closest('.dropdown-item');
                                    if (item) {
                                        item.style.background = hexToRgba(newColor, 0.18);
                                    }
                                    
                                    // 실시간 동기화
                                    syncTableAndKanban(type);
                                }
                            })
                            .catch(error => {
                                console.error('색상 변경 실패:', error);
                            });
                        });
                    });
                    
                    // 삭제 버튼 이벤트
                    window.dropdown.querySelectorAll('button[data-del]').forEach(function(delBtn) {
                        delBtn.addEventListener('click', function(e) {
                            e.stopPropagation();
                            const optionId = this.getAttribute('data-del');
                            
                            if (confirm('이 옵션을 삭제하시겠습니까?')) {
                                fetch('/600/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + optionId, {
                                    method: 'DELETE'
                                })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        this.closest('.dropdown-option-container').remove();
                                        
                                        // 실시간 동기화
                                        syncTableAndKanban(type);
                                    }
                                })
                                .catch(error => {
                                    console.error('삭제 실패:', error);
                                    alert('삭제에 실패했습니다.');
                                });
                            }
                        });
                    });
                    
                    // 수정 버튼 이벤트
                    window.dropdown.querySelectorAll('button[data-edit]').forEach(function(editBtn) {
                        editBtn.addEventListener('click', function(e) {
                            e.stopPropagation();
                            const optionId = this.getAttribute('data-edit');
                            const span = this.closest('.dropdown-item').querySelector('span');
                            const oldText = span.innerText;
                            
                            // 텍스트를 입력 필드로 변경
                            const input = document.createElement('input');
                            input.type = 'text';
                            input.value = oldText;
                            input.style.cssText = 'flex: 1; border: 1px solid #007bff; border-radius: 3px; padding: 2px 4px; font-size: 12px;';
                            
                            span.replaceWith(input);
                            input.focus();
                            input.select();
                            
                            const handleSave = () => {
                                const newText = input.value.trim();
                                if (newText && newText !== oldText) {
                                    fetch('/600/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + optionId + '&name=' + encodeURIComponent(newText), {
                                        method: 'PUT'
                                    })
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.success) {
                                            // 수정된 내용 즉시 반영
                                            const newSpan = document.createElement('span');
                                            newSpan.style.cssText = 'flex: 1;';
                                            newSpan.innerText = newText;
                                            
                                            input.replaceWith(newSpan);
                                            
                                            // 실시간 동기화
                                            syncTableAndKanban(type);
                                        }
                                    })
                                    .catch(error => {
                                        console.error('수정 실패:', error);
                                        // 실패시 원래 값으로 복원
                                        const restoredSpan = document.createElement('span');
                                        restoredSpan.style.cssText = 'flex: 1;';
                                        restoredSpan.innerText = oldText;
                                        input.replaceWith(restoredSpan);
                                    });
                                } else {
                                    // 변경사항이 없으면 원래대로 복원
                                    const restoredSpan = document.createElement('span');
                                    restoredSpan.style.cssText = 'flex: 1;';
                                    restoredSpan.innerText = oldText;
                                    input.replaceWith(restoredSpan);
                                }
                            };
                            
                            const handleCancel = () => {
                                const cancelSpan = document.createElement('span');
                                cancelSpan.style.cssText = 'flex: 1;';
                                cancelSpan.innerText = oldText;
                                input.replaceWith(cancelSpan);
                            };
                            
                            input.addEventListener('keydown', function(ev) {
                                if (ev.key === 'Enter') {
                                    handleSave();
                                } else if (ev.key === 'Escape') {
                                    handleCancel();
                                }
                            });
                            
                            input.addEventListener('blur', handleCancel);
                        });
                    });
                    
                    // 새 옵션 추가 이벤트
                    const addBtn = window.dropdown.querySelector('.add-btn');
                    const addInput = window.dropdown.querySelector('input[type="text"]');
                    
                    const handleAdd = () => {
                        const newOptionName = addInput.value.trim();
                        if (newOptionName) {
                            fetch('/600/dropdown_options/?field=' + encodeURIComponent(type), {
                                method: 'POST',
                                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                body: 'name=' + encodeURIComponent(newOptionName)
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.id && data.option) {
                                    // 새로 추가된 옵션을 드롭다운에 동적으로 추가
                                    const optionsContainer = window.dropdown.querySelector('div[style*="max-height"]');
                                    const newOptionDiv = document.createElement('div');
                                    newOptionDiv.className = 'dropdown-option-container';
                                    newOptionDiv.style.cssText = 'padding: 4px 8px; border-bottom: 1px solid #f0f0f0;';
                                    newOptionDiv.innerHTML = `
                                      <div class="dropdown-item" data-option-id="${data.id}" 
                                           style="cursor: pointer; 
                                                  background: ${data.color ? hexToRgba(data.color, 0.18) : 'white'}; 
                                                  border-radius: 4px; 
                                                  padding: 6px 8px; 
                                                  margin-bottom: 4px;
                                                  border: 1px solid #ddd;
                                                  transition: all 0.2s;
                                                  display: flex;
                                                  align-items: center;
                                                  justify-content: space-between;">
                                        <span style="flex: 1;">${data.option}</span>
                                        <div class="option-controls" style="display: flex; gap: 4px; align-items: center;">
                                          <input type="color" value="${data.color||'#eeeeee'}" data-color-edit="${data.id}" 
                                                 style="width: 20px; height: 20px; border: none; cursor: pointer; border-radius: 2px;" title="색상 변경">
                                          <button data-edit="${data.id}" 
                                                  style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px;" title="수정">✏️</button>
                                          <button data-del="${data.id}" 
                                                  style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px;" title="삭제">🗑️</button>
                                        </div>
                                      </div>
                                    `;
                                    optionsContainer.appendChild(newOptionDiv);
                                    
                                    // 새로 추가된 옵션에 이벤트 바인딩
                                    const newItem = newOptionDiv.querySelector('.dropdown-item');
                                    newItem.addEventListener('click', function(e) {
                                        if (e.target.closest('.option-controls')) {
                                            return;
                                        }
                                        
                                        e.preventDefault();
                                        e.stopPropagation();
                                        
                                        td.innerHTML = `<div class="dropdown-pill" style="background:${this.style.background}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${this.innerText}</div>`;
                                        td.setAttribute('data-value', data.id);
                                        
                                        if (window.dropdown && window.dropdown.parentNode) {
                                          window.dropdown.parentNode.removeChild(window.dropdown);
                                          window.dropdown = null;
                                        }
                                        
                                        // 서버 업데이트
                                        if (id && id.startsWith('temp_')) {
                                            saveNewRowField(td.parentElement, type, data.id);
                                        } else {
                                            fetch('/600/update/', {
                                                method: 'POST',
                                                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                                body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(data.id)
                                            })
                                            .then(response => response.json())
                                            .then(data => {
                                                if (data.success) {
                                                    // 실시간 동기화
                                                    syncTableAndKanban(type);
                                                }
                                            });
                                        }
                                    });
                                    
                                    // 입력 필드 초기화
                                    addInput.value = '';
                                    
                                    // 실시간 동기화 - 새 옵션 추가도 반영
                                    syncTableAndKanban(type);
                                }
                            })
                            .catch(error => {
                                console.error('옵션 추가 실패:', error);
                                alert('옵션 추가에 실패했습니다.');
                            });
                        }
                    };
                    
                    addBtn.addEventListener('click', handleAdd);
                    addInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            handleAdd();
                        }
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
      
      // 테이블 컨테이너에 스크롤 이벤트 리스너 추가
      tableView.addEventListener('scroll', function() {
          const thead = table.querySelector('thead');
          if (!thead) return;
          
          const scrollTop = tableView.scrollTop;
          
          // 스크롤이 있을 때 sticky 적용
          if (scrollTop > 0) {
              thead.classList.add('sticky');
              thead.classList.remove('out-of-view');
          } else {
              // 스크롤이 없을 때는 기본 상태로 복원
              thead.classList.remove('sticky');
              thead.classList.remove('out-of-view');
          }
      });
      
      // 윈도우 스크롤 이벤트도 추가하여 테이블이 뷰포트를 벗어날 때 처리
      window.addEventListener('scroll', function() {
          const thead = table.querySelector('thead');
          if (!thead) return;
          
          const tableViewRect = tableView.getBoundingClientRect();
          
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
          const thead = table.querySelector('thead');
          if (thead && thead.classList.contains('sticky')) {
              // sticky 상태 유지하되 위치 재조정
              const tableViewRect = tableView.getBoundingClientRect();
              
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
                  
                  // Sticky 헤더 재초기화
                  if (typeof initializeStickyHeader === 'function') {
                      initializeStickyHeader();
                      console.log('Sticky 헤더 재초기화 완료');
                  }
                  
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
      fetch('/600/update_row_field/', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({
              row_id: rowId,
              field_name: field,
              value: value
          })
      })
      .then(r=>r.json())
      .then(function(data){
          if(!data.success) {
              alert('수정 실패: '+(data.error||''));
              return;
          }
          
          // 부분 업데이트로 변경 (전체 테이블 새로고침 대신)
          updateTableCell(rowId, field, value);
          
          // F/U 일정 필드인 경우 캘린더도 새로고침
          if(field === 'F/U 일정' && window.calendar) {
              window.calendar.refetchEvents();
          }
          
          // 모달이 열려있는 경우 모달 데이터도 새로고침
          if (document.getElementById('detailModal') && document.getElementById('detailModal').style.display !== 'none') {
              fetch('/600/get_row_details/'+rowId+'/')
                .then(r => r.json())
                .then(function(data){
                    if(data.success) showDetailModal(data.row_data, data.row_id);
                });
          }
      })
      .catch(function(err){
          alert('수정 실패: 네트워크 오류');
          console.error(err);
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
                      let html = '<div><b>' + type + ' 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
                      options.forEach(function(opt) {
                          html += `<li style="display:flex;align-items:center;gap:6px;">
                              <span data-option-id="${opt.id}" style="cursor:pointer;background:${opt.color ? hexToRgba(opt.color, 0.18) : '#eee'};border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;">${opt.option}</span>
                              <input type="color" value="${opt.color||'#eeeeee'}" data-color-edit="${opt.id}" style="width:24px;height:24px;border:none;vertical-align:middle;cursor:pointer;">
                              <button data-edit="${opt.id}">✏️</button>
                              <button data-del="${opt.id}">🗑️</button>
                          </li>`;
                      });
                      html += '</ul>';
                      html += '<input type="text" placeholder="새 옵션 추가" style="width:70%;"> <button class="add-btn">추가</button></div>';
                      dropdown.innerHTML = html;
                      document.body.appendChild(dropdown);
                      
                      // 옵션 선택
                      dropdown.querySelectorAll('span[data-option-id]').forEach(function(span){
                          span.onclick = function(){
                              td.innerHTML = `<div class="dropdown-pill" style="background:${this.style.background}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${this.innerText}</div>`;
                              td.setAttribute('data-value', this.getAttribute('data-option-id'));
                              closeDropdown();
                              // 드롭다운 값 저장
                              saveNewRowField(tr, type, this.getAttribute('data-option-id'));
                          };
                      });
                      
                      // 새 항목 추가
                      dropdown.querySelector('.add-btn').onclick = function(){
                          const val = dropdown.querySelector('input[type=text]').value.trim();
                          if(val) {
                              fetch('/600/dropdown_options/?field=' + encodeURIComponent(type), {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'name=' + encodeURIComponent(val)
                              })
                              .then(r => r.json())
                              .then(data => {
                                  if(data.id && data.option) {
                                      // 새로 추가된 옵션을 드롭다운에 동적으로 추가
                                      const ul = dropdown.querySelector('ul');
                                      const li = document.createElement('li');
                                      li.style.cssText = 'display:flex;align-items:center;gap:6px;';
                                      li.innerHTML = `
                                          <span data-option-id="${data.id}" style="cursor:pointer;background:${data.color ? hexToRgba(data.color, 0.18) : '#eee'};border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;">${data.option}</span>
                                          <input type="color" value="${data.color||'#eeeeee'}" data-color-edit="${data.id}" style="width:24px;height:24px;border:none;vertical-align:middle;cursor:pointer;">
                                          <button data-edit="${data.id}">✏️</button>
                                          <button data-del="${data.id}">🗑️</button>
                                      `;
                                      ul.appendChild(li);
                                      
                                      // 새로 추가된 옵션에 이벤트 바인딩
                                      const span = li.querySelector('span[data-option-id]');
                                      span.onclick = function(){
                                          td.innerHTML = `<div class="dropdown-pill" style="background:${this.style.background}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${this.innerText}</div>`;
                                          td.setAttribute('data-value', data.id);
                                          closeDropdown();
                                          // 드롭다운 값 저장
                                          saveNewRowField(tr, type, data.id);
                                      };
                                      
                                      // 새 옵션의 컬러피커, 삭제, 수정 버튼 이벤트 바인딩
                                      bindNewRowDropdownItemEvents(li, type, tr);
                                      
                                      // 입력 필드 초기화
                                      dropdown.querySelector('input[type=text]').value = '';
                                  }
                              })
                              .catch(error => {
                                  console.error('옵션 추가 실패:', error);
                                  alert('옵션 추가에 실패했습니다.');
                              });
                          }
                      };
                      
                      // 기존 옵션들에 이벤트 바인딩
                      dropdown.querySelectorAll('li').forEach(function(li) {
                          bindNewRowDropdownItemEvents(li, type, tr);
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
          editBtn.onclick = function(e){
              e.stopPropagation();
              const span = li.querySelector('span[data-option-id]');
              const old = span.innerText;
              const input = document.createElement('input');
              input.type = 'text'; input.value = old;
              input.className = 'table-edit-input';
              span.replaceWith(input);
              input.focus();
              input.onkeydown = function(ev){
                  if(ev.key==='Enter'){
                      fetch('/600/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + editBtn.getAttribute('data-edit') + '&name=' + encodeURIComponent(input.value), {
                          method: 'PUT'
                      }).then(r => r.json()).then(data => {
                          if(data.success) {
                              // 수정된 내용 즉시 반영
                              const newSpan = document.createElement('span');
                              newSpan.setAttribute('data-option-id', editBtn.getAttribute('data-edit'));
                              newSpan.style.cssText = span.style.cssText;
                              newSpan.innerText = input.value;
                              
                              // 클릭 이벤트 재바인딩
                              newSpan.addEventListener('click', function(){
                                  const td = tr.querySelector('td[data-field="' + type + '"]');
                                  if(td) {
                                      td.innerHTML = `<div class="dropdown-pill" style="background:${this.style.background}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${this.innerText}</div>`;
                                      td.setAttribute('data-value', this.getAttribute('data-option-id'));
                                      closeDropdown();
                                      // 드롭다운 값 저장
                                      saveNewRowField(tr, type, this.getAttribute('data-option-id'));
                                  }
                              });
                              
                              input.replaceWith(newSpan);
                              
                              // 실시간 동기화 - 드롭다운 옵션 수정도 테이블과 칸반보드에 반영
                              syncTableAndKanban(type);
                          }
                      }).catch(error => {
                          console.error('수정 실패:', error);
                          // 실패시 원래 값으로 복원
                          const restoredSpan = document.createElement('span');
                          restoredSpan.setAttribute('data-option-id', editBtn.getAttribute('data-edit'));
                          restoredSpan.style.cssText = input.previousElementSibling ? input.previousElementSibling.style.cssText : 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                          restoredSpan.innerText = old;
                          input.replaceWith(restoredSpan);
                      });
                  } else if(ev.key==='Escape') {
                      // ESC 키로 취소
                      const cancelSpan = document.createElement('span');
                      cancelSpan.setAttribute('data-option-id', editBtn.getAttribute('data-edit'));
                      cancelSpan.style.cssText = input.previousElementSibling ? input.previousElementSibling.style.cssText : 'cursor:pointer;background:#eee;border-radius:4px;padding:2px 8px;min-width:60px;display:inline-block;';
                      cancelSpan.innerText = old;
                      input.replaceWith(cancelSpan);
                  }
              };
          };
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
  
  // 숫자 필드 업데이트 시 콤마 포맷팅 적용
  function updateCellValue(id, fieldName, value, element) {
      console.log('updateCellValue 호출:', {id, fieldName, value, element});
      let processedValue = value;
      if (fieldName === '매출' || fieldName.includes('매출')) {
          let raw = (value || '').toString().replace(/[^\d]/g, '');
          if (raw) {
              processedValue = parseInt(raw).toString();
          } else {
              processedValue = '';
          }
      }
      
      // 숫자인지 확인 (콤마 제거 후 숫자 변환 가능한지 체크)
      const numericValue = processedValue.replace(/,/g, '');
      const isNumeric = !isNaN(numericValue) && !isNaN(parseFloat(numericValue));
      
      if (isNumeric && fieldName !== '연락처' && fieldName !== '사업자번호') {
          // 숫자 필드인 경우 콤마 제거 후 서버에 저장
          const cleanValue = removeCommaFromNumber(processedValue);
          
          fetch('/600/update_row_field/', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'X-CSRFToken': getCsrfToken()
              },
              body: `id=${id}&field=${encodeURIComponent(fieldName)}&value=${encodeURIComponent(cleanValue)}`
          })
          .then(response => response.json())
          .then(data => {
              if (data.success) {
                  // 성공 시 화면에는 콤마가 포함된 값으로 표시
                  // 매출 필드는 한국어 단위로 표시
                  if (fieldName === '매출' || fieldName.includes('매출')) {
                      element.textContent = formatToKoreanCurrency(cleanValue);
                  } else {
                      element.textContent = formatNumberWithComma(cleanValue);
                  }
                  
                  // 실시간 동기화
                  syncTableAndKanban(fieldName);
              } else {
                  console.error('셀 업데이트 실패:', data.error);
                  showNotification('셀 업데이트에 실패했습니다: ' + (data.error || ''), 'error');
              }
          })
          .catch(error => {
              console.error('네트워크 오류:', error);
              showNotification('네트워크 오류가 발생했습니다: ' + error.message, 'error');
          });
      } else {
          // 일반 텍스트 필드인 경우 기존 로직 사용
          fetch('/600/update_row_field/', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'X-CSRFToken': getCsrfToken()
              },
              body: `id=${id}&field=${encodeURIComponent(fieldName)}&value=${encodeURIComponent(value)}`
          })
          .then(response => response.json())
          .then(data => {
              if (data.success) {
                  element.textContent = value;
                  
                  // 실시간 동기화
                  syncTableAndKanban(fieldName);
              } else {
                  console.error('셀 업데이트 실패:', data.error);
                  showNotification('셀 업데이트에 실패했습니다: ' + (data.error || ''), 'error');
              }
          })
          .catch(error => {
              console.error('네트워크 오류:', error);
              showNotification('네트워크 오류가 발생했습니다: ' + error.message, 'error');
          });
      }
  }
  
  // 테이블과 칸반보드 실시간 동기화 함수
  function syncTableAndKanban(fieldName) {
      // 테이블 새로고침은 필요한 경우에만 실행
      // (드롭다운 옵션 변경, 정렬/필터 변경 등)
      if (fieldName && ['구분', '영업진행', '가능성', '업종'].includes(fieldName)) {
          if (typeof refreshTable === 'function') {
              refreshTable();
          }
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

              // 서버에 새 행 생성 요청 (회사명: '새 항목')
              fetch('/600/create_new_row/', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'field=' + encodeURIComponent('회사명') + '&value=' + encodeURIComponent('새 항목')
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
  });

  // 매출 셀 더블클릭/수정 시 한글 단위 → 숫자(콤마)로 입력
  function showNumberForEdit(input) {
      const value = input.value;
      const number = parseKoreanCurrency(value);
      input.value = formatNumberWithComma(number);
      input.select();
  }