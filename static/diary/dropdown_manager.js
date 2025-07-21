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
                    fetch('/sales/update/', {
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
                            
                            // 종속된 행들 찾아서 업데이트
                            updateDependentRows(id, '지역', selectedRegion);
                            
                            // 테이블 리렌더링으로 모든 드롭다운 pill 업데이트
                            if (typeof refreshTable === 'function') {
                                refreshTable();
                            }
                            
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
                    fetch('/sales/update/', {
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
                            
                            // 종속된 행들 찾아서 업데이트
                            updateDependentRows(id, '상세지역', selectedSubregion);
                            
                            // 테이블 리렌더링으로 모든 드롭다운 pill 업데이트
                            if (typeof refreshTable === 'function') {
                                refreshTable();
                            }
                            
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
        
        fetch('/sales/dropdown_options/?field=' + encodeURIComponent(type))
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
                    
                    // "선택 없음" 옵션 추가
                    html += `
                      <div class="dropdown-option-container" style="padding: 4px 8px; border-bottom: 1px solid #f0f0f0;">
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
                            <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #999; font-style: italic;">선택 없음</span>
                          </div>
                        </div>
                      </div>
                    `;
                    
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
                            
                            // "선택 없음" 옵션 처리
                            if (optionId === 'none') {
                                // UI 업데이트
                                td.innerHTML = `<div class="dropdown-pill" style="background:#eee; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">선택 없음</div>`;
                                td.setAttribute('data-value', '');
                                
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
                                            
                                            // 테이블 리렌더링으로 모든 드롭다운 pill 업데이트
                                            if (typeof refreshTable === 'function') {
                                                refreshTable();
                                            }
                                            
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
                                if (window.dropdown && window.dropdown.parentNode) {
                                    window.dropdown.parentNode.removeChild(window.dropdown);
                                    window.dropdown = null;
                                }
                                return;
                            }
                            
                            const option = options.find(o => String(o.id) === String(optionId));
                            // UI 업데이트 - 즉시 실행
                            if (option) {
                                const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                                td.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                                td.setAttribute('data-value', optionId);
                            } else {
                                // 옵션을 찾지 못한 경우에도 pill 형태로 표시
                                console.log(`옵션을 찾지 못함, pill 형태로 표시: ${optionId}`);
                                td.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${optionId}</div>`;
                                td.setAttribute('data-value', optionId);
                            }
                            
                            // 드롭다운 닫기 - 즉시 실행
                            if (window.dropdown && window.dropdown.parentNode) {
                                window.dropdown.parentNode.removeChild(window.dropdown);
                                window.dropdown = null;
                            }
                            
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
                                        // 테이블 리렌더링으로 모든 드롭다운 pill 업데이트
                                        if (typeof refreshTable === 'function') {
                                            refreshTable();
                                        }
                                        
                                        // 종속된 행들 찾아서 업데이트 (ID 전달)
                                        updateDependentRows(id, type, optionId);
                                        
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
        colorInput.addEventListener('change', function(e) {
            e.stopPropagation();
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
                    const optionContainer = this.closest('.dropdown-option-container');
                    const dropdownItem = optionContainer.querySelector('.dropdown-item');
                    if (dropdownItem) {
                        dropdownItem.style.background = hexToRgba(newColor, 0.18);
                    }
                    syncTableAndKanban(fieldType);
                    
                    // 상태 속성인 경우 상태 탭 새로고침
                    if (window.statusAttributeName && fieldType === window.statusAttributeName) {
                        console.log('상태 속성 색상 변경됨, 상태 탭 새로고침 시작');
                        // 상태 탭 새로고침 함수 호출
                        if (typeof refreshStatusTabs === 'function') {
                            setTimeout(() => {
                                refreshStatusTabs();
                            }, 100);
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
              min-width: ${Math.max(rect.width, 150)}px !important;
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
                // 호버 효과
                item.addEventListener('mouseenter', function() {
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
                item.addEventListener('mouseout', function() {
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
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const selectedOptionId = this.getAttribute('data-option-id');
                    const selectedOptionText = this.getAttribute('data-option-text');
                    const selectedColor = this.getAttribute('data-color');
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
                });
            });
            
            // 드롭다운 외부 클릭 시 닫기
            setTimeout(() => {
                document.addEventListener('click', function closeHandler(e) {
                    if (dropdown && !dropdown.contains(e.target) && !btn.contains(e.target)) {
                        if (dropdown.parentNode) {
                            dropdown.parentNode.removeChild(dropdown);
                            window.dropdown = null;
                        }
                        document.removeEventListener('click', closeHandler);
                    }
                });
            }, 100);
        })
        .catch(function(error) {
            console.error('모달 드롭다운 옵션 로드 실패:', error);
            alert('드롭다운 옵션을 불러오는데 실패했습니다: ' + error.message);
        });
  }
  
  // 모달용 드롭다운 옵션 선택 함수
  function selectModalDropdownOption(rowId, fieldName, optionId, optionText, btn, color) {
    console.log('selectModalDropdownOption 호출됨:', rowId, fieldName, optionId, optionText);
    
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
        if (data.success) {
            console.log('모달 드롭다운 업데이트 성공:', fieldName, optionId);
            
            // 테이블 실시간 업데이트 - 리렌더링으로 모든 드롭다운 pill 업데이트
            if (typeof refreshTable === 'function') {
                refreshTable();
            }
            
            // 종속된 행들 찾아서 업데이트
            if (typeof updateDependentRows === 'function') {
                updateDependentRows(rowId, fieldName, optionId);
            }
            
            // 칸반보드 실시간 업데이트 - 현재 칸반보드 속성과 일치하는 경우
            const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
                document.getElementById('kanbanAttributeSelect').value : 
                window.SELECTED_KANBAN_ATTR || window.kanbanAttribute;
                
            if (currentKanbanAttr && fieldName === currentKanbanAttr) {
                if (typeof refreshKanban === 'function') {
                    refreshKanban();
                }
            }
        } else {
            console.error('모달 드롭다운 업데이트 실패:', data.error);
            showNotification('업데이트 실패: ' + data.error, 'error');
            // 실패 시 버튼 텍스트 복원
            btn.textContent = btn.textContent; // 이전 값으로 복원 (실제로는 서버에서 가져와야 함)
        }
    })
    .catch(error => {
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
      min-width: ${Math.max(rect.width, 150)}px !important;
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
    setTimeout(() => {
        document.addEventListener('click', function closeHandler(e) {
            if (dropdown && !dropdown.contains(e.target) && !btn.contains(e.target)) {
                if (dropdown.parentNode) {
                    dropdown.parentNode.removeChild(dropdown);
                    window.dropdown = null;
                }
                document.removeEventListener('click', closeHandler);
            }
        });
    }, 100);
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
          min-width: ${Math.max(rect.width, 150)}px !important;
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
        setTimeout(() => {
            document.addEventListener('click', function closeHandler(e) {
                if (dropdown && !dropdown.contains(e.target) && !btn.contains(e.target)) {
                    if (dropdown.parentNode) {
                        dropdown.parentNode.removeChild(dropdown);
                        window.dropdown = null;
                    }
                    document.removeEventListener('click', closeHandler);
                }
            });
        }, 100);
      })
      .catch(error => {
        console.error('상세지역 드롭다운 로딩 오류:', error);
        alert('상세지역 정보를 불러오는 중 오류가 발생했습니다.');
      });
  }