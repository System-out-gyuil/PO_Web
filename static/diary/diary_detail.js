// 상세보기 모달 함수 - 새로운 Row 시스템에 맞게 수정
function showDetailModal(rowData, rowId) {
  console.log('===== showDetailModal 시작 =====');
  console.log('rowData:', rowData);
  console.log('rowId:', rowId);
  console.log('rowData["음성파일"]:', rowData['음성파일']);
  console.log('rowData 전체 속성:');
  Object.keys(rowData).forEach(key => {
      console.log(`- ${key}:`, rowData[key]);
  });
  console.log('================================');
  
  // 현재 상세 조회 중인 행 ID 저장
  window.currentDetailRowId = rowId;
  
  // 사용자의 속성들을 기준으로 표시
  const user = { id: 1 }; // 임시로 user id 1 사용
  
  // 백엔드에서 사용자의 속성 목록을 가져와야 함
  fetch('/diary/get_user_attributes/')
    .then(r => r.json())
    .then(function(attributesData) {
        if (!attributesData.success) {
            alert('속성 정보를 불러올 수 없습니다.');
            return;
        }
        
        // 속성들을 필수/일반 순서로 정렬
        const sortedAttributes = attributesData.attributes.sort((a, b) => {
            // essential 속성이 먼저 오도록 정렬 (true가 false보다 먼저)
            if (a.essential !== b.essential) {
                return b.essential - a.essential; // true(1)가 false(0)보다 먼저
            }
            // 같은 그룹 내에서는 id 순서로 정렬
            return a.id - b.id;
        });
        
        let html = '<h3>상세 정보</h3><table style="width:100%">';
        const readonlyFields = ['생성일', '수정일'];
        let textAttributeValue = ''; // text 타입 속성의 값을 저장
        let audioFileValue = ''; // 음성파일 속성의 값을 저장
        
        sortedAttributes.forEach(function(attr) {
            const value = rowData[attr.name] || '';
            let inputHtml = '';
            
            // 음성파일 컬럼은 좌측에 표시하지 않음
            if (attr.name === '음성파일') {
                audioFileValue = value;
                return; // 이 속성은 좌측 테이블에 추가하지 않음
            }
            
            if (readonlyFields.includes(attr.name)) {
                inputHtml = `<input type="text" value="${value}" readonly style="background:#f8f9fa;">`;
            } else if (attr.name === '지역') {
                // 지역 필드는 특별 처리
                inputHtml = `<button type="button" class="add-btn" style="width:100%;background:#f8f9fa;color:#333;border:1px solid #eee;" onclick="openDetailDropdown('${rowId}','${attr.name}',this)">${value||'선택'}</button>`;
            } else if (attr.name === '상세지역') {
                // 상세지역 필드는 특별 처리
                inputHtml = `<button type="button" class="add-btn" style="width:100%;background:#f8f9fa;color:#333;border:1px solid #eee;" onclick="openDetailDropdown('${rowId}','${attr.name}',this)">${value||'선택'}</button>`;
            } else if (attr.name === '기대출') {
                // 기대출 필드는 8개 카테고리를 4칸씩 2줄로 표시
                let debtData = {};
                try {
                    if (value && typeof value === 'object') {
                        debtData = value;
                    } else if (value && typeof value === 'string' && value.startsWith('{')) {
                        debtData = JSON.parse(value);
                    }
                } catch (e) {
                    console.error('기대출 데이터 파싱 오류:', e);
                }
                
                // 8개 카테고리 정의
                const debtCategories = [
                    { key: 'tech_guarantee', label: '기술보증기금' },
                    { key: 'credit_guarantee', label: '신용보증기금' },
                    { key: 'credit_foundation', label: '신용보증재단' },
                    { key: 'smba', label: '중진공' },
                    { key: 'semas_innovation', label: '소진공-혁신성장' },
                    { key: 'semas_lowcredit', label: '소진공-저신용' },
                    { key: 'collateral', label: '담보' },
                    { key: 'credit', label: '신용' }
                ];
                
                // 첫 번째 줄 (4개) - 4x2 그리드 형태로 변경
                let firstRowHtml = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 15px;">';
                for (let i = 0; i < 4; i++) {
                    const category = debtCategories[i];
                    const currentValue = debtData[category.key] || '';
                    firstRowHtml += `
                        <div style="text-align: center;">
                            <label style="display: block; font-size: 12px; font-weight: bold; color: #495057; margin-bottom: 5px;">${category.label}</label>
                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                <input type="text" 
                                       id="debt_${category.key}_${rowId}" 
                                       value="${currentValue}" 
                                       placeholder="0"
                                       style="width: 70px; height: 28px; padding: 4px 6px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px; text-align: center;"
                                       onchange="updateDebtField('${rowId}', '${category.key}', this.value)">
                                <span style="font-size: 11px; color: #6c757d;">만원</span>
                            </div>
                        </div>
                    `;
                }
                firstRowHtml += '</div>';
                
                // 두 번째 줄 (4개)
                let secondRowHtml = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">';
                for (let i = 4; i < 8; i++) {
                    const category = debtCategories[i];
                    const currentValue = debtData[category.key] || '';
                    secondRowHtml += `
                        <div style="text-align: center;">
                            <label style="display: block; font-size: 12px; font-weight: bold; color: #495057; margin-bottom: 5px;">${category.label}</label>
                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                <input type="text" 
                                       id="debt_${category.key}_${rowId}" 
                                       value="${currentValue}" 
                                       placeholder="0"
                                       style="width: 70px; height: 28px; padding: 4px 6px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px; text-align: center;"
                                       onchange="updateDebtField('${rowId}', '${category.key}', this.value)">
                                <span style="font-size: 11px; color: #6c757d;">만원</span>
                            </div>
                        </div>
                    `;
                }
                secondRowHtml += '</div>';
                
                // 총액 표시
                const totalAmount = Object.values(debtData).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
                const totalHtml = `
                    <div style="margin-top: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px; text-align: center;">
                        <span style="font-weight: bold; color: #495057;">총 기대출: </span>
                        <span id="debt_total_${rowId}" style="font-weight: bold; color: #007bff;">${totalAmount.toLocaleString()}</span>
                        <span style="color: #6c757d;">만원</span>
                    </div>
                `;
                
                inputHtml = `
                    <div style="border: 1px solid #e9ecef; border-radius: 6px; padding: 12px; background: #fff;">
                        ${firstRowHtml}
                        ${secondRowHtml}
                        ${totalHtml}
                    </div>
                `;
            } else if (attr.type === 'outstanding_debts') {
                // 기존 코드 제거 (위의 attr.name === '기대출'로 대체됨)
                // 이 부분은 더 이상 사용되지 않음
            } else if (attr.type === 'recommend') {
                // 추천자금 필드 처리
                let displayValue = '';
                let detailData = null;
                
                // 저장된 값이 JSON 형태인지 확인
                try {
                    if (value && typeof value === 'string' && value.startsWith('{')) {
                        detailData = JSON.parse(value);
                        displayValue = `${detailData['총자금']?.toLocaleString() || '0'}원`;
                    } else {
                        displayValue = value || '';
                    }
                } catch (e) {
                    displayValue = value || '';
                }
                
                inputHtml = `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <input type="text" 
                               value="${displayValue}" 
                               data-field="${attr.name}" 
                               onchange="updateRowField('${rowId}', '${attr.name}', this.value)"
                               style="flex: 1; padding: 8px; border: 1px solid #ced4da; border-radius: 4px;">
                        ${detailData ? `
                        <button type="button" 
                                onclick="showFundingDetailModal('${rowId}', '${attr.name}')" 
                                style="padding: 8px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap; font-size: 14px;">
                            상세보기
                        </button>
                        ` : ''}
                        <button type="button" 
                                onclick="requestFundingRecommendation('${rowId}')" 
                                style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap; font-size: 14px;">
                            추천받기
                        </button>
                    </div>
                `;
            } else if (attr.name === '추천자금') {
                // 속성명으로도 추천자금 필드 처리 (fallback)
                let displayValue = '';
                let detailData = null;
                
                // 저장된 값이 JSON 형태인지 확인
                try {
                    if (value && typeof value === 'string' && value.startsWith('{')) {
                        detailData = JSON.parse(value);
                        displayValue = `${detailData['총자금']?.toLocaleString() || '0'}원`;
                    } else {
                        displayValue = value || '';
                    }
                } catch (e) {
                    displayValue = value || '';
                }
                
                inputHtml = `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <input type="text" 
                               value="${displayValue}" 
                               data-field="${attr.name}" 
                               onchange="updateRowField('${rowId}', '${attr.name}', this.value)"
                               style="flex: 1; padding: 8px; border: 1px solid #ced4da; border-radius: 4px;">
                        ${detailData ? `
                        <button type="button" 
                                onclick="showFundingDetailModal('${rowId}', '${attr.name}')" 
                                style="padding: 8px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap; font-size: 14px;">
                            상세보기
                        </button>
                        ` : ''}
                        <button type="button" 
                                onclick="requestFundingRecommendation('${rowId}')" 
                                style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap; font-size: 14px;">
                            추천받기
                        </button>
                    </div>
                `;
            } else if (attr.type === 'dropdown') {
                inputHtml = `<button type="button" class="add-btn" style="width:100%;background:#f8f9fa;color:#333;border:1px solid #eee;" onclick="openDetailDropdown('${rowId}','${attr.name}',this)">${value||'선택'}</button>`;
            } else if (attr.type === 'datetime') {
                // 날짜 형식 변환
                let dateValue = '';
                if (value) {
                    try {
                        const dt = new Date(value);
                        dateValue = dt.toISOString().split('T')[0];
                    } catch(e) {
                        dateValue = value;
                    }
                }
                inputHtml = `<input type="date" value="${dateValue}" data-field="${attr.name}" onchange="updateRowField('${rowId}', '${attr.name}', this.value)">`;
            } else if (attr.type === 'file') {
                // 파일 업로드 처리
                let fileInfo = null;
                try {
                    // value에 파일 정보가 JSON으로 저장되어 있는지 확인
                    if (value && typeof value === 'object' && value.original_filename) {
                        fileInfo = value;
                    } else if (value && typeof value === 'string' && value.startsWith('{')) {
                        fileInfo = JSON.parse(value);
                    }
                } catch (e) {
                    // JSON 파싱 실패 시 null로 유지
                }
                
                if (fileInfo && fileInfo.original_filename) {
                    // 파일이 이미 업로드된 경우
                    inputHtml = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <button type="button" onclick="document.getElementById('file_${attr.name}_${rowId}').click()" 
                                    style="padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                수정
                            </button>
                            <a href="${fileInfo.download_url}" download="${fileInfo.original_filename}" 
                               style="color: #007bff; text-decoration: none; cursor: pointer;"
                               onclick="downloadFile('${fileInfo.download_url}', '${fileInfo.original_filename}')">
                                📎 ${fileInfo.original_filename}
                            </a>
                            <button type="button" onclick="deleteFile('${rowId}', '${attr.name}')" 
                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                삭제
                            </button>
                            <input type="file" id="file_${attr.name}_${rowId}" style="display: none;" onchange="handleFileUpload('${rowId}', '${attr.name}', this)">
                        </div>
                    `;
                } else {
                    // 파일이 업로드되지 않은 경우
                    inputHtml = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <input type="file" id="file_${attr.name}_${rowId}" style="display: none;" onchange="handleFileUpload('${rowId}', '${attr.name}', this)">
                            <button type="button" onclick="document.getElementById('file_${attr.name}_${rowId}').click()" 
                                    style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                파일 선택
                            </button>
                            <span style="color: #666; font-size: 12px;">파일이 선택되지 않음</span>
                        </div>
                    `;
                }
            } else if (attr.type === 'text') {
                // "변환된 텍스트"는 우측에만 표시하므로 좌측에서 제외
                if (attr.name === '변환된 텍스트') {
                    return; // 이 속성은 건너뛰기
                }
                
                // text 타입은 좌측에서 바로 편집 가능
                textAttributeValue = value;
                window.currentTextAttributeName = attr.name; // text 속성명 저장
                
                // 좌측에서 바로 편집 가능한 일반 텍스트 입력창
                inputHtml = `<input type="text" value="${value}" data-field="${attr.name}" onchange="updateRowField('${rowId}', '${attr.name}', this.value)">`;
            } else {
                inputHtml = `<input type="text" value="${value}" data-field="${attr.name}" onchange="updateRowField('${rowId}', '${attr.name}', this.value)">`;
            }
            
            html += `<tr><th style="text-align:right;padding:4px 8px;color:#888;">${attr.name}</th><td style="padding:4px 8px;">${inputHtml}</td></tr>`;
        });
        
        html += '</table>';
        document.getElementById('detailModalContent').innerHTML = html;
        
        // 우측 텍스트 영역에 변환된 텍스트 컬럼 값 로드
        const convertedTextArea = document.getElementById('convertedText');
        if (convertedTextArea) {
            // "변환된 텍스트" 속성 값 찾기
            const convertedTextAttribute = rowData['변환된 텍스트'];
            convertedTextArea.value = convertedTextAttribute || '';
        }
        
        // 음성파일 관리 영역 업데이트 ("음성파일" 속성 사용)
        // DOM 요소가 준비된 후에 실행하도록 setTimeout 사용
        setTimeout(() => {
            try {
                updateAudioFileManagement(audioFileValue);
            } catch (error) {
                console.error('음성파일 관리 영역 업데이트 오류:', error);
            }
        }, 100);
        
        // 전역 변수에 현재 행 ID 저장
        window.currentDetailRowId = rowId;
        window.currentRowId = rowId;
        
        document.getElementById('detailModal').style.display = 'flex';
    });
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
  fetch('/diary/get_user_attributes/')
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

// 모달용 지역 드롭다운 표시 함수
function showModalRegionDropdown(rowId, fieldName, btn) {
  console.log('showModalRegionDropdown 호출됨:', rowId, fieldName, btn);
  
  const regionNames = ['서울','경기','인천','대구','부산','광주','대전','울산','세종','강원','충북','충남','전북','전남'];
  
  // 기존 드롭다운이 있으면 닫기
  closeDropdown();
  
  // 드롭다운 메뉴 생성 - 테이블과 동일한 스타일 적용
  const dropdown = document.createElement('div');
  dropdown.className = 'dropdown-edit';
  dropdown.style.position = 'absolute';
  dropdown.style.left = (btn.getBoundingClientRect().left + window.scrollX) + 'px';
  dropdown.style.top = (btn.getBoundingClientRect().top + window.scrollY + btn.offsetHeight) + 'px';
  dropdown.style.zIndex = '4000';
  
  let html = '<div><b>지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">';
  regionNames.forEach(function(region) {
      html += `<li style="margin-bottom:2px;"><span data-region="${region}" style="cursor:pointer;padding:2px 4px;border-radius:3px;">${region}</span></li>`;
  });
  html += '</ul></div>';
  
  dropdown.innerHTML = html;
  document.body.appendChild(dropdown);
  
  // 전역 dropdown 변수에 저장 (closeDropdown 함수에서 사용)
  window.dropdown = dropdown;
  
  console.log('지역 드롭다운 생성 완료:', dropdown);
  
  // 지역 클릭 이벤트
  dropdown.querySelectorAll('span[data-region]').forEach(function(span) {
      span.onmouseover = function() {
          this.style.background = '#f1f3f6';
      };
      span.onmouseout = function() {
          this.style.background = '';
      };
      span.onclick = function() {
          const selectedRegion = this.getAttribute('data-region');
          selectModalRegionOption(rowId, selectedRegion, this);
      };
  });
  
  // 드롭다운 외부 클릭 시 닫기
  function closeDropdownHandler(e) {
      if (!dropdown.contains(e.target)) {
          closeDropdown();
          document.removeEventListener('click', closeDropdownHandler);
      }
  }
  setTimeout(() => document.addEventListener('click', closeDropdownHandler), 100);
}

// 모달용 상세지역 드롭다운 표시 함수
function showModalSubregionDropdown(rowId, fieldName, btn) {
  // 현재 지역 값을 가져와야 함
  fetch('/diary/get_row_details/' + rowId + '/')
      .then(r => r.json())
      .then(function(data) {
          if (!data.success) {
              alert('행 정보를 불러올 수 없습니다.');
              return;
          }
          
          const currentRegion = data.row_data['지역'] || '서울';
          const regionMap = {
              '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
              '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
              '인천': ['계양구','남동구','동구','미추홀구','부평구','서구','연수구','중구','강화군','옹진군'],
              '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
              '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
              '광주': ['동구','서구','남구','북구','광산구'],
              '대전': ['동구','중구','서구','유성구','대덕구'],
              '울산': ['중구','남구','동구','북구','울주군'],
              '세종': ['세종시'],
              '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
              '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
              '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
              '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
              '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군']
          };
          
          const subregions = regionMap[currentRegion] || [];
          
          // 기존 드롭다운이 있으면 닫기
          closeDropdown();
          
          // 드롭다운 메뉴 생성 - 테이블과 동일한 스타일 적용
          const dropdown = document.createElement('div');
          dropdown.className = 'dropdown-edit';
          dropdown.style.position = 'absolute';
          dropdown.style.left = (btn.getBoundingClientRect().left + window.scrollX) + 'px';
          dropdown.style.top = (btn.getBoundingClientRect().top + window.scrollY + btn.offsetHeight) + 'px';
          dropdown.style.zIndex = '4000';
          
          let html = `<div><b>${currentRegion} 상세지역 선택</b><ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;">`;
          subregions.forEach(function(subregion) {
              html += `<li style="margin-bottom:2px;"><span data-subregion="${subregion}" style="cursor:pointer;padding:2px 4px;border-radius:3px;">${subregion}</span></li>`;
          });
          html += '</ul></div>';
          
          dropdown.innerHTML = html;
          document.body.appendChild(dropdown);
          
          // 전역 dropdown 변수에 저장
          window.dropdown = dropdown;
          
          // 상세지역 클릭 이벤트
          dropdown.querySelectorAll('span[data-subregion]').forEach(function(span) {
              span.onmouseover = function() {
                  this.style.background = '#f1f3f6';
              };
              span.onmouseout = function() {
                  this.style.background = '';
              };
              span.onclick = function() {
                  const selectedSubregion = this.getAttribute('data-subregion');
                  selectModalSubregionOption(rowId, selectedSubregion, this);
              };
          });
          
          // 드롭다운 외부 클릭 시 닫기
          function closeDropdownHandler(e) {
              if (!dropdown.contains(e.target)) {
                  closeDropdown();
                  document.removeEventListener('click', closeDropdownHandler);
              }
          }
          setTimeout(() => document.addEventListener('click', closeDropdownHandler), 100);
      });
}

// 모달용 지역 옵션 선택 함수
function selectModalRegionOption(rowId, regionText, element) {
  // 서버에 업데이트 요청
  fetch('/diary/update_row_field/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'id=' + encodeURIComponent(rowId) + '&field=지역&value=' + encodeURIComponent(regionText)
  })
  .then(r => r.json())
  .then(function(data) {
      if (data.success) {
          // 드롭다운 닫기
          closeDropdown();
          
          // 지역이 변경되면 상세지역도 해당 지역의 첫 번째 값으로 초기화
          const regionMap = {
              '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
              '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
              '인천': ['계양구','남동구','동구','미추홀구','부평구','서구','연수구','중구','강화군','옹진군'],
              '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
              '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
              '광주': ['동구','서구','남구','북구','광산구'],
              '대전': ['동구','중구','서구','유성구','대덕구'],
              '울산': ['중구','남구','동구','북구','울주군'],
              '세종': ['세종시'],
              '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
              '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
              '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
              '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
              '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군']
          };
          
          const firstSubregion = (regionMap[regionText] || [])[0] || '';
          if (firstSubregion) {
              // 상세지역도 함께 업데이트
              fetch('/diary/update_row_field/', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'id=' + encodeURIComponent(rowId) + '&field=상세지역&value=' + encodeURIComponent(firstSubregion)
              })
              .then(r => r.json())
              .then(function(data) {
                  if (data.success) {
                      // 모달 새로고침
                      fetch('/diary/get_row_details/' + rowId + '/')
                          .then(r => r.json())
                          .then(function(data) {
                              if (data.success) {
                                  showDetailModal(data.row_data, data.row_id);
                              }
                          });
                          
                      // 테이블과 칸반보드 새로고침
                      refreshTable();
                      // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
                      if (window.kanbanAttribute && '지역' === window.kanbanAttribute) {
                          refreshKanban();
                      }
                  }
              });
          }
      } else {
          alert('수정 실패: ' + (data.error || ''));
      }
  });
}

// 모달용 상세지역 옵션 선택 함수
function selectModalSubregionOption(rowId, subregionText, element) {
  // 서버에 업데이트 요청
  fetch('/diary/update_row_field/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'id=' + encodeURIComponent(rowId) + '&field=상세지역&value=' + encodeURIComponent(subregionText)
  })
  .then(r => r.json())
  .then(function(data) {
      if (data.success) {
          // 드롭다운 닫기
          closeDropdown();
          
          // 모달 새로고침
          fetch('/diary/get_row_details/' + rowId + '/')
              .then(r => r.json())
              .then(function(data) {
                  if (data.success) {
                      showDetailModal(data.row_data, data.row_id);
                  }
              });
              
          // 테이블과 칸반보드 새로고침
          refreshTable();
          // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
          if (window.kanbanAttribute && '상세지역' === window.kanbanAttribute) {
              refreshKanban();
          }
      } else {
          alert('수정 실패: ' + (data.error || ''));
      }
  });
}

function closeDetailModal() {
  document.getElementById('detailModal').style.display = 'none';
  
  // 전역 변수 초기화
  window.currentDetailRowId = null;
  window.currentTextAttributeName = null;
  window.currentAudioFileInfo = null;
  
  // 모달 닫을 때 테이블, 칸반보드, 캘린더 새로고침
  refreshTable();
  refreshKanban();
  if (window.calendar) {
      window.calendar.refetchEvents();
  }
}

// 기대출 필드 업데이트 함수
function updateDebtField(rowId, debtKey, value) {
    // 텍스트 입력값에서 숫자만 추출 (콤마 제거 후 parseFloat 사용)
    const numericValue = parseFloat(value.replace(/[^0-9.]/g, '')) || 0;
    
    // 전역 debtData에 업데이트
    if (!window.debtData) {
        window.debtData = {};
    }
    window.debtData[debtKey] = numericValue;
    
    // 합계 계산
    const totalAmount = Object.values(window.debtData).reduce((sum, val) => sum + val, 0);
    
    // 합계 표시 업데이트
    const totalElement = document.getElementById(`debt_total_${rowId}`);
    if (totalElement) {
        totalElement.textContent = totalAmount.toLocaleString();
    }
    
    // 서버에 저장
    fetch('/diary/update_debt_field/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            row_id: rowId,
            debt_data: window.debtData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('기대출 정보가 업데이트되었습니다.');
            
            // 테이블과 칸반보드 새로고침
            if (typeof refreshTable === 'function') {
                refreshTable();
            }
            
            if (window.kanbanAttribute && window.kanbanAttribute === '기대출') {
                if (typeof refreshKanban === 'function') {
                    refreshKanban();
                }
            }
        } else {
            console.error('기대출 업데이트 실패:', data.error);
            showNotification('기대출 정보 업데이트에 실패했습니다.', 'error');
        }
    })
    .catch(error => {
        console.error('기대출 업데이트 오류:', error);
        showNotification('기대출 정보 업데이트 중 오류가 발생했습니다.', 'error');
    });
}

// CSRF 토큰 가져오기 함수 (이미 있다면 중복 제거)
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// 알림 표시 함수 (이미 있다면 중복 제거)
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
        color: white;
        padding: 12px 20px;
        border-radius: 5px;
        z-index: 10000;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// 추천자금 요청 함수
function requestFundingRecommendation(rowId) {
    // 로딩 상태 표시
    showNotification('추천자금을 분석 중입니다...', 'info');
    
    // 백엔드에 추천자금 요청
    fetch('/diary/get_funding_recommendation/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            row_id: rowId
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // 응답이 JSON인지 확인
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            return response.text().then(text => {
                console.log('Non-JSON response:', text);
                throw new Error('서버에서 JSON이 아닌 응답을 반환했습니다.');
            });
        }
        
        return response.json();
    })
    .then(data => {
        console.log('Funding recommendation response:', data);
        
        if (data.success) {
            // 성공 알림
            showNotification('추천자금 분석이 완료되었습니다!', 'success');
            
            // 추천 결과를 모달로 표시
            showFundingRecommendationModal(data.recommendation, data.data);
            
            // 현재 열린 상세 모달이 있다면 백그라운드에서 조용히 새로고침 (깜빡임 방지)
            const existingDetailModal = document.querySelector('#detailModal');
            if (existingDetailModal) {
                // 서버에서 최신 데이터를 가져와서 백그라운드에서 준비 (모달은 닫지 않음)
                fetch(`/diary/get_row_details/${rowId}/`)
                    .then(response => response.json())
                    .then(updatedData => {
                        if (updatedData.success) {
                            // 현재 모달이 여전히 열려있는지 확인 후 조용히 업데이트
                            const currentModal = document.querySelector('#detailModal');
                            if (currentModal && currentModal.style.display !== 'none') {
                                // 기존 모달을 닫지 않고 내용만 업데이트
                                const tempDiv = document.createElement('div');
                                tempDiv.style.display = 'none';
                                document.body.appendChild(tempDiv);
                                
                                // 임시로 새 모달 콘텐츠 생성
                                window.pendingModalUpdate = {
                                    rowData: updatedData.row_data,
                                    rowId: rowId
                                };
                            }
                        }
                    })
                    .catch(error => {
                        console.error('백그라운드 모달 준비 오류:', error);
                    });
            }
        } else {
            showNotification('추천자금 분석에 실패했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
        }
    })
    .catch(error => {
        console.error('추천자금 요청 오류:', error);
        showNotification('추천자금 요청 중 오류가 발생했습니다: ' + error.message, 'error');
    });
}

// 추천자금 결과 모달 표시 함수
function showFundingRecommendationModal(recommendation, analysisData) {
    // 기존 모달이 있으면 제거
    const existingModal = document.getElementById('fundingRecommendationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 결과 데이터 준비
    const result = recommendation;
    
    // 모달 HTML 구성
    const modalHtml = `
        <div id="fundingRecommendationModal" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        ">
            <div style="
                background: white;
                border-radius: 8px;
                padding: 30px;
                max-width: 800px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h2 style="margin: 0 0 20px 0; color: #333; text-align: center;">자금 추천 분석 결과</h2>
                
                <!-- 총 추천 금액 -->
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                ">
                    <h3 style="margin: 0 0 10px 0;">총 추천 금액</h3>
                    <div style="font-size: 28px; font-weight: bold;">
                        ${result.total_amount ? result.total_amount.toLocaleString() : '0'}원
                    </div>
                    <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">
                        신뢰도: ${result.confidence || '85'}
                    </div>
                </div>
                
                <!-- 자금 상세 내역 -->
                ${result.detailed_funds && Object.keys(result.detailed_funds).length > 0 ? `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px;">
                        추천 자금 상세 내역
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                        ${Object.entries(result.detailed_funds).map(([fundName, amount]) => `
                            <div style="
                                background: #f8f9fa;
                                border: 1px solid #e9ecef;
                                border-radius: 6px;
                                padding: 15px;
                                text-align: center;
                            ">
                                <div style="font-weight: bold; color: #495057; margin-bottom: 8px;">
                                    ${fundName}
                                </div>
                                <div style="font-size: 18px; font-weight: bold; color: #007bff;">
                                    ${amount.toLocaleString()}원
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <!-- 분석 결과 -->
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 5px;">
                        기업 분석 결과
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                        <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">매출 점수</div>
                            <div style="font-size: 20px; font-weight: bold; color: #007bff;">
                                ${result.analysis?.sales_score || '개선필요'}
                            </div>
                        </div>
                        <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">신용 점수</div>
                            <div style="font-size: 20px; font-weight: bold; color: #28a745;">
                                ${result.analysis?.credit_score || '개선필요'}
                            </div>
                        </div>
                        <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">기업 안정성</div>
                            <div style="font-size: 20px; font-weight: bold; color: #fd7e14;">
                                ${result.analysis?.business_stability || '안정적'}
                            </div>
                        </div>
                        <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">부채 비율</div>
                            <div style="font-size: 20px; font-weight: bold; color: #dc3545;">
                                ${result.analysis?.debt_ratio || '보통'}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 추천 금융상품 -->
                ${result.recommendations && result.recommendations.length > 0 ? `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ffc107; padding-bottom: 5px;">
                        추천 금융상품
                    </h4>
                    <div style="space-y: 10px;">
                        ${result.recommendations.map(product => `
                            <div style="
                                background: #fff3cd;
                                border: 1px solid #ffeaa7;
                                border-radius: 6px;
                                padding: 15px;
                                margin-bottom: 10px;
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: bold; color: #856404; margin-bottom: 5px;">
                                            ${product.fund_name || product.name || '금융상품'}
                                        </div>
                                        <div style="color: #6c757d; font-size: 14px;">
                                            추천 금융상품
                                        </div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 16px; font-weight: bold; color: #007bff;">
                                            ${(product.limit || product.amount || 0).toLocaleString()}원
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ffc107; padding-bottom: 5px;">
                        추천 금융상품
                    </h4>
                    <div style="
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 6px;
                        padding: 15px;
                        text-align: center;
                        color: #6c757d;
                    ">
                        추천 금융상품 정보가 없습니다.
                    </div>
                </div>
                `}
                
                <!-- 버튼 영역 -->
                <div style="text-align: center; margin-top: 30px;">
                    <button onclick="closeFundingRecommendationModal()" style="
                        background: #6c757d;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 16px;
                        margin-right: 10px;
                    ">닫기</button>
                    <button onclick="closeFundingRecommendationModal(); refreshTable(); refreshKanban();" style="
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 16px;
                    ">확인</button>
                </div>
            </div>
        </div>
    `;
    
    // 모달을 DOM에 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 외부 클릭 시 닫기
    document.getElementById('fundingRecommendationModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeFundingRecommendationModal();
        }
    });
}

// 추천자금 모달 닫기 함수
function closeFundingRecommendationModal() {
    const modal = document.getElementById('fundingRecommendationModal');
    if (modal) {
        modal.remove();
    }
    
    // 업데이트 대기 중인 상세 모달이 있다면 내용만 업데이트 (모달은 닫지 않음)
    if (window.pendingModalUpdate) {
        const currentModal = document.querySelector('#detailModal');
        if (currentModal && currentModal.style.display !== 'none') {
            // 상세 모달을 닫지 않고 내용만 새로고침
            showDetailModal(window.pendingModalUpdate.rowData, window.pendingModalUpdate.rowId);
        }
        window.pendingModalUpdate = null;
    }
}

// 자금 상세보기 모달 함수
function showFundingDetailModal(rowId, fieldName) {
    // 서버에서 행 데이터 가져오기
    fetch(`/diary/get_row_details/${rowId}/`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                showNotification('행 데이터를 가져올 수 없습니다.', 'error');
                return;
            }
            
            const rowData = data.row_data;
            const fundingDataStr = rowData[fieldName] || '';
            
            let fundingData = null;
            try {
                if (fundingDataStr && typeof fundingDataStr === 'string' && fundingDataStr.startsWith('{')) {
                    fundingData = JSON.parse(fundingDataStr);
                }
            } catch (e) {
                console.error('자금 데이터 파싱 오류:', e);
                showNotification('자금 데이터를 파싱할 수 없습니다.', 'error');
                return;
            }
            
            if (!fundingData) {
                showNotification('자금 상세 정보가 없습니다.', 'warning');
                return;
            }
            
            // 기존 모달이 있으면 제거
            const existingModal = document.getElementById('fundingDetailModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // 추천 모달과 동일한 구조로 모달 HTML 구성
            const modalHtml = `
                <div id="fundingDetailModal" style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                ">
                    <div style="
                        background: white;
                        border-radius: 8px;
                        padding: 30px;
                        max-width: 800px;
                        width: 90%;
                        max-height: 80vh;
                        overflow-y: auto;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    ">
                        <h2 style="margin: 0 0 20px 0; color: #333; text-align: center;">자금 추천 분석 결과</h2>
                        
                        <!-- 총 추천 금액 -->
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 20px;
                            border-radius: 8px;
                            margin-bottom: 20px;
                            text-align: center;
                        ">
                            <h3 style="margin: 0 0 10px 0;">총 추천 금액</h3>
                            <div style="font-size: 28px; font-weight: bold;">
                                ${fundingData['총자금'] ? fundingData['총자금'].toLocaleString() : '0'}원
                            </div>
                            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">
                                신뢰도: 85
                            </div>
                        </div>
                        
                        <!-- 자금 상세 내역 -->
                        ${fundingData['자금들'] && Object.keys(fundingData['자금들']).length > 0 ? `
                        <div style="margin-bottom: 20px;">
                            <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px;">
                                추천 자금 상세 내역
                            </h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                                ${Object.entries(fundingData['자금들']).map(([fundName, amount]) => `
                                    <div style="
                                        background: #f8f9fa;
                                        border: 1px solid #e9ecef;
                                        border-radius: 6px;
                                        padding: 15px;
                                        text-align: center;
                                    ">
                                        <div style="font-weight: bold; color: #495057; margin-bottom: 8px;">
                                            ${fundName}
                                        </div>
                                        <div style="font-size: 18px; font-weight: bold; color: #007bff;">
                                            ${amount.toLocaleString()}원
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}
                        
                        <!-- 분석 결과 -->
                        <div style="margin-bottom: 20px;">
                            <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 5px;">
                                기업 분석 결과
                            </h4>
                            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                                <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                                    <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">매출 점수</div>
                                    <div style="font-size: 20px; font-weight: bold; color: #007bff;">
                                        ${fundingData.analysis?.sales_score || '개선필요'}
                                    </div>
                                </div>
                                <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                                    <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">신용 점수</div>
                                    <div style="font-size: 20px; font-weight: bold; color: #28a745;">
                                        ${fundingData.analysis?.credit_score || '개선필요'}
                                    </div>
                                </div>
                                <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                                    <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">기업 안정성</div>
                                    <div style="font-size: 20px; font-weight: bold; color: #fd7e14;">
                                        ${fundingData.analysis?.business_stability || '안정적'}
                                    </div>
                                </div>
                                <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center;">
                                    <div style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">부채 비율</div>
                                    <div style="font-size: 20px; font-weight: bold; color: #dc3545;">
                                        ${fundingData.analysis?.debt_ratio || '보통'}
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 추천 금융상품 -->
                        <div style="margin-bottom: 20px;">
                            <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ffc107; padding-bottom: 5px;">
                                추천 금융상품
                            </h4>
                            <div style="space-y: 10px;">
                                ${fundingData['자금들'] && Object.keys(fundingData['자금들']).length > 0 ? Object.entries(fundingData['자금들']).map(([fundName, amount]) => `
                                    <div style="
                                        background: #fff3cd;
                                        border: 1px solid #ffeaa7;
                                        border-radius: 6px;
                                        padding: 15px;
                                        margin-bottom: 10px;
                                    ">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <div>
                                                <div style="font-weight: bold; color: #856404; margin-bottom: 5px;">
                                                    ${fundName}
                                                </div>
                                                <div style="color: #6c757d; font-size: 14px;">
                                                    추천 금융상품
                                                </div>
                                            </div>
                                            <div style="text-align: right;">
                                                <div style="font-size: 16px; font-weight: bold; color: #007bff;">
                                                    ${amount.toLocaleString()}원
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('') : `
                                    <div style="
                                        background: #fff3cd;
                                        border: 1px solid #ffeaa7;
                                        border-radius: 6px;
                                        padding: 15px;
                                        margin-bottom: 10px;
                                        text-align: center;
                                        color: #6c757d;
                                    ">
                                        추천 금융상품 정보가 없습니다.
                                    </div>
                                `}
                            </div>
                        </div>
                        
                        <!-- 버튼 영역 -->
                        <div style="text-align: center; margin-top: 30px;">
                            <button onclick="closeFundingDetailModal()" style="
                                background: #6c757d;
                                color: white;
                                border: none;
                                padding: 12px 24px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 16px;
                                margin-right: 10px;
                            ">닫기</button>
                            <button onclick="closeFundingDetailModal()" style="
                                background: #007bff;
                                color: white;
                                border: none;
                                padding: 12px 24px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 16px;
                            ">확인</button>
                        </div>
                    </div>
                </div>
            `;
            
            // 모달을 DOM에 추가
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // 모달 외부 클릭 시 닫기
            document.getElementById('fundingDetailModal').addEventListener('click', function(e) {
                if (e.target === this) {
                    closeFundingDetailModal();
                }
            });
        })
        .catch(error => {
            console.error('행 데이터 조회 오류:', error);
            showNotification('행 데이터를 가져오는 중 오류가 발생했습니다.', 'error');
        });
}

// 자금 상세보기 모달 닫기 함수
function closeFundingDetailModal() {
    const modal = document.getElementById('fundingDetailModal');
    if (modal) {
        modal.remove();
    }
}

function updateRowField(rowId, fieldName, value) {
    // 행의 필드 값을 업데이트하는 함수
    fetch('/diary/update_row_field/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken()
        },
        body: `id=${rowId}&field=${fieldName}&value=${encodeURIComponent(value)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`${fieldName} 필드 업데이트 성공`);
        } else {
            console.error('필드 업데이트 실패:', data.error);
            showNotification('필드 업데이트에 실패했습니다.', 'error');
        }
    })
    .catch(error => {
        console.error('네트워크 오류:', error);
        showNotification('네트워크 오류가 발생했습니다.', 'error');
    });
}

