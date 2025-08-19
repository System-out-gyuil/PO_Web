// 사용자 속성 정보 캐시
let userAttributesCache = null;
let attributesCacheTimestamp = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5분

function showDetailModal(rowData, rowId) {
    console.log('===== showDetailModal 시작 =====');
    
    
    // 현재 상세 조회 중인 행 ID 저장
    window.currentDetailRowId = rowId;
    
    // 사용자의 속성들을 기준으로 표시
    // const user = { id: 1 }; // 임시로 user id 1 사용
    
    // 캐시 확인: 5분 이내의 데이터가 있으면 재사용
    const now = Date.now();
    if (userAttributesCache && attributesCacheTimestamp && (now - attributesCacheTimestamp < CACHE_DURATION)) {
        console.log('캐시된 속성 데이터 사용');
        generateDetailModalContent(userAttributesCache, rowData, rowId);
        return;
    }
    
    // 백엔드에서 사용자의 속성 목록을 가져와야 함 - 상세보기 모달용으로 요청
    console.log('새로운 속성 데이터 요청');
    fetch('/sales/get_user_attributes/?for_detail_modal=true')
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('속성 목록 가져오기 실패:', data.error);
                return;
            }
            
            // 캐시에 저장
            userAttributesCache = data.attributes;
            attributesCacheTimestamp = now;
            
            generateDetailModalContent(data.attributes, rowData, rowId);
        })
        .catch(error => {
            console.error('속성 정보 요청 실패:', error);
        });
}

function generateDetailModalContent(attributes, rowData, rowId) {
    // 속성을 상세보기 모달 순서대로 정렬 (detail_sort_order 기준)
    const sortedAttributes = attributes.sort((a, b) => (a.detail_sort_order || 0) - (b.detail_sort_order || 0));
    
    // 읽기 전용 필드 목록 - 모든 필드를 수정 가능하게 하기 위해 비움
    const readonlyFields = [];
    
    // 숨김 필드 목록 (표시하지 않할 속성들)
    const hiddenFields = ['음성파일', '변환된 텍스트'];
    
    let html = '<h3>상세 정보</h3>';
    let textAttributeValue = ''; // text 타입 속성의 값을 저장
    let audioFileValue = ''; // 음성파일 속성의 값을 저장
    
    // 지역 정보를 저장할 변수들
    let regionValue = '';
    let subregionValue = '';
    let regionProcessed = false;
    
    // 드래그 가능한 컨테이너 시작
    html += '<div id="attributeContainer" style="position: relative;">';
    
    sortedAttributes.forEach(function(attr) {
        const value = rowData[attr.name] || '';
        let inputHtml = '';
        
        // 숨김 필드들은 좌측에 표시하지 않음
        if (hiddenFields.includes(attr.name)) {
            if (attr.name === '음성파일') {
                audioFileValue = value;
            }
            return; // 이 속성은 좌측 테이블에 추가하지 않음
        }
        
        // 지역과 상세지역을 한 줄로 표시하기 위한 처리
        if (attr.name === '지역') {
            regionValue = value;
            return; // 지역은 일단 저장만 하고 건너뛰기
        } else if (attr.name === '상세지역') {
            subregionValue = value;
            // 지역과 상세지역을 한 줄로 표시
            if (!regionProcessed) {
                html += `
                    <div class="attribute-row" data-attribute-id="${attr.id}" data-attribute-name="지역" style="display:flex;align-items:center;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #eee;position:relative;">
                        <div class="drag-handle" style="position:absolute;left:-15px;top:50%;transform:translateY(-50%);color:#ccc;cursor:move;">⋮⋮</div>
                        <label class="attribute-label" style="width:120px;font-weight:bold;color:#007bff;cursor:move;user-select:none;">지역:</label>
                        <div style="flex:1;display:flex;align-items:center;gap:10px;">
                            <button type="button" class="add-btn" style="width: 50%; background:#f8f9fa;color:#333;border:1px solid #eee;padding:8px 12px;border-radius:4px;" onclick="openDetailDropdown('${rowId}','지역',this)">${regionValue||'선택'}</button>
                            <button type="button" class="add-btn" style="width: 50%; background:#f8f9fa;color:#333;border:1px solid #eee;padding:8px 12px;border-radius:4px;" onclick="openDetailDropdown('${rowId}','상세지역',this)">${subregionValue||'선택'}</button>
                        </div>
                    </div>
                `;
                regionProcessed = true;
            }
            return; // 상세지역 처리 완료
        }
        
        if (readonlyFields.includes(attr.name)) {
            inputHtml = `<input type="text" value="${value}" style="background:#f8f9fa;">`;
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
            
            // 전역 debtData 초기화
            window.debtData = debtData;
            
            // 첫 번째 줄 (4개) - 4x2 그리드 형태로 변경
            let firstRowHtml = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 15px;">';
            for (let i = 0; i < 4; i++) {
                const category = debtCategories[i];
                const currentValue = debtData[category.key] || '';
                // 만원 단위 값 표시
                const displayValue = currentValue ? currentValue.toString() : '';
                firstRowHtml += `
                    <div style="text-align: center;">
                        <label style="display: block; font-size: 12px; font-weight: bold; color: #495057; margin-bottom: 5px;">${category.label}</label>
                        <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                            <input type="text" 
                                   id="debt_${category.key}_${rowId}" 
                                   value="${displayValue}" 
                                   placeholder="0"
                                   style="width: 67px; height: 28px; padding: 4px 6px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px; text-align: center;"
                                   oninput="formatDebtInputRealtime(this, '${rowId}', '${category.key}')"
                                   onblur="updateDebtField('${rowId}', '${category.key}', this.value)">
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
                // 만원 단위 값 표시
                const displayValue = currentValue ? currentValue.toString() : '';
                secondRowHtml += `
                    <div style="text-align: center;">
                        <label style="display: block; font-size: 12px; font-weight: bold; color: #495057; margin-bottom: 5px;">${category.label}</label>
                        <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                            <input type="text" 
                                   id="debt_${category.key}_${rowId}" 
                                   value="${displayValue}" 
                                   placeholder="0"
                                   style="width: 65px; height: 28px; padding: 4px 6px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px; text-align: center;"
                                   oninput="formatDebtInputRealtime(this, '${rowId}', '${category.key}')"
                                   onblur="updateDebtField('${rowId}', '${category.key}', this.value)">
                            <span style="font-size: 11px; color: #6c757d;">만원</span>
                        </div>
                    </div>
                `;
            }
            secondRowHtml += '</div>';
            
            // 총액 표시 (만원 단위)
            const totalAmount = Object.values(debtData).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
            const totalDisplayValue = totalAmount ? `${totalAmount}만원` : '0만원';
            const totalHtml = `
                <div style="margin-top: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px; text-align: center;">
                    <span style="font-weight: bold; color: #495057;">총 기대출: </span>
                    <span id="debt_total_${rowId}" style="font-weight: bold; color: #007bff;">${totalDisplayValue}</span>
                </div>
            `;
            
            inputHtml = `
                <div class="input-field" style="padding: 12px; background: #fff;">
                    ${firstRowHtml}
                    ${secondRowHtml}
                    ${totalHtml}
                </div>
            `;
        } else if (attr.type === 'recommend') {
            // 추천자금 필드 처리
            let displayValue = '';
            let detailData = null;
            
            // 저장된 값이 JSON 형태인지 확인
            try {
                if (value && typeof value === 'string' && value.startsWith('{')) {
                    detailData = JSON.parse(value);
                    const totalAmount = detailData['총자금'] || 0;
                    displayValue = totalAmount ? formatToKoreanCurrency(totalAmount) : '0';
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
                           onchange="detailUpdateRowField('${rowId}', '${attr.name}', this.value)"
                           style="flex: 1; padding: 8px; border: 1px solid #b1b1b1; border-radius: 4px;">
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
                    const totalAmount = detailData['총자금'] || 0;
                    displayValue = totalAmount ? formatToKoreanCurrency(totalAmount) : '0';
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
                           onchange="detailUpdateRowField('${rowId}', '${attr.name}', this.value)"
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
        } else if (attr.name === '매출' || attr.name.includes('매출')) {
            // 매출 필드는 억과 천만 단위로 분리된 입력칸 항상 표시, 저장/취소 버튼 없이 blur로 저장
            const numericValue = parseFloat(value) || 0;
            const eok = Math.floor(numericValue / 100000000);
            const cheonman = Math.floor((numericValue % 100000000) / 10000000);
            inputHtml = `
                <div class="sales-field-container" data-field="${attr.name}" data-raw="${numericValue}" style="display: flex; align-items: center; gap: 10px; width: 100%; background: white; padding: 8px; min-height: 20px;">
                    <div style="display: flex; align-items: center; gap: 5px; flex: 1;">
                        <input class="input-field" type="number" id="sales_eok_${rowId}" value="${eok}" placeholder="0" min="0"
                            style="width: 80px; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: inherit; font-family: inherit; box-sizing: border-box;"
                            onblur="saveSalesInput('${rowId}', '${attr.name}')">
                        <span style="font-size: 14px; color: #495057;">억</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 5px; flex: 1;">
                        <input class="input-field" type="number" id="sales_cheonman_${rowId}" value="${cheonman}" placeholder="0" min="0" max="99"
                            style="width: 80px; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: inherit; font-family: inherit; box-sizing: border-box;"
                            onblur="saveSalesInput('${rowId}', '${attr.name}')">
                        <span style="font-size: 14px; color: #495057;">천만</span>
                    </div>
                </div>
            `;
        } else if (attr.name === '개업년월') {
            // 개업년월 필드 처리 - 달력과 년전 입력 옵션
            let businessData = {};
            let displayText = '';
            
            try {
                if (value && typeof value === 'string') {
                    businessData = JSON.parse(value);
                } else if (value && typeof value === 'object') {
                    businessData = value;
                }
            } catch (e) {
                console.error('개업년월 데이터 파싱 오류:', e);
                businessData = {};
            }
            
            // 현재 값에 따른 표시
            if (businessData.opening_date) {
                displayText = `개업일: ${businessData.opening_date}`;
            } else if (businessData.years_ago) {
                displayText = `${businessData.years_ago}년 전`;
            } else {
                displayText = '개업 정보 없음';
            }
            
            inputHtml = `
                <div style="border: 1px solid #b1b1b1; border-radius: 4px; padding: 12px; background: #fff;" data-field="${attr.name}" data-current-value='${JSON.stringify(businessData)}'>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <!-- 개업일 입력 -->
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <label style="width: 80px; font-weight: bold; color: #495057;">개업일:</label>
                            <input type="date" 
                                   id="opening_date_${rowId}" 
                                   value="${businessData.opening_date || ''}"
                                   style="flex: 1; padding: 8px; border: 1px solid #ced4da; border-radius: 4px;"
                                   onchange="updateBusinessField('${rowId}', '${attr.name}', 'opening_date', this.value)">
                            
                            <!-- 년전 입력 -->
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="display: flex; align-items: center; gap: 3px; cursor: pointer;">
                                    <input class="input-field" type="number" 
                                           id="years_ago_${rowId}"
                                           value="${businessData.years_ago || ''}"
                                           placeholder="년수"
                                           min="0"
                                           max="100"
                                           style="width: 60px; padding: 4px; border: 1px solid #ced4da; border-radius: 4px; margin: 0 5px;"
                                           onchange="updateBusinessField('${rowId}', '${attr.name}', 'years_ago', this.value)">
                                    <span style="font-size: 12px;">년 전</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (attr.name === '업종') {
            // 업종 드롭다운 처리
            const industryOptions = [
                "농업, 임업 및 어업",
                "광업",
                "제조업",
                "전기, 가스, 증기 및 공기 조절 공급업",
                "수도, 하수 및 폐기물 처리, 원료 재생업",
                "건설업",
                "도매 및 소매업",
                "운수 및 창고업",
                "숙박 및 음식점업",
                "정보통신업",
                "금융 및 보험업",
                "부동산업",
                "전문, 과학 및 기술 서비스업",
                "사업시설 관리, 사업 지원 및 임대 서비스업",
                "교육서비스업",
                "보건업 및 사회복지 서비스업",
                "예술 스포츠 및 여가관련 서비스업",
                "협회 및 단체, 수리 및 기타 개인서비스업"
            ];
            
            const selectOptions = industryOptions.map(option => 
                `<option value="${option}" ${value === option ? 'selected' : ''}>${option}</option>`
            ).join('');
            
            inputHtml = `
                <select onchange="detailUpdateRowField('${rowId}', '${attr.name}', this.value)" 
                        style="width:100%;padding:8px;background:white;" class="input-field">
                    <option value="">업종 선택</option>
                    ${selectOptions}
                </select>
            `;
        } else if (attr.type === 'file') {
            // 파일 타입 속성 처리 (여러 파일 지원)
            let filesData = [];
            let hasFiles = false;
            
            // 파일 정보 파싱
            try {
                if (value && value !== null && value !== undefined) {
                    if (typeof value === 'object') {
                        // 단일 파일인 경우 배열로 변환
                        if (Array.isArray(value)) {
                            filesData = value;
                        } else {
                            filesData = [value];
                        }
                        hasFiles = true;
                    } else if (typeof value === 'string' && value.trim() !== '') {
                        if (value.trim().startsWith('[')) {
                            // JSON 배열
                            filesData = JSON.parse(value);
                        } else if (value.trim().startsWith('{')) {
                            // JSON 객체 (단일 파일)
                            filesData = [JSON.parse(value)];
                        } else {
                            // 문자열 (단일 파일명)
                            filesData = [{
                                original_filename: value.trim(),
                                type: 'file'
                            }];
                        }
                        hasFiles = true;
                    }
                }
            } catch (e) {
                console.error('파일 정보 파싱 오류:', e, 'value:', value);
                if (value) {
                    filesData = [{
                        original_filename: String(value),
                        type: 'file'
                    }];
                    hasFiles = true;
                }
            }
            
            if (hasFiles && filesData.length > 0) {
                // 여러 파일을 세로로 정렬하여 표시
                let filesHtml = '';
                
                filesData.forEach((fileInfo, index) => {
                    const displayFileName = fileInfo.original_filename || fileInfo.stored_filename || fileInfo.filename || 'unknown';
                    
                    // 디버깅: 각 파일 정보 로그
                    console.log(`파일 ${index}:`, fileInfo);
                    console.log(`파일 ${index} displayFileName:`, displayFileName);
                    
                    // 파일의 고유 ID 생성 (기존 ID가 없으면 stored_filename 사용)
                    const fileId = fileInfo.id || fileInfo.stored_filename || `file_${index}`;
                    
                    // 파일 타입별 처리
                    if (fileInfo.type === 'img' || fileInfo.content_type?.startsWith('image/')) {
                        filesHtml += `
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #000; border-radius: 4px; background: #f8f9fa;">
                                <span style="flex: 1; font-size: 14px;">📄 ${displayFileName}</span>
                                <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, id: fileId, field_name: attr.name, row_id: rowId}).replace(/\"/g, '&quot;')})"
                                        style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    미리보기
                                </button>
                                <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                        style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    다운로드
                                </button>
                                <button class="delete-file-btn" 
                                        data-row-id="${rowId}" 
                                        data-field-name="${attr.name}" 
                                        data-file-index="${index}"
                                        style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    삭제
                                </button>
                            </div>
                        `;
                    } else if (fileInfo.type === 'audio') {
                        filesHtml += `
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                <span style="flex: 1; font-size: 14px;">🎵 ${displayFileName}</span>
                                <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, id: fileId, field_name: attr.name, row_id: rowId}).replace(/\"/g, '&quot;')})"
                                        style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    미리보기
                                </button>
                                <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                        style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    다운로드
                                </button>
                                <button class="delete-file-btn" 
                                        data-row-id="${rowId}" 
                                        data-field-name="${attr.name}" 
                                        data-file-index="${index}"
                                        style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    삭제
                                </button>
                            </div>
                        `;
                    } else {
                        // 일반 파일
                        filesHtml += `
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                <span style="flex: 1; font-size: 14px;">📄 ${displayFileName}</span>
                                <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, field_name: attr.name, row_id: rowId}).replace(/\"/g, '&quot;')})"
                                        style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    미리보기
                                </button>
                                <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                        style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    다운로드
                                </button>
                                <button class="delete-file-btn" 
                                        data-row-id="${rowId}" 
                                        data-field-name="${attr.name}" 
                                        data-file-index="${index}"
                                        style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                    삭제
                                </button>
                            </div>
                        `;
                    }
                });
                
                // 파일 추가 버튼
                filesHtml += `
                    <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; background: #fff;">
                        <span style="flex: 1; color: #6c757d; font-size: 14px;">파일 추가</span>
                        <button type="button" 
                                onclick="document.getElementById('file_${attr.name}_${rowId}').click()" 
                                style="padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                            + 파일 추가
                        </button>
                        <input type="file" 
                               id="file_${attr.name}_${rowId}" 
                               style="display: none;"
                               onchange="uploadFile('${rowId}', '${attr.name}', this)">
                    </div>
                `;
                
                inputHtml = filesHtml;
            } else {
                // 파일이 없는 경우: 파일 선택 버튼 (다중 선택 지원)
                inputHtml = `
                    <div style="display: flex; align-items: center;">
                        <span style="flex: 1; color: #6c757d; font-size: 14px; padding: 8px 0;">파일이 선택되지 않았습니다</span>
                        <button type="button" 
                                onclick="document.getElementById('file_${attr.name}_${rowId}').click()" 
                                style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                            파일 선택
                        </button>
                        <input type="file" 
                               id="file_${attr.name}_${rowId}" 
                               style="display: none;"
                               onchange="uploadFile('${rowId}', '${attr.name}', this)">
                    </div>
                `;
            }
        } else if (attr.type === 'dropdown') {
            // value가 있을 때 색상 정보도 가져오기 위해 options를 fetch
            inputHtml = `<button type="button" class="add-btn" id="modal-dropdown-btn-${rowId}-${attr.name}" style="width:100%;background:#f8f9fa;color:#333;border:1px solid #eee;" onclick="openDetailDropdown('${rowId}','${attr.name}',this)">${value||'선택'}</button>`;
            // 옵션 색상 fetch 후 버튼 배경색 적용
            setTimeout(() => {
                fetch('/sales/dropdown_options/?field=' + encodeURIComponent(attr.name))
                    .then(r => r.json())
                    .then(data => {
                        console.log('dropdown_options 데이터:', data);
                        if (data.options) {
                            const opt = data.options.find(o => o.option === value);
                            const btn = document.getElementById(`modal-dropdown-btn-${rowId}-${attr.name}`);
                            if (btn && opt && opt.color) {
                                btn.style.background = hexToRgba(opt.color, 0.18);
                                btn.style.color = '#333';
                            }
                        }
                    });
            }, 0);
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
            inputHtml = `<input class="input-field" type="date" value="${dateValue}" data-field="${attr.name}" onchange="detailUpdateRowField('${rowId}', '${attr.name}', this.value)">`;
        } else if (attr.type === 'number') {
            inputHtml = `<input class="input-field" type="number" value="${value}" data-field="${attr.name}" onchange="detailUpdateRowField('${rowId}', '${attr.name}', this.value)">`;
        } else if (attr.type === 'age') {
            // 나이 필드 처리 - 달력과 체크박스 포함
            let ageData = {};
            let displayText = '';
            
            try {
                if (value && typeof value === 'string') {
                    ageData = JSON.parse(value);
                }
            } catch (e) {
                ageData = {};
            }
            
            // 현재 값에 따른 표시
            if (ageData.birth_date) {
                displayText = `생년월일: ${ageData.birth_date}`;
            } else if (ageData.age_range) {
                displayText = ageData.age_range === 'under40' ? '40세 미만' : '40세 이상';
            } else {
                displayText = '나이 정보 없음';
            }
            
            inputHtml = `
                <div style="border: 1px solid #b1b1b1; border-radius: 4px; padding: 12px; background: #fff;" data-field="${attr.name}" data-current-value='${JSON.stringify(ageData)}'>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <!-- 생년월일 입력 -->
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <label style="width: 80px; font-weight: bold; color: #495057;">생년월일:</label>
                            <input type="date" 
                                   id="birth_date_${rowId}" 
                                   value="${ageData.birth_date || ''}"
                                   style="flex: 1; padding: 8px; border: 1px solid #ced4da; border-radius: 4px;"
                                   onchange="updateAgeField('${rowId}', '${attr.name}', 'birth_date', this.value)">
                            
                            <!-- 연령대 체크박스 -->
                            <div style="display: flex; gap: 10px;">
                                <label style="display: flex; align-items: center; gap: 3px; cursor: pointer;">
                                    <input type="checkbox" 
                                           ${ageData.age_range === 'under40' ? 'checked' : ''}
                                           onchange="updateAgeField('${rowId}', '${attr.name}', 'age_range', this.checked ? 'under40' : '')"
                                           style="margin: 0; width: 12px; height: 12px;">
                                    <span style="font-size: 12px;">40세 미만</span>
                                </label>
                                <label style="display: flex; align-items: center; gap: 3px; cursor: pointer;">
                                    <input type="checkbox" 
                                           ${ageData.age_range === 'over40' ? 'checked' : ''}
                                           onchange="updateAgeField('${rowId}', '${attr.name}', 'age_range', this.checked ? 'over40' : '')"
                                           style="margin: 0; width: 12px; height: 12px;">
                                    <span style="font-size: 12px;">40세 이상</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (attr.type === 'multi_select') {
            // 다중 선택 필드 처리
            let selectedValues = [];
            try {
                if (value && typeof value === 'string') {
                    selectedValues = JSON.parse(value);
                } else if (Array.isArray(value)) {
                    selectedValues = value;
                }
            } catch (e) {
                selectedValues = [];
            }
            
            const displayText = selectedValues.length > 0 ? selectedValues.join(', ') : '선택';
            inputHtml = `<button type="button" class="add-btn" style="width:100%;background:#f8f9fa;color:#333;border:1px solid #eee;" onclick="openDetailDropdown('${rowId}','${attr.name}',this)">${displayText}</button>`;
        } else if (attr.type === 'recommend_biz') {
            // 지원사업 속성 값 가져오기
            const supportValue = rowData[attr.name] || attr.value;
            let supportDisplay = '';
            console.log('attr.name:', attr.name);
            console.log('rowData[attr.name]:', rowData[attr.name]);
            console.log('attr.value:', attr.value);
            console.log('supportValue:', supportValue);
            
            if (supportValue) {
                try {
                    let supportData;
                    console.log('supportValue type check:', typeof supportValue);
                    console.log('supportValue is object?', typeof supportValue === 'object');
                    console.log('supportValue is null?', supportValue === null);
                    console.log('supportValue raw value:', JSON.stringify(supportValue));
                    
                    if (typeof supportValue === 'string') {
                        // 문자열인 경우 JSON 파싱 시도
                        if (supportValue.trim().startsWith('{') && supportValue.trim().endsWith('}')) {
                            // Python 딕셔너리 형식이므로 빈 배열인지 확인
                            if (supportValue.includes("'pblanc_ids': []") && supportValue.includes("'알림': []")) {
                                supportData = { pblanc_ids: [], 알림: [] };
                                console.log('빈 딕셔너리 감지, 빈 객체로 초기화');
                            } else {
                                // 다른 값이 있는 경우에만 파싱 시도
                                try {
                                    const jsString = supportValue.replace(/'/g, '"');
                                    supportData = JSON.parse(jsString);
                                    console.log('Python 딕셔너리 파싱 성공:', supportData);
                                } catch (jsonError) {
                                    console.log('파싱 실패, 빈 객체로 초기화:', jsonError);
                                    supportData = { pblanc_ids: [], 알림: [] };
                                }
                            }
                        } else {
                            // 일반 쉼표 구분 문자열
                            const splitIds = supportValue.split(',').filter(id => id.trim());
                            supportData = { pblanc_ids: splitIds };
                        }
                    } else if (typeof supportValue === 'object' && supportValue !== null) {
                        // 이미 객체인 경우 (dict 형태)
                        supportData = supportValue;
                        console.log('이미 객체 형태 데이터:', supportData);
                    } else {
                        // 기타 타입인 경우 빈 객체로 초기화
                        supportData = { pblanc_ids: [], 알림: [] };
                    }
                    
                    const pblancIds = supportData.pblanc_ids || [];
                    console.log('최종 pblancIds:', pblancIds);
                    console.log('pblancIds.length:', pblancIds.length);
                    console.log('pblancIds type:', typeof pblancIds);
                    console.log('Array.isArray(pblancIds):', Array.isArray(pblancIds));
                    
                    const alerts = supportData.알림 || [];
                    console.log('alerts:', alerts);
                    console.log('alerts.length:', alerts.length);
                    
                    // 빈 배열 체크를 더 엄격하게
                    if (pblancIds && Array.isArray(pblancIds) && pblancIds.length > 0) {
                        supportDisplay = `신규 추천 공고: ${pblancIds.length}개`;
                        if (alerts && Array.isArray(alerts) && alerts.length > 0) {
                            supportDisplay += ` (새로운 공고: ${alerts.length}개)`;
                        }
                    } else {
                        supportDisplay = '신규 추천 공고 없음';
                    }
                } catch (e) {
                    console.error('supportValue 파싱 오류:', e);
                    supportDisplay = '데이터 오류';
                }
            } else {
                supportDisplay = '신규 추천 공고 없음';
            }
            
            inputHtml = `
                <div style="display: flex; gap: 10px; align-items: center;">
                    <div style="flex: 1; padding: 8px 12px; background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 4px; color: #333;">
                        ${supportDisplay}
                        ${(() => {
                            if (supportValue) {
                                try {
                                    let supportData;
                                    if (typeof supportValue === 'string') {
                                        supportData = { pblanc_ids: supportValue.split(',').filter(id => id.trim()) };
                                    } else if (typeof supportValue === 'object' && supportValue !== null) {
                                        // 이미 객체인 경우 그대로 사용
                                        supportData = supportValue;
                                    } else {
                                        supportData = { pblanc_ids: [] };
                                    }
                                    const alerts = supportData.알림 || [];
                                    return (alerts && Array.isArray(alerts) && alerts.length > 0) ? '<span style="color: #dc3545; font-weight: bold; margin-left: 8px;">🔔</span>' : '';
                                } catch (e) {
                                    return '';
                                }
                            }
                            return '';
                        })()}
                    </div>
                    <button type="button" class="btn btn-primary" onclick="openRecommendModal('${rowId}', 'view')" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        추천 지원사업 공고 보기
                    </button>
                    <button type="button" class="btn btn-success" onclick="openRecommendModal('${rowId}', 'recommend')" style="background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        추천받기
                    </button>
                </div>
            `;
        }
        
        else {
            // 기본 텍스트 필드
            if (attr.name === '신용점수') {
                // 신용점수 필드는 실시간 검증 추가
                inputHtml = `<input type="text" value="${value}" class="input-field" data-field="${attr.name}" 
                           onchange="detailUpdateRowField('${rowId}', '${attr.name}', this.value); highlightRequiredField(this, this.value && this.value !== '0' ? false : true);" 
                           oninput="highlightRequiredField(this, this.value && this.value !== '0' ? false : true);">`;
            } else {
                inputHtml = `<input class="input-field" type="text" value="${value}" data-field="${attr.name}" onchange="detailUpdateRowField('${rowId}', '${attr.name}', this.value)">`;
            }
        }
        
        // 지역 관련 필드가 아닌 경우에만 HTML에 추가
        if (attr.name !== '지역' && attr.name !== '상세지역') {
            // 라벨 색상 설정
            let labelColor = '#333'; // 기본 색상
            
            // 파란색 라벨 (지역, 기대출, 개업년월, 나이, 경력, 직원수)
            if (['기대출', '개업년월', '나이', '경력', '직원수'].includes(attr.name)) {
                labelColor = '#007bff';
            }
            // 붉은색 라벨 (매출, 신용점수, 업종)
            else if (['매출', '신용점수', '업종'].includes(attr.name)) {
                labelColor = '#dc3545';
            }
            
            html += `
                <div class="attribute-row" data-attribute-id="${attr.id}" data-attribute-name="${attr.name}" style="display:flex;align-items:center;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #eee;position:relative;">
                    <div class="drag-handle" style="position:absolute;left:-15px;top:50%;transform:translateY(-50%);color:#ccc;cursor:move;">⋮⋮</div>
                    <label class="attribute-label" style="width:120px;font-weight:bold;color:${labelColor};cursor:move;user-select:none;">
                        ${attr.name}
                        ${(() => {
                            if (attr.type === 'recommend_biz') {
                                const supportValue = rowData[attr.name] || attr.value;
                                if (supportValue) {
                                    try {
                                        let supportData;
                                        if (typeof supportValue === 'string') {
                                            supportData = { pblanc_ids: supportValue.split(',').filter(id => id.trim()) };
                                        } else if (typeof supportValue === 'object' && supportValue !== null) {
                                            // 이미 객체인 경우 그대로 사용
                                            supportData = supportValue;
                                        } else {
                                            supportData = { pblanc_ids: [] };
                                        }
                                        const alerts = supportData.알림 || [];
                                        return (alerts && Array.isArray(alerts) && alerts.length > 0) ? '<span style="color: #dc3545; font-weight: bold; margin-left: 8px;">🔔</span>' : '';
                                    } catch (e) {
                                        return '';
                                    }
                                }
                            }
                            return '';
                        })()}
                    </label>
                    <div style="flex:1;">${inputHtml}</div>
                </div>
            `;
        }
    });
    
    // 드래그 가능한 컨테이너 종료
    html += '</div>';
    
    // 상세정보 모달 내용 업데이트
    document.getElementById('detailModalContent').innerHTML = html;
    
    // 드래그앤드랍 이벤트 리스너 추가
    initializeDetailModalDragAndDrop();
    
    // 음성파일 영역 업데이트
    updateAudioFileSection(rowId, audioFileValue);

    console.log('window.innerWidth:', window.innerWidth);

    if (window.innerWidth < 1000) {
        document.querySelector('.detail-modal-content').style.flexDirection = 'column';
    }
    // 모달 표시
    document.getElementById('detailModal').style.display = 'flex';
    
    // 행 복제 버튼 재생성
    if (typeof recreateDuplicateButtons === 'function') {
        setTimeout(() => {
            recreateDuplicateButtons();
            console.log('상세보기 모달에서 행 복제 버튼 재생성 완료');
        }, 100);
    }
    
    // 파일 삭제 버튼 이벤트 리스너 추가 (setTimeout으로 지연)
    setTimeout(() => {
        const deleteButtons = document.querySelectorAll('.delete-file-btn');
        console.log('찾은 삭제 버튼 개수:', deleteButtons.length);
        
        deleteButtons.forEach((btn, index) => {
            console.log(`버튼 ${index}:`, btn);
            console.log(`버튼 ${index}의 data 속성:`, {
                rowId: btn.getAttribute('data-row-id'),
                fieldName: btn.getAttribute('data-field-name'),
                fileIndex: btn.getAttribute('data-file-index')
            });
            
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const rowId = this.getAttribute('data-row-id');
                const fieldName = this.getAttribute('data-field-name');
                const fileIndex = this.getAttribute('data-file-index');
                
                console.log('파일 삭제 버튼 클릭됨:', rowId, fieldName, fileIndex);
                console.log('fileIndex 타입:', typeof fileIndex);
                console.log('fileIndex 값:', fileIndex);
                
                // fileIndex를 숫자로 변환
                const numericFileIndex = parseInt(fileIndex, 10);
                console.log('변환된 fileIndex:', numericFileIndex);
                
                console.log('deleteFile 함수 호출 전');
                deleteFile(rowId, fieldName, numericFileIndex);
                console.log('deleteFile 함수 호출 후');
            });
        });

        const recommendViewBtn = document.querySelector(`button[onclick*="openRecommendModal('${rowId}', 'view')"]`);
        if (recommendViewBtn) {
            addNotificationToRecommendButton(rowId, recommendViewBtn);
        }
    }, 100);
}

// 상세보기 모달의 드래그앤드랍 기능 초기화
function initializeDetailModalDragAndDrop() {
    const container = document.getElementById('attributeContainer');
    if (!container) return;
    
    let draggedElement = null;
    let draggedOverElement = null;
    
    // 모든 드래그 가능한 요소에 이벤트 리스너 추가
    const attributeRows = container.querySelectorAll('.attribute-row');
    
    attributeRows.forEach(row => {
        // attribute-row의 draggable 속성을 false로 설정
        row.draggable = false;
        
        // 라벨 요소를 찾아서 드래그 가능하게 설정
        const label = row.querySelector('.attribute-label');
        const dragHandle = row.querySelector('.drag-handle');
        
        if (label) {
            label.draggable = true;
            label.style.cursor = 'move';
        }
        
        if (dragHandle) {
            dragHandle.draggable = true;
            dragHandle.style.cursor = 'move';
        }
        
        // 라벨과 드래그 핸들에만 드래그 시작 이벤트 추가
        [label, dragHandle].forEach(element => {
            if (element) {
                element.addEventListener('dragstart', function(e) {
                    draggedElement = row; // 실제로는 row 전체를 드래그 대상으로 설정
                    row.style.opacity = '0.5';
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/html', row.outerHTML);
                });
            }
        });
        
        row.addEventListener('dragend', function(e) {
            this.style.opacity = '';
            draggedElement = null;
            draggedOverElement = null;
            
            // 모든 드래그 오버 스타일 제거
            attributeRows.forEach(r => {
                r.style.borderTop = '';
                r.style.borderBottom = '';
            });
        });
        
        row.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            if (draggedElement && this !== draggedElement) {
                // 드래그 오버 시각적 피드백
                const rect = this.getBoundingClientRect();
                const midY = rect.top + rect.height / 2;
                
                if (e.clientY < midY) {
                    this.style.borderTop = '2px solid #007bff';
                    this.style.borderBottom = '';
                } else {
                    this.style.borderTop = '';
                    this.style.borderBottom = '2px solid #007bff';
                }
                draggedOverElement = this;
            }
        });
        
        row.addEventListener('dragleave', function(e) {
            // 마우스가 완전히 요소를 벗어날 때만 스타일 제거
            const rect = this.getBoundingClientRect();
            if (e.clientX < rect.left || e.clientX > rect.right || 
                e.clientY < rect.top || e.clientY > rect.bottom) {
                this.style.borderTop = '';
                this.style.borderBottom = '';
            }
        });
        
        row.addEventListener('drop', function(e) {
            e.preventDefault();
            
            if (draggedElement && this !== draggedElement) {
                const rect = this.getBoundingClientRect();
                const midY = rect.top + rect.height / 2;
                
                if (e.clientY < midY) {
                    // 위쪽에 삽입
                    container.insertBefore(draggedElement, this);
                } else {
                    // 아래쪽에 삽입
                    container.insertBefore(draggedElement, this.nextSibling);
                }
                
                // 순서 변경 사항을 서버에 저장
                saveDetailSortOrder();
            }
            
            // 드래그 스타일 정리
            this.style.borderTop = '';
            this.style.borderBottom = '';
        });
    });
}

// 상세보기 모달의 속성 순서를 서버에 저장
function saveDetailSortOrder() {
    const container = document.getElementById('attributeContainer');
    if (!container) return;
    
    const attributeRows = container.querySelectorAll('.attribute-row');
    const attributeOrders = [];
    
    attributeRows.forEach((row, index) => {
        const attributeId = row.getAttribute('data-attribute-id');
        if (attributeId) {
            attributeOrders.push({
                id: parseInt(attributeId),
                detail_sort_order: index
            });
        }
    });
    
    // 서버에 순서 업데이트 요청
    fetch('/sales/update_detail_sort_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            attribute_orders: attributeOrders
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('상세보기 속성 순서가 저장되었습니다.');
            // 캐시 무효화
            userAttributesCache = null;
            attributesCacheTimestamp = null;
        } else {
            console.error('속성 순서 저장 실패:', data.error);
            alert('속성 순서 저장에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('속성 순서 저장 오류:', error);
        alert('속성 순서 저장 중 오류가 발생했습니다.');
    });
}

// 한국어 통화 단위로 업데이트하는 함수
function detailUpdateRowFieldWithKoreanCurrency(rowId, fieldName, value) {
    // 입력값에서 숫자만 추출
    const cleanValue = value.replace(/[^\d]/g, '');
    const numericValue = parseInt(cleanValue) || 0;
    
    // 한국어 단위로 표시
    const koreanValue = formatToKoreanCurrency(numericValue);
    
    // 입력 필드에 한국어 단위로 표시
    const inputElement = document.querySelector(`input[data-field="${fieldName}"]`);
    if (inputElement) {
        inputElement.value = koreanValue;
    }
    
    // 서버에 숫자 값으로 저장
    fetch('/sales/update_row_field/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            row_id: rowId,
            field_name: fieldName,
            value: numericValue
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('매출 정보가 업데이트되었습니다.');
            
            // 테이블과 칸반보드 새로고침
            if (typeof refreshTable === 'function') {
                refreshTable();
            }
            
            // 종속된 행들 업데이트
            if (typeof updateDependentRows === 'function') {
                updateDependentRows(rowId, fieldName, numericValue);
            }
        } else {
            console.error('매출 업데이트 실패:', data.error);
            showNotification('매출 정보 업데이트에 실패했습니다.', 'error');
        }
    })
    .catch(error => {
        console.error('매출 업데이트 오류:', error);
        showNotification('매출 정보 업데이트 중 오류가 발생했습니다.', 'error');
    });
}









// 모달용 지역 옵션 선택 함수
function selectModalRegionOption(rowId, regionText, element) {
  // 서버에 업데이트 요청
  fetch('/sales/update_row_field/', {
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
              '세종': ['세종특별자치시'],
              '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
              '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
              '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
              '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
              '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군'],
              '경북': ['포항시','경주시','김천시','안동시','구미시','영주시','영천시','상주시','문경시','경산시','군위군','의성군','청송군','영양군','영덕군','청도군','고령군','성주군','칠곡군','예천군','봉화군','울진군','울릉군'],
              '경남': ['창원시','진주시','통영시','사천시','김해시','밀양시','거제시','양산시','의령군','함안군','창녕군','고성군','남해군','하동군','산청군','함양군','거창군','합천군']
          };
          
          const firstSubregion = (regionMap[regionText] || [])[0] || '';
          if (firstSubregion) {
              // 상세지역도 함께 업데이트
              fetch('/sales/update_row_field/', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'id=' + encodeURIComponent(rowId) + '&field=상세지역&value=' + encodeURIComponent(firstSubregion)
              })
              .then(r => r.json())
              .then(function(data) {
                  if (data.success) {
                      // 모달 새로고침
                      fetch('/sales/get_row_details/' + rowId + '/')
                          .then(r => r.json())
                          .then(function(data) {
                              if (data.success) {
                                  showDetailModal(data.row_data, data.row_id);
                              }
                          });
                          
                      // 테이블 실시간 업데이트
                      if (typeof refreshTable === 'function') {
                          refreshTable();
                      }
                      
                      // 칸반보드 실시간 업데이트 - 지역 또는 상세지역이 현재 칸반보드 속성과 일치하는 경우
                      const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
                          document.getElementById('kanbanAttributeSelect').value : 
                          window.SELECTED_KANBAN_ATTR || window.kanbanAttribute;
                          
                      if (currentKanbanAttr && ('지역' === currentKanbanAttr || '상세지역' === currentKanbanAttr)) {
                          if (typeof refreshKanban === 'function') {
                              refreshKanban();
                          }
                      }
                      checkKanbanAndRefresh('지역');
                  }
              });
          } else {
              // 상세지역이 없는 경우에도 테이블과 칸반보드 업데이트
              // 테이블 실시간 업데이트
              if (typeof refreshTable === 'function') {
                  refreshTable();
              }
              
              // 칸반보드 실시간 업데이트
              const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
                  document.getElementById('kanbanAttributeSelect').value : 
                  window.SELECTED_KANBAN_ATTR || window.kanbanAttribute;
                  
              if (currentKanbanAttr && '상세지역' === currentKanbanAttr) {
                  if (typeof refreshKanban === 'function') {
                      refreshKanban();
                  }
              }
              checkKanbanAndRefresh('상세지역');
          }
      } else {
          alert('수정 실패: ' + (data.error || ''));
      }
  });
}

// 모달용 상세지역 옵션 선택 함수
function selectModalSubregionOption(rowId, subregionText, element) {
  // 서버에 업데이트 요청
  fetch('/sales/update_row_field/', {
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
          fetch('/sales/get_row_details/' + rowId + '/')
              .then(r => r.json())
              .then(function(data) {
                  if (data.success) {
                      showDetailModal(data.row_data, data.row_id);
                  }
              });
              
          // 테이블 실시간 업데이트
          if (typeof refreshTable === 'function') {
              refreshTable();
          }
          
          // 칸반보드 실시간 업데이트 - 상세지역이 현재 칸반보드 속성과 일치하는 경우
          const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
              document.getElementById('kanbanAttributeSelect').value : 
              window.SELECTED_KANBAN_ATTR || window.kanbanAttribute;
              
          if (currentKanbanAttr && '상세지역' === currentKanbanAttr) {
              if (typeof refreshKanban === 'function') {
                  refreshKanban();
              }
          }
          window.triggerKanbanRefreshIfNeeded();
      } else {
          alert('수정 실패: ' + (data.error || ''));
      }
  });
}

// 모달에서 변경사항이 있었는지 추적하는 전역 변수
window.modalHasChanges = false;

function closeDetailModal() {
  document.getElementById('detailModal').style.display = 'none';
  
  // 전역 변수 초기화
  window.currentDetailRowId = null;
  window.currentTextAttributeName = null;
  window.currentAudioFileInfo = null;
  
  // 변경사항이 있었을 때만 새로고침 실행
  if (window.modalHasChanges) {
    setTimeout(() => {
      // 테이블 새로고침 (필요한 경우에만)
      if (typeof refreshTable === 'function') {
        refreshTable();
      }
      
      // 칸반보드 새로고침 (필요한 경우에만)
      if (typeof refreshKanban === 'function') {
        refreshKanban();
      }
      
      // 캘린더 새로고침 (필요한 경우에만)
      if (window.calendar && typeof window.calendar.refetchEvents === 'function') {
        window.calendar.refetchEvents();
      }
      
      // 테이블 새로고침 후 추가 초기화 작업
      setTimeout(() => {
        // Sticky 헤더 재초기화
        if (typeof initializeStickyHeader === 'function') {
          initializeStickyHeader();
          console.log('상세 모달 닫기 후 Sticky 헤더 재초기화 완료');
          
          // 추가로 약간의 지연 후 한 번 더 시도 (DOM 완전 렌더링 보장)
          setTimeout(() => {
            initializeStickyHeader();
            console.log('상세 모달 닫기 후 Sticky 헤더 재초기화 재시도 완료');
          }, 150);
        }
        
        // 컬럼 드래그앤드롭 재초기화
        if (typeof initializeColumnDragDrop === 'function') {
          initializeColumnDragDrop(true); // force=true로 강제 재초기화
          console.log('상세 모달 닫기 후 컬럼 드래그앤드롭 재초기화 완료');
        }
        
        // 테이블 셀 이벤트 재바인딩
        if (typeof bindTableCellEvents === 'function') {
          bindTableCellEvents();
          console.log('상세 모달 닫기 후 테이블 셀 이벤트 재바인딩 완료');
        }
        
        // 체크박스와 상세보기 버튼 이벤트 재바인딩
        if (typeof bindCheckboxEvents === 'function') {
          bindCheckboxEvents();
          console.log('상세 모달 닫기 후 체크박스 이벤트 재바인딩 완료');
        }
        
        if (typeof bindDetailButtonEvents === 'function') {
          setTimeout(() => {
              console.log('상세 모달 닫기 후 상세보기 버튼 이벤트 바인딩 시작...');
              bindDetailButtonEvents();
              console.log('상세 모달 닫기 후 상세보기 버튼 이벤트 바인딩 완료');
          }, 200);
        }
        
        // 드롭다운 pill 렌더링
        if (typeof renderDropdownPills === 'function') {
          renderDropdownPills();
          console.log('상세 모달 닫기 후 드롭다운 pill 렌더링 완료');
        }
        
        // 행 복제 버튼과 상세보기 버튼 재생성
        if (typeof recreateDuplicateButtons === 'function') {
          recreateDuplicateButtons();
          console.log('상세 모달 닫기 후 행 복제 버튼과 상세보기 버튼 재생성 완료');
        }
        
        // 행 드래그앤드롭 재초기화
        if (typeof reinitializeRowDragDrop === 'function') {
          reinitializeRowDragDrop();
          console.log('상세 모달 닫기 후 행 드래그앤드롭 재초기화 완료');
        }
      }, 200); // 테이블 새로고침 완료 후 200ms 지연
      
      // 변경사항 플래그 리셋
      window.modalHasChanges = false;
    }, 100); // 100ms 지연으로 사용자가 즉시 다른 모달을 열 수 있도록 함
  }
}

// 기대출 필드 업데이트 함수
function updateDebtField(rowId, debtKey, value) {
    // 입력값에서 숫자만 추출
    const cleanValue = value.replace(/[^\d]/g, '');
    const numericValue = parseInt(cleanValue) || 0;
    
    // 전역 debtData에 업데이트 (만원 단위로 저장)
    if (!window.debtData) {
        window.debtData = {};
    }
    window.debtData[debtKey] = numericValue;
    
    // 합계 계산 (만원 단위)
    const totalAmount = Object.values(window.debtData).reduce((sum, val) => sum + (parseInt(val) || 0), 0);
    const totalDisplayValue = totalAmount ? `${totalAmount}만원` : '0만원';
    
    // 합계 표시 업데이트
    const totalElement = document.getElementById(`debt_total_${rowId}`);
    if (totalElement) {
        totalElement.textContent = totalDisplayValue;
    }
    
    // 서버에 저장
    fetch('/sales/update_debt_field/', {
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


// 추천자금 요청 함수
function requestFundingRecommendation(rowId) {
    console.log('=== 추천자금 요청 시작 ===');
    console.log('Row ID:', rowId);
    
    // 필수값 검증
    const requiredFields = ['신용점수', '업종', '매출'];
    const missingFields = [];
    
    console.log('필수 필드 목록:', requiredFields);
    
    // 현재 열린 상세 모달에서 필수값 확인
    const detailModal = document.getElementById('detailModal');
    console.log('상세 모달 상태:', {
        exists: !!detailModal,
        display: detailModal ? detailModal.style.display : 'N/A'
    });
    
    if (detailModal && detailModal.style.display !== 'none') {
        console.log('모달이 열려있음 - 모달 내 검증 시작');
        
        // 모달이 열려있는 경우 모달 내의 값들을 확인
        for (const fieldName of requiredFields) {
            console.log(`\n--- ${fieldName} 필드 검증 시작 ---`);
            
            const fieldElement = detailModal.querySelector(`[data-field="${fieldName}"]`);
            console.log(`${fieldName} 필드 요소:`, {
                found: !!fieldElement,
                element: fieldElement
            });
            
            if (fieldElement) {
                const value = fieldElement.value;
                console.log(`${fieldName} 값:`, value);
                
                // 매출 필드는 특별한 필드로 처리해야 함
                if (fieldName === '매출' && fieldElement.classList.contains('sales-field-container')) {
                    console.log(`${fieldName} - 특별한 필드로 재분류`);
                    // 특별한 필드 처리로 넘어가기 위해 continue
                    continue;
                }
                
                if (!value || value.trim() === '' || value === '0' || value === '선택' || value === '클릭하여 입력') {
                    console.log(`${fieldName} - 누락됨 (일반 필드)`);
                    missingFields.push(fieldName);
                    // 빨간 테두리 표시
                    highlightRequiredField(fieldElement, true);
                } else {
                    console.log(`${fieldName} - 정상 (일반 필드)`);
                    // 정상인 경우 원래 스타일로 복원
                    highlightRequiredField(fieldElement, false);
                }
            } else {
                console.log(`${fieldName} - 특별한 필드 처리 시작`);
                
                // 특별한 필드들 처리
                if (fieldName === '매출') {
                    console.log('매출 필드 특별 처리 시작');
                    
                    // sales-field-container를 직접 찾기
                    const salesContainer = detailModal.querySelector('.sales-field-container[data-field="매출"]');
                    const salesInput = detailModal.querySelector('input[data-field="매출"]');
                    
                    console.log('매출 필드 검색 결과:', {
                        salesContainer: !!salesContainer,
                        salesInput: !!salesInput
                    });
                    
                    if (salesContainer) {
                        const rawValue = salesContainer.getAttribute('data-raw');
                        const displayText = salesContainer.textContent.trim();
                        
                        console.log('매출 컨테이너 검증 디버깅:', {
                            rawValue: rawValue,
                            displayText: displayText,
                            hasDataRaw: salesContainer.hasAttribute('data-raw'),
                            containerHTML: salesContainer.innerHTML
                        });
                        
                        // 더 정확한 검증 로직
                        const hasValidValue = (
                            rawValue && 
                            rawValue !== '' && 
                            !isNaN(parseInt(rawValue, 10)) && 
                            parseInt(rawValue, 10) >= 0 &&
                            !displayText.includes('클릭하여 입력') &&
                            displayText !== ''
                        );
                        
                        console.log('매출 컨테이너 유효성 검사 결과:', hasValidValue);
                        
                        if (!hasValidValue) {
                            console.log('매출 - 누락됨 (컨테이너)');
                            missingFields.push(fieldName);
                            // 빨간 테두리 표시
                            highlightRequiredField(salesContainer, true);
                        } else {
                            console.log('매출 - 정상 (컨테이너)');
                            // 정상인 경우 원래 스타일로 복원
                            highlightRequiredField(salesContainer, false);
                        }
                    } else if (salesInput) {
                        // input 형태의 매출 필드 처리
                        const inputValue = salesInput.value.trim();
                        console.log('매출 input 검증 디버깅:', {
                            inputValue: inputValue,
                            inputType: salesInput.type
                        });
                        
                        const hasValidInputValue = (
                            inputValue && 
                            inputValue !== '0' && 
                            inputValue !== '' && 
                            !isNaN(parseInt(inputValue.replace(/[^\d]/g, ''), 10)) && 
                            parseInt(inputValue.replace(/[^\d]/g, ''), 10) > 0
                        );
                        
                        console.log('매출 input 유효성 검사 결과:', hasValidInputValue);
                        
                        if (!hasValidInputValue) {
                            console.log('매출 - 누락됨 (input)');
                            missingFields.push(fieldName);
                            // 빨간 테두리 표시
                            highlightRequiredField(salesInput, true);
                        } else {
                            console.log('매출 - 정상 (input)');
                            // 정상인 경우 원래 스타일로 복원
                            highlightRequiredField(salesInput, false);
                        }
                    } else {
                        console.log('매출 필드를 찾을 수 없음');
                        missingFields.push(fieldName);
                    }
                } else if (fieldName === '업종') {
                    console.log('업종 필드 특별 처리 시작');
                    
                    const industrySelect = detailModal.querySelector('select[onchange*="업종"]');
                    console.log('업종 select 요소:', {
                        found: !!industrySelect,
                        value: industrySelect ? industrySelect.value : 'N/A'
                    });
                    
                    if (industrySelect && (!industrySelect.value || industrySelect.value === '')) {
                        console.log('업종 - 누락됨');
                        missingFields.push(fieldName);
                        // 빨간 테두리 표시
                        highlightRequiredField(industrySelect, true);
                    } else if (industrySelect) {
                        console.log('업종 - 정상');
                        // 정상인 경우 원래 스타일로 복원
                        highlightRequiredField(industrySelect, false);
                    } else {
                        console.log('업종 select를 찾을 수 없음');
                        missingFields.push(fieldName);
                    }
                } else if (fieldName === '신용점수') {
                    console.log('신용점수 필드 특별 처리 시작');
                    
                    const creditScoreInput = detailModal.querySelector('input[data-field="신용점수"]');
                    console.log('신용점수 input 요소:', {
                        found: !!creditScoreInput,
                        value: creditScoreInput ? creditScoreInput.value : 'N/A'
                    });
                    
                    if (creditScoreInput && (!creditScoreInput.value || creditScoreInput.value === '0' || creditScoreInput.value.trim() === '')) {
                        console.log('신용점수 - 누락됨');
                        missingFields.push(fieldName);
                        // 빨간 테두리 표시
                        highlightRequiredField(creditScoreInput, true);
                    } else if (creditScoreInput) {
                        console.log('신용점수 - 정상');
                        // 정상인 경우 원래 스타일로 복원
                        highlightRequiredField(creditScoreInput, false);
                    } else {
                        console.log('신용점수 input을 찾을 수 없음');
                        missingFields.push(fieldName);
                    }
                } else {
                    console.log(`${fieldName} - 특별 처리 없음, 누락으로 처리`);
                    missingFields.push(fieldName);
                }
            }
        }
        
        console.log('\n=== 모달 내 검증 완료 ===');
        console.log('누락된 필드들:', missingFields);
        
    } else {
        console.log('모달이 닫혀있음 - 서버에서 데이터 가져와서 검증');
        
        // 모달이 닫혀있는 경우 서버에서 데이터를 가져와서 확인
        fetch(`/sales/get_row_details/${rowId}/`)
            .then(response => response.json())
            .then(data => {
                console.log('서버 응답:', data);
                
                if (data.success) {
                    const rowData = data.row_data;
                    console.log('행 데이터:', rowData);
                    
                    // 필수값 확인
                    if (!rowData['신용점수'] || rowData['신용점수'] === '0' || rowData['신용점수'] === '') {
                        missingFields.push('신용점수');
                    }
                    if (!rowData['업종'] || rowData['업종'] === '') {
                        missingFields.push('업종');
                    }
                    
                    // 매출 검증 로직 개선
                    const revenueValue = rowData['매출'];
                    const hasValidRevenue = (
                        revenueValue && 
                        revenueValue !== '' && 
                        !isNaN(parseInt(revenueValue, 10)) && 
                        parseInt(revenueValue, 10) >= 0
                    );
                    
                    if (!hasValidRevenue) {
                        missingFields.push('매출');
                    }
                    
                    console.log('서버 검증 결과 - 누락된 필드들:', missingFields);
                    
                    // 필수값이 누락된 경우 알림 표시
                    if (missingFields.length > 0) {
                        showNotification(`다음 필수 항목을 입력해주세요: ${missingFields.join(', ')}`, 'error');
                        return;
                    }
                    
                    // 모든 필수값이 있으면 추천 요청 진행
                    proceedWithFundingRecommendation(rowId);
                } else {
                    showNotification('데이터를 가져올 수 없습니다.', 'error');
                }
            })
            .catch(error => {
                console.error('필수값 검증 중 오류:', error);
                showNotification('필수값 검증 중 오류가 발생했습니다.', 'error');
            });
        return;
    }
    
    // 모달이 열려있는 경우 즉시 검증
    console.log('\n=== 최종 검증 결과 ===');
    console.log('누락된 필드들:', missingFields);
    
    if (missingFields.length > 0) {
        console.log('필수값 누락 - 알림 표시');
        showNotification(`다음 필수 항목을 입력해주세요: ${missingFields.join(', ')}`, 'error');
        return;
    }
    
    console.log('모든 필수값 확인됨 - 추천 요청 진행');
    // 모든 필수값이 있으면 추천 요청 진행
    proceedWithFundingRecommendation(rowId);
}

// 필수 필드 하이라이트 함수
function highlightRequiredField(element, isError) {
    if (!element) return;
    
    if (isError) {
        // 빨간 테두리와 배경색 적용
        element.style.border = '2px solid #dc3545';
        element.style.boxShadow = '0 0 5px rgba(220, 53, 69, 0.3)';
        element.style.backgroundColor = '#fff5f5';
        
        // 애니메이션 효과 추가
        element.style.animation = 'shake 0.5s ease-in-out';
        
        // 3초 후 자동으로 스타일 제거
        setTimeout(() => {
            if (element.style.border === '2px solid #dc3545') {
                element.style.border = '';
                element.style.boxShadow = '';
                element.style.backgroundColor = '';
                element.style.animation = '';
            }
        }, 3000);
    } else {
        // 정상 상태로 복원
        element.style.border = '';
        element.style.boxShadow = '';
        element.style.backgroundColor = '';
        element.style.animation = '';
    }
}

// CSS 애니메이션 추가 (페이지 로드 시)
document.addEventListener('DOMContentLoaded', function() {
    // shake 애니메이션 CSS 추가
    if (!document.getElementById('required-field-animation')) {
        const style = document.createElement('style');
        style.id = 'required-field-animation';
        style.textContent = `
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
                20%, 40%, 60%, 80% { transform: translateX(2px); }
            }
        `;
        document.head.appendChild(style);
    }
});

// 실제 추천자금 요청을 처리하는 함수
function proceedWithFundingRecommendation(rowId) {
    // 로딩 상태 표시
    showNotification('추천자금을 분석 중입니다...', 'info');
    
    // 백엔드에 추천자금 요청
    fetch('/sales/get_funding_recommendation/', {
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
            
            // 백엔드 응답 구조에 맞게 데이터 변환
            const recommendation = {
                total_amount: parseInt(data.total_recommended_amount.replace(/[,원]/g, '')),
                individual_funds: data.individual_funds || [],
                analysis_summary: data.analysis_summary,
                engine_info: data.engine_info || {},
                detailed_funds: {},
                exclusion_notes: data.analysis_summary?.exclusion_notes || [],
                recommended_notices: data.recommended_notices || []
            };
            
            // individual_funds에서 detailed_funds 생성
            if (data.individual_funds) {
                data.individual_funds.forEach(fund => {
                    recommendation.detailed_funds[fund.fund_name] = fund.limit;
                });
            }
            
            // 추천 결과를 모달로 표시
            showFundingRecommendationModal(recommendation, data);
            
            // 현재 열린 상세 모달이 있다면 백그라운드에서 조용히 새로고침 (깜빡임 방지)
            const existingDetailModal = document.querySelector('#detailModal');
            if (existingDetailModal) {
                // 서버에서 최신 데이터를 가져와서 백그라운드에서 준비 (모달은 닫지 않음)
                fetch(`/sales/get_row_details/${rowId}/`)
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
            window.triggerKanbanRefreshIfNeeded();
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
    console.log('showFundingRecommendationModal, 디테일')
    // 기존 모달이 있으면 제거
    const existingModal = document.getElementById('fundingRecommendationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 결과 데이터 준비
    const result = recommendation;
    
    console.log('모달 표시를 위한 결과 데이터:', result);
    
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
                max-width: 900px;
                width: 95%;
                max-height: 85vh;
                overflow-y: auto;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            ">
                <h2 style="margin: 0 0 20px 0; color: #333; text-align: center;">정책자금 추천 분석 결과</h2>
                
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
                    <div style="font-size: 32px; font-weight: bold;">
                        ${(result.total_amount || 0).toLocaleString()}원
                    </div>
                    <div style="font-size: 14px; opacity: 0.9; margin-top: 10px;">
                        다양한 정책자금을 통해 기업 성장을 지원합니다
                    </div>
                </div>
                
                <!-- 개별 자금 추천 내역 -->
                ${result.individual_funds && result.individual_funds.length > 0 ? `
                <div style="margin-bottom: 25px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 8px;">
                        💰 개별 자금 추천 내역 (${result.individual_funds.length}개)
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px;">
                        ${result.individual_funds.map((fund, index) => `
                            <div style="
                                background: #f8f9fa;
                                border: 1px solid #e9ecef;
                                border-radius: 8px;
                                padding: 20px;
                                position: relative;
                                transition: transform 0.2s;
                            " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                <div style="
                                    position: absolute;
                                    top: 10px;
                                    right: 15px;
                                    background: #007bff;
                                    color: white;
                                    padding: 4px 8px;
                                    border-radius: 12px;
                                    font-size: 12px;
                                    font-weight: bold;
                                ">
                                    가능자금 ${index + 1}
                                </div>
                                <div style="font-weight: bold; color: #495057; margin-bottom: 8px; margin-right: 60px;">
                                    ${fund.fund_name}
                                </div>
                                <div style="font-size: 20px; font-weight: bold; color: #007bff; margin-bottom: 10px;">
                                    ${(fund.limit || 0).toLocaleString()}원
                                </div>
                                <div style="color: #6c757d; font-size: 13px; margin-bottom: 8px;">
                                    <strong>기관:</strong> ${fund.institution || '정부기관'}
                                </div>
                                <div style="color: #6c757d; font-size: 13px; margin-bottom: 8px;">
                                    <strong>금리:</strong> ${fund.interest_rate || '3.0~6.0%'}
                                </div>
                                <div style="color: #6c757d; font-size: 13px; margin-bottom: 8px;">
                                    <strong>처리기간:</strong> ${fund.processing_time || '2-4주'}
                                </div>
                                ${fund.calculation_note ? `
                                <div style="
                                    background: #fff3cd;
                                    border: 1px solid #ffeaa7;
                                    border-radius: 4px;
                                    padding: 8px;
                                    margin-top: 10px;
                                    font-size: 12px;
                                    color: #856404;
                                ">
                                    💡 ${fund.calculation_note}
                                </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : `
                <div style="margin-bottom: 25px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 8px;">
                        💰 개별 자금 추천 내역
                    </h4>
                    <div style="
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        color: #6c757d;
                    ">
                        현재 기업 상황으로는 추가 추천 가능한 자금이 없습니다.
                    </div>
                </div>
                `}
                
                <!-- 상세 자금 내역 (카테고리별) -->
                ${result.detailed_funds && Object.keys(result.detailed_funds).length > 0 ? `
                <div style="margin-bottom: 25px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 8px;">
                        📊 카테고리별 자금 내역
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                        ${Object.entries(result.detailed_funds).map(([fundName, amount]) => `
                            <div style="
                                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                border: 1px solid #dee2e6;
                                border-radius: 6px;
                                padding: 15px;
                                text-align: center;
                            ">
                                <div style="font-weight: bold; color: #495057; margin-bottom: 8px; font-size: 14px;">
                                    ${fundName}
                                </div>
                                <div style="font-size: 16px; font-weight: bold; color: #28a745;">
                                    ${amount.toLocaleString()}원
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <!-- 공고 추천 -->
                ${result.recommended_notices && result.recommended_notices.length > 0 ? `
                <div style="margin-bottom: 25px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 8px;">
                        📢 맞춤 공고 추천 (${result.recommended_notices.length}개)
                    </h4>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        ${result.recommended_notices.map(notice => `
                            <div onclick="window.open('/board/detail/${notice.pblanc_id}/', '_blank')" style="
                                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                border: 1px solid #dee2e6;
                                border-radius: 8px;
                                padding: 16px;
                                cursor: pointer;
                                transition: all 0.2s ease;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.15)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'">
                                <div style="font-weight: bold; color: #495057; margin-bottom: 8px; font-size: 15px; line-height: 1.4;">
                                    ${notice.title}
                                </div>
                                <div style="color: #6c757d; font-size: 13px; margin-bottom: 4px;">
                                    <strong>기관:</strong> ${notice.institution}
                                </div>
                                <div style="color: #6c757d; font-size: 13px; margin-bottom: 4px;">
                                    <strong>접수기간:</strong> ${notice.apply_period}
                                </div>
                                <div style="color: #6c757d; font-size: 13px;">
                                    <strong>지원내용:</strong> ${notice.support_amount}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : `
                <div style="margin-bottom: 25px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 8px;">
                        📢 맞춤 공고 추천
                    </h4>
                    <div style="
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        color: #6c757d;
                    ">
                        현재 조건에 맞는 공고가 없습니다.
                    </div>
                </div>
                `}
                
                <!-- 제외된 자금 정보 -->
                ${result.exclusion_notes && result.exclusion_notes.length > 0 ? `
                <div style="margin-bottom: 25px;">
                    <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #dc3545; padding-bottom: 8px;">
                        ⚠️ 신청 불가 자금 (${result.exclusion_notes.length}개)
                    </h4>
                    <div style="space-y: 8px;">
                        ${result.exclusion_notes.map(note => `
                            <div style="
                                background: #f8d7da;
                                border: 1px solid #f5c6cb;
                                border-radius: 6px;
                                padding: 12px;
                                margin-bottom: 8px;
                                color: #721c24;
                                font-size: 14px;
                            ">
                                ${note}
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <!-- 추가 정보 -->
                <div style="
                    background: #d1ecf1;
                    border: 1px solid #bee5eb;
                    border-radius: 6px;
                    padding: 15px;
                    margin-bottom: 20px;
                    font-size: 14px;
                    color: #0c5460;
                ">
                    <strong>💡 안내사항:</strong><br>
                    • 추천 금액은 현재 기업 상황을 기반으로 한 예상 금액입니다.<br>
                    • 실제 승인 금액은 심사 과정에서 달라질 수 있습니다.<br>
                    • 자세한 신청 조건은 각 기관에 문의하시기 바랍니다.
                </div>
                
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
                        transition: background-color 0.2s;
                    " onmouseover="this.style.backgroundColor='#5a6268'" onmouseout="this.style.backgroundColor='#6c757d'">닫기</button>
                    <button onclick="closeFundingRecommendationModal(); refreshTable(); refreshKanban();" style="
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 16px;
                        transition: background-color 0.2s;
                    " onmouseover="this.style.backgroundColor='#0056b3'" onmouseout="this.style.backgroundColor='#007bff'">확인</button>
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
    console.log('closeFundingRecommendationModal, 디테일')
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
    console.log('showFundingDetailModal, 디테일')
    // 서버에서 행 데이터 가져오기
    fetch(`/sales/get_row_details/${rowId}/`)
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
                } else if (fundingDataStr && typeof fundingDataStr === 'object') {
                    fundingData = fundingDataStr;
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
            
            console.log('상세보기 자금 데이터:', fundingData);
            
            // pblanc_ids가 있으면 공고 정보를 서버에서 가져오기
            let recommendedNoticesPromise = Promise.resolve([]);
            if (fundingData.pblanc_ids && fundingData.pblanc_ids.length > 0) {
                recommendedNoticesPromise = fetch('/sales/get_recommended_notices/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        pblanc_ids: fundingData.pblanc_ids
                    })
                })
                .then(response => response.json())
                .then(data => data.success ? data.recommended_notices : [])
                .catch(error => {
                    console.error('공고 정보 가져오기 실패:', error);
                    return [];
                });
            }
            
            // 공고 정보를 가져온 후 모달 표시
            recommendedNoticesPromise.then(recommendedNotices => {
                // 기존 모달이 있으면 제거
                const existingModal = document.getElementById('fundingDetailModal');
                if (existingModal) {
                    existingModal.remove();
                }
                
                // 데이터 구조 정규화 - 추천받기와 동일한 형태로 변환
                let normalizedData = {
                    total_amount: 0,
                    individual_funds: [],
                    detailed_funds: {},
                    analysis_summary: null,
                    engine_info: { version: '정책자금 추천 엔진 V2.0' },
                    exclusion_notes: [],
                    recommended_notices: recommendedNotices
                };
                
                // 저장된 데이터에서 값 추출
                if (fundingData.total_amount) {
                    normalizedData.total_amount = fundingData.total_amount;
                } else if (fundingData['총자금']) {
                    normalizedData.total_amount = fundingData['총자금'];
                }
                
                // individual_funds가 있으면 사용
                if (fundingData.individual_funds && Array.isArray(fundingData.individual_funds)) {
                    normalizedData.individual_funds = fundingData.individual_funds;
                } else if (fundingData['자금들']) {
                    // 레거시 데이터를 individual_funds 형태로 변환
                    normalizedData.individual_funds = Object.entries(fundingData['자금들']).map(([name, amount], index) => ({
                        fund_name: name,
                        limit: amount,
                        priority: index + 1,
                        institution: '정부기관',
                        interest_rate: '3.0~6.0%',
                        processing_time: '2-4주'
                    }));
                }
                
                // detailed_funds 설정
                if (fundingData.detailed_funds) {
                    normalizedData.detailed_funds = fundingData.detailed_funds;
                } else if (fundingData['자금들']) {
                    normalizedData.detailed_funds = fundingData['자금들'];
                }
                
                // analysis_summary 설정
                if (fundingData.analysis_summary) {
                    normalizedData.analysis_summary = fundingData.analysis_summary;
                } else {
                    normalizedData.analysis_summary = {
                        total_products: normalizedData.individual_funds.length,
                        confidence: '95%',
                        version: 'V2.0',
                        calculation_time: '1초 미만'
                    };
                }
                
                // engine_info 설정
                if (fundingData.engine_info) {
                    normalizedData.engine_info = fundingData.engine_info;
                }
                
                // exclusion_notes 설정
                if (fundingData.exclusion_notes) {
                    normalizedData.exclusion_notes = fundingData.exclusion_notes;
                }
                
                // V2.0 응답 구조에 맞춰 모달 HTML 구성 (추천받기 모달과 완전히 동일)
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
                            max-width: 900px;
                            width: 95%;
                            max-height: 85vh;
                            overflow-y: auto;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        ">
                            <h2 style="margin: 0 0 20px 0; color: #333; text-align: center;">정책자금 추천 분석 결과</h2>
                            
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
                                <div style="font-size: 32px; font-weight: bold;">
                                    ${(normalizedData.total_amount || 0).toLocaleString()}원
                                </div>
                                <div style="font-size: 14px; opacity: 0.9; margin-top: 10px;">
                                    다양한 정책자금을 통해 기업 성장을 지원합니다
                                </div>
                            </div>
                            
                            <!-- 개별 자금 추천 내역 -->
                            ${normalizedData.individual_funds && normalizedData.individual_funds.length > 0 ? `
                            <div style="margin-bottom: 25px;">
                                <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 8px;">
                                    💰 개별 자금 추천 내역 (${normalizedData.individual_funds.length}개)
                                </h4>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px;">
                                    ${normalizedData.individual_funds.map((fund, index) => `
                                        <div style="
                                            background: #f8f9fa;
                                            border: 1px solid #e9ecef;
                                            border-radius: 8px;
                                            padding: 20px;
                                            position: relative;
                                            transition: transform 0.2s;
                                        " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                            <div style="
                                                position: absolute;
                                                top: 10px;
                                                right: 15px;
                                                background: #007bff;
                                                color: white;
                                                padding: 4px 8px;
                                                border-radius: 12px;
                                                font-size: 12px;
                                                font-weight: bold;
                                            ">
                                               가능자금 ${index + 1}
                                            </div>
                                            <div style="font-weight: bold; color: #495057; margin-bottom: 8px; margin-right: 60px;">
                                                ${fund.fund_name}
                                            </div>
                                            <div style="font-size: 20px; font-weight: bold; color: #007bff; margin-bottom: 10px;">
                                                ${(fund.limit || 0).toLocaleString()}원
                                            </div>
                                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 8px;">
                                                <strong>기관:</strong> ${fund.institution || '정부기관'}
                                            </div>
                                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 8px;">
                                                <strong>금리:</strong> ${fund.interest_rate || '3.0~6.0%'}
                                            </div>
                                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 8px;">
                                                <strong>처리기간:</strong> ${fund.processing_time || '2-4주'}
                                            </div>
                                            ${fund.calculation_note ? `
                                            <div style="
                                                background: #fff3cd;
                                                border: 1px solid #ffeaa7;
                                                border-radius: 4px;
                                                padding: 8px;
                                                margin-top: 10px;
                                                font-size: 12px;
                                                color: #856404;
                                            ">
                                                💡 ${fund.calculation_note}
                                            </div>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            ` : `
                            <div style="margin-bottom: 25px;">
                                <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 8px;">
                                    💰 개별 자금 추천 내역
                                </h4>
                                <div style="
                                    background: #f8f9fa;
                                    border: 1px solid #e9ecef;
                                    border-radius: 8px;
                                    padding: 20px;
                                    text-align: center;
                                    color: #6c757d;
                                ">
                                    현재 기업 상황으로는 추가 추천 가능한 자금이 없습니다.
                                </div>
                            </div>
                            `}
                            
                            <!-- 상세 자금 내역 (카테고리별) -->
                            ${normalizedData.detailed_funds && Object.keys(normalizedData.detailed_funds).length > 0 ? `
                            <div style="margin-bottom: 25px;">
                                <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 8px;">
                                    📊 카테고리별 자금 내역
                                </h4>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                                    ${Object.entries(normalizedData.detailed_funds).map(([fundName, amount]) => `
                                        <div style="
                                            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                            border: 1px solid #dee2e6;
                                            border-radius: 6px;
                                            padding: 15px;
                                            text-align: center;
                                        ">
                                            <div style="font-weight: bold; color: #495057; margin-bottom: 8px; font-size: 14px;">
                                                ${fundName}
                                            </div>
                                            <div style="font-size: 16px; font-weight: bold; color: #28a745;">
                                                ${amount.toLocaleString()}원
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            ` : ''}
                            
                            <!-- 공고 추천 -->
                            ${normalizedData.recommended_notices && normalizedData.recommended_notices.length > 0 ? `
                            <div style="margin-bottom: 25px;">
                                <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 8px;">
                                    📢 맞춤 공고 추천 (${normalizedData.recommended_notices.length}개)
                                </h4>
                                <div style="display: flex; flex-direction: column; gap: 12px;">
                                    ${normalizedData.recommended_notices.map(notice => `
                                        <div onclick="window.open('/board/detail/${notice.pblanc_id}/', '_blank')" style="
                                            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                            border: 1px solid #dee2e6;
                                            border-radius: 8px;
                                            padding: 16px;
                                            cursor: pointer;
                                            transition: all 0.2s ease;
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.15)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'">
                                            <div style="font-weight: bold; color: #495057; margin-bottom: 8px; font-size: 15px; line-height: 1.4;">
                                                ${notice.title}
                                            </div>
                                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 4px;">
                                                <strong>기관:</strong> ${notice.institution}
                                            </div>
                                            <div style="color: #6c757d; font-size: 13px; margin-bottom: 4px;">
                                                <strong>접수기간:</strong> ${notice.apply_period}
                                            </div>
                                            <div style="color: #6c757d; font-size: 13px;">
                                                <strong>지원내용:</strong> ${notice.support_amount}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            ` : `
                            <div style="margin-bottom: 25px;">
                                <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 8px;">
                                    📢 맞춤 공고 추천
                                </h4>
                                <div style="
                                    background: #f8f9fa;
                                    border: 1px solid #e9ecef;
                                    border-radius: 8px;
                                    padding: 20px;
                                    text-align: center;
                                    color: #6c757d;
                                ">
                                    현재 조건에 맞는 공고가 없습니다.
                                </div>
                            </div>
                            `}
                            
                            <!-- 제외된 자금 정보 -->
                            ${normalizedData.exclusion_notes && normalizedData.exclusion_notes.length > 0 ? `
                            <div style="margin-bottom: 25px;">
                                <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #dc3545; padding-bottom: 8px;">
                                    ⚠️ 신청 불가 자금 (${normalizedData.exclusion_notes.length}개)
                                </h4>
                                <div style="space-y: 8px;">
                                    ${normalizedData.exclusion_notes.map(note => `
                                        <div style="
                                            background: #f8d7da;
                                            border: 1px solid #f5c6cb;
                                            border-radius: 6px;
                                            padding: 12px;
                                            margin-bottom: 8px;
                                            color: #721c24;
                                            font-size: 14px;
                                        ">
                                            ${note}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            ` : ''}
                            
                            <!-- 추가 정보 -->
                            <div style="
                                background: #d1ecf1;
                                border: 1px solid #bee5eb;
                                border-radius: 6px;
                                padding: 15px;
                                margin-bottom: 20px;
                                font-size: 14px;
                                color: #0c5460;
                            ">
                                <strong>💡 안내사항:</strong><br>
                                • 추천 금액은 현재 기업 상황을 기반으로 한 예상 금액입니다.<br>
                                • 실제 승인 금액은 심사 과정에서 달라질 수 있습니다.<br>
                                • 자세한 신청 조건은 각 기관에 문의하시기 바랍니다.
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
                                    transition: background-color 0.2s;
                                " onmouseover="this.style.backgroundColor='#5a6268'" onmouseout="this.style.backgroundColor='#6c757d'">닫기</button>
                                <button onclick="closeFundingDetailModal()" style="
                                    background: #007bff;
                                    color: white;
                                    border: none;
                                    padding: 12px 24px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 16px;
                                    transition: background-color 0.2s;
                                " onmouseover="this.style.backgroundColor='#0056b3'" onmouseout="this.style.backgroundColor='#007bff'">확인</button>
                            </div>
                        </div>
                    </div>
                `;
                
                // 모달 추가
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                // 외부 클릭 시 모달 닫기 이벤트 추가
                const fundingDetailModal = document.getElementById('fundingDetailModal');
                if (fundingDetailModal) {
                    fundingDetailModal.addEventListener('click', function(e) {
                        // 모달 배경을 클릭했을 때만 닫기 (모달 내용 클릭 시에는 닫지 않음)
                        if (e.target === fundingDetailModal) {
                            closeFundingDetailModal();
                        }
                    });
                }
            })
            .catch(error => {
                console.error('자금 상세 정보 조회 오류:', error);
                showNotification('자금 상세 정보를 조회할 수 없습니다.', 'error');
            });
    });
}

// 자금 상세보기 모달 닫기 함수
function closeFundingDetailModal() {
    console.log('closeFundingDetailModal, 디테일')
    const modal = document.getElementById('fundingDetailModal');
    if (modal) {
        modal.remove();
    }
}

// 나이 필드 업데이트 함수
function updateAgeField(rowId, fieldName, dataType, value) {
    // 현재 저장된 나이 데이터 가져오기
    let currentAgeData = {};
    const ageElement = document.querySelector(`[data-field="${fieldName}"]`);
    
    try {
        // 기존 데이터 파싱 시도
        if (ageElement && ageElement.dataset.currentValue) {
            currentAgeData = JSON.parse(ageElement.dataset.currentValue);
        }
    } catch (e) {
        console.log('기존 나이 데이터 없음, 새로 생성');
    }
    
    if (dataType === 'birth_date') {
        // 생년월일 입력 시 연령대 체크박스 해제
        currentAgeData.birth_date = value;
        currentAgeData.age_range = '';
        
        // 연령대 체크박스들 해제
        const under40Checkbox = document.querySelector(`input[onchange*="'${fieldName}'"][onchange*="'under40'"]`);
        const over40Checkbox = document.querySelector(`input[onchange*="'${fieldName}'"][onchange*="'over40'"]`);
        if (under40Checkbox) under40Checkbox.checked = false;
        if (over40Checkbox) over40Checkbox.checked = false;
        
    } else if (dataType === 'age_range') {
        // 연령대 선택 시 생년월일 입력 해제
        currentAgeData.age_range = value;
        currentAgeData.birth_date = '';
        
        // 생년월일 입력 해제
        const birthDateInput = document.querySelector(`input[onchange*="'${fieldName}'"][onchange*="birth_date"]`);
        if (birthDateInput) birthDateInput.value = '';
        
        // 다른 연령대 체크박스 해제 (배타적 선택)
        if (value === 'under40') {
            const over40Checkbox = document.querySelector(`input[onchange*="'${fieldName}'"][onchange*="'over40'"]`);
            if (over40Checkbox) over40Checkbox.checked = false;
        } else if (value === 'over40') {
            const under40Checkbox = document.querySelector(`input[onchange*="'${fieldName}'"][onchange*="'under40'"]`);
            if (under40Checkbox) under40Checkbox.checked = false;
        }
    }
    
    // 현재 데이터를 element에 저장
    if (ageElement) {
        ageElement.dataset.currentValue = JSON.stringify(currentAgeData);
    }
    
    // 서버에 업데이트 요청
    const ageDataToSend = JSON.stringify(currentAgeData);
    detailUpdateRowField(rowId, fieldName, ageDataToSend);
}

// 날짜 입력 포맷 함수 (YY.MM.DD)
function formatDateInput(input) {
    let value = input.value.replace(/[^\d]/g, ''); // 숫자만 남기기
    
    if (value.length >= 3) {
        value = value.substring(0, 2) + '.' + value.substring(2, 4) + (value.length > 4 ? '.' + value.substring(4, 6) : '');
    } else if (value.length >= 2) {
        value = value.substring(0, 2) + (value.length > 2 ? '.' + value.substring(2) : '');
    }
    
    // 최대 8자리 (YYMMDD)로 제한
    if (value.replace(/\./g, '').length > 6) {
        const cleanValue = value.replace(/\./g, '').substring(0, 6);
        value = cleanValue.substring(0, 2) + '.' + cleanValue.substring(2, 4) + '.' + cleanValue.substring(4, 6);
    }
    
    input.value = value;
}

// 음성파일 영역 업데이트 함수
function updateAudioFileSection(rowId, audioFileValue) {
    console.log('updateAudioFileSection 호출됨:', rowId, audioFileValue);
    
    // 영업노트 영역의 음성파일 관리 기능 업데이트
    // 이 함수는 우측 영업노트 영역에서 음성파일 데이터를 업데이트하는 역할을 합니다.
    if (typeof updateAudioFileManagement === 'function') {
        updateAudioFileManagement(audioFileValue);
    } else {
        console.log('updateAudioFileManagement 함수를 찾을 수 없습니다.');
    }
}

// 음성파일 재생 함수 (필요시 구현)
function playAudio(rowId) {
    console.log('음성파일 재생:', rowId);
    // 실제 음성파일 재생 로직은 필요에 따라 구현
    showNotification('음성파일 재생 기능은 준비 중입니다.', 'info');
}

// 매출 필드 실시간 변환 함수
function formatSalesInputRealtime(input, rowId, fieldName) {
    const value = input.value.replace(/[^\d]/g, '');
    const numericValue = parseInt(value) || 0;
    
    // 콤마 형태로 표시
    if (numericValue > 0) {
        input.value = numericValue.toLocaleString();
        // 매출이 입력되면 빨간 테두리 제거
        highlightRequiredField(input, false);
    } else {
        input.value = '';
    }
}

// 기대출 필드 실시간 변환 함수
function formatDebtInputRealtime(input, rowId, categoryKey) {
    const value = input.value.replace(/[^\d]/g, '');
    const numericValue = parseInt(value) || 0;
    
    // 콤마 형태로 표시
    if (numericValue > 0) {
        input.value = numericValue.toLocaleString();
    } else {
        input.value = '';
    }
}



// 상세보기 모달의 파일 필드 실시간 업데이트 함수
function updateFileFieldInModal(rowId, fieldName, fileInfo) {
    console.log('updateFileFieldInModal 호출됨:', rowId, fieldName, fileInfo);
    
    // AI 캐시 추적 - 파일 수정 (실제 파일 정보 사용)
    if (window.trackFileChange && fileInfo) {
        // 파일 정보에 추가 식별 정보 포함
        const enhancedFileInfo = {
            ...fileInfo,
            file_hash: fileInfo.file_hash || fileInfo.hash || `${fileInfo.filename || fileInfo.original_filename}_${fileInfo.file_size || fileInfo.size}_${fileInfo.last_modified || Date.now()}`,
            last_modified: fileInfo.last_modified || fileInfo.modified_time || Date.now(),
            file_size: fileInfo.file_size || fileInfo.size
        };
        window.trackFileChange(rowId, fieldName, 'modified', enhancedFileInfo);
        console.log('AI 캐시에 파일 수정 추적:', enhancedFileInfo);
    }
    
    const detailModal = document.getElementById('detailModal');
    if (!detailModal) {
        console.log('상세보기 모달이 열려있지 않음');
        return; // 모달이 열려있지 않으면 종료
    }
    
    console.log('상세보기 모달 찾음:', detailModal);
    
    // 실제 모달 구조에 맞게 필드를 찾기
    // 라벨 텍스트로 해당 필드의 부모 div를 찾기
    const labels = detailModal.querySelectorAll('label');
    let targetFieldDiv = null;
    
    for (let label of labels) {
        if (label.textContent.includes(fieldName + ':')) {
            targetFieldDiv = label.closest('div[style*="display:flex"]');
            break;
        }
    }
    
    if (!targetFieldDiv) {
        console.log(`필드를 찾을 수 없음: ${fieldName}`);
        return;
    }
    
    console.log('필드 div 찾음:', targetFieldDiv);
    
    // 파일 정보 영역 업데이트
    const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
    if (fileContainer) {
        const fileName = fileInfo.original_filename || fileInfo.filename || '업로드된 파일';
        const downloadUrl = fileInfo.download_url || `/sales/download_file/${rowId}/${fieldName}/`;
        
        fileContainer.innerHTML = `
            <div style="display: flex; align-items: center;">
                <span style="flex: 1; color: #28a745; font-size: 14px; padding: 8px 0;">📎 ${fileName} (업로드 완료)</span>
                <button type="button" 
                    onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, field_name: fieldName}).replace(/\"/g, '&quot;')})" 
                    style="
                        padding: 6px 12px; 
                        background: #ffc107; 
                        color: #333; 
                        border: none; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 12px;
                        font-weight: 500;">
                    미리보기
                </button>
                <button type="button" 
                    onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                    style="
                        padding: 6px 12px; 
                        background: #17a2b8; 
                        color: white; 
                        border: none; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 12px;
                        font-weight: 500;">
                    다운로드
                </button>
                <button class="delete-file-btn" 
                        data-row-id="${rowId}" 
                        data-field-name="${attr.name}" 
                        data-file-index="${index}"
                        style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                    삭제
                </button>
                <input type="file" 
                    id="file_${fieldName}_${rowId}" 
                    style="display: none;"
                    onchange="uploadFile('${rowId}', '${attr.name}', this)">
            </div>
        `;
        
        console.log('파일 표시 영역 업데이트 완료');
    } else {
        console.log('파일 컨테이너를 찾을 수 없음');
    }
}

// 파일 삭제 후 상세보기 모달의 파일 필드를 "파일 없음" 상태로 업데이트하는 함수
function updateFileFieldInModalAfterDelete(rowId, fieldName) {
    console.log('updateFileFieldInModalAfterDelete 호출됨:', rowId, fieldName);
    
    // AI 캐시 추적 - 파일 삭제
    if (window.trackFileChange) {
        const fileInfo = {
            fieldName: fieldName,
            rowId: rowId
        };
        window.trackFileChange(rowId, fieldName, 'deleted', fileInfo);
        console.log('AI 캐시에 파일 삭제 추적:', fileInfo);
    }
    
    const detailModal = document.getElementById('detailModal');
    if (!detailModal) {
        console.log('상세보기 모달이 열려있지 않음');
        return; // 모달이 열려있지 않으면 종료
    }
    
    // 실제 모달 구조에 맞게 필드를 찾기
    // 라벨 텍스트로 해당 필드의 부모 div를 찾기
    const labels = detailModal.querySelectorAll('label');
    let targetFieldDiv = null;
    
    for (let label of labels) {
        if (label.textContent.includes(fieldName + ':')) {
            targetFieldDiv = label.closest('div[style*="display:flex"]');
            break;
        }
    }
    
    if (!targetFieldDiv) {
        console.log(`필드를 찾을 수 없음: ${fieldName}`);
        return;
    }
    
    console.log('필드 div 찾음:', targetFieldDiv);
    
    // 서버에서 최신 파일 정보를 가져와서 업데이트
    fetch(`/sales/get_row_details/${rowId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.row_data) {
                const fileValue = data.row_data[fieldName];
                console.log('서버에서 받은 파일 값:', fileValue);
                
                if (fileValue) {
                    try {
                        let filesData;
                        
                        // fileValue가 이미 객체인지 문자열인지 확인
                        if (typeof fileValue === 'string') {
                            filesData = JSON.parse(fileValue);
                        } else if (typeof fileValue === 'object') {
                            filesData = fileValue;
                        } else {
                            console.error('예상치 못한 파일 값 타입:', typeof fileValue);
                            filesData = [];
                        }
                        
                        const files = Array.isArray(filesData) ? filesData : [filesData];
                        console.log('파싱된 파일 데이터:', files);
                        
                        if (files.length > 0) {
                            // 파일이 남아있는 경우: 파일 목록 표시
                            let filesHtml = '';
                            files.forEach((fileInfo, index) => {
                                const displayFileName = fileInfo.original_filename || fileInfo.filename || 'Unknown';
                                
                                if (fileInfo.type === 'img' || fileInfo.content_type?.startsWith('image/')) {
                                    filesHtml += `
                                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                            <span style="flex: 1; font-size: 14px;">📄 ${displayFileName}</span>
                                            <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, field_name: fieldName}).replace(/\"/g, '&quot;')})"
                                                    style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                미리보기
                                            </button>
                                            <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                                    style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                다운로드
                                            </button>
                                            <button onclick="deleteFile('${rowId}', '${fieldName}', '${index}')"
                                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                삭제
                                            </button>
                                        </div>
                                    `;
                                } else if (fileInfo.type === 'audio') {
                                    filesHtml += `
                                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                            <span style="flex: 1; font-size: 14px;">🎵 ${displayFileName}</span>
                                            <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, id: fileId, field_name: attr.name, row_id: rowId}).replace(/\"/g, '&quot;')})"
                                                    style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                미리보기
                                            </button>
                                            <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                                    style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                다운로드
                                            </button>
                                            <button class="delete-file-btn" 
                                                    data-row-id="${rowId}" 
                                                    data-field-name="${attr.name}" 
                                                    data-file-index="${index}"
                                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                삭제
                                            </button>
                                        </div>
                                    `;
                                } else {
                                    // 일반 파일
                                    filesHtml += `
                                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                            <span style="flex: 1; font-size: 14px;">📄 ${displayFileName}</span>
                                            <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, field_name: fieldName}).replace(/\"/g, '&quot;')})"
                                                    style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                미리보기
                                            </button>
                                            <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                                    style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                다운로드
                                            </button>
                                            <button onclick="deleteFile('${rowId}', '${fieldName}', '${index}')"
                                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                삭제
                                            </button>
                                        </div>
                                    `;
                                }
                            });
                            
                            // 파일 추가 버튼
                            filesHtml += `
                                <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; background: #fff;">
                                    <span style="flex: 1; color: #6c757d; font-size: 14px;">파일 추가</span>
                                    <button type="button" 
                                            onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                            style="padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                        + 파일 추가
                                    </button>
                                    <input type="file" 
                                           id="file_${fieldName}_${rowId}" 
                                           style="display: none;"
                                           onchange="uploadFile('${rowId}', '${fieldName}', this)">
                                </div>
                            `;
                            
                            // 파일 컨테이너 업데이트
                            const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                            if (fileContainer) {
                                fileContainer.innerHTML = filesHtml;
                                console.log('파일 목록 업데이트 완료');
                                
                                // 새로운 삭제 버튼에 이벤트 리스너 추가
                                setTimeout(() => {
                                    const deleteButtons = fileContainer.querySelectorAll('.delete-file-btn');
                                    console.log('새로 찾은 삭제 버튼 개수:', deleteButtons.length);
                                    
                                    deleteButtons.forEach((btn, index) => {
                                        console.log(`새 버튼 ${index}:`, btn);
                                        console.log(`새 버튼 ${index}의 data 속성:`, {
                                            rowId: btn.getAttribute('data-row-id'),
                                            fieldName: btn.getAttribute('data-field-name'),
                                            fileIndex: btn.getAttribute('data-file-index')
                                        });
                                        
                                        btn.addEventListener('click', function(e) {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            
                                            const rowId = this.getAttribute('data-row-id');
                                            const fieldName = this.getAttribute('data-field-name');
                                            const fileIndex = this.getAttribute('data-file-index');
                                            
                                            console.log('새 파일 삭제 버튼 클릭됨:', rowId, fieldName, fileIndex);
                                            console.log('fileIndex 타입:', typeof fileIndex);
                                            console.log('fileIndex 값:', fileIndex);
                                            
                                            // fileIndex를 숫자로 변환
                                            const numericFileIndex = parseInt(fileIndex, 10);
                                            console.log('변환된 fileIndex:', numericFileIndex);
                                            
                                            console.log('deleteFile 함수 호출 전');
                                            deleteFile(rowId, fieldName, numericFileIndex);
                                            console.log('deleteFile 함수 호출 후');
                                        });
                                    });
                                }, 100);
                            }
                        } else {
                            // 파일이 없는 경우: 파일 선택 버튼
                            const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                            if (fileContainer) {
                                fileContainer.innerHTML = `
                                    <div style="display: flex; align-items: center;">
                                        <span style="flex: 1; color: #6c757d; font-size: 14px; padding: 8px 0;">파일이 선택되지 않았습니다</span>
                                        <button type="button" 
                                                onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                                style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                            파일 선택
                                        </button>
                                        <input type="file" 
                                               id="file_${fieldName}_${rowId}" 
                                               style="display: none;"
                                               onchange="uploadFile('${rowId}', '${fieldName}', this)">
                                    </div>
                                `;
                                console.log('파일 표시 영역을 "파일 없음"으로 업데이트 완료');
                            }
                        }
                    } catch (e) {
                        console.error('파일 정보 파싱 오류:', e, 'fileValue:', fileValue);
                        // 파싱 오류 시 "파일 없음" 상태로 설정
                        const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                        if (fileContainer) {
                            fileContainer.innerHTML = `
                                <div style="display: flex; align-items: center;">
                                    <span style="flex: 1; color: #6c757d; font-size: 14px; padding: 8px 0;">파일이 선택되지 않았습니다</span>
                                    <button type="button" 
                                            onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                            style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                        파일 선택
                                    </button>
                                    <input type="file" 
                                           id="file_${fieldName}_${rowId}" 
                                           style="display: none;"
                                           onchange="uploadFile('${rowId}', '${fieldName}', this)">
                                </div>
                            `;
                        }
                    }
                } else {
                    // 파일 값이 없는 경우: 파일 선택 버튼
                    const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                    if (fileContainer) {
                        fileContainer.innerHTML = `
                            <div style="display: flex; align-items: center;">
                                <span style="flex: 1; color: #6c757d; font-size: 14px; padding: 8px 0;">파일이 선택되지 않았습니다</span>
                                <button type="button" 
                                        onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                        style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                    파일 선택
                                </button>
                                <input type="file" 
                                       id="file_${fieldName}_${rowId}" 
                                       style="display: none;"
                                       onchange="uploadFile('${rowId}', '${fieldName}', this)">
                            </div>
                        `;
                        console.log('파일 표시 영역을 "파일 없음"으로 업데이트 완료');
                    }
                }
            } else {
                console.error('행 정보 가져오기 실패:', data.error);
            }
        })
        .catch(error => {
            console.error('파일 정보 업데이트 오류:', error);
        });
}

// 매출 입력값 실시간 업데이트
function updateSalesFromInputs(rowId, fieldName) {
    const eokInput = document.getElementById('sales_eok_' + rowId);
    const cheonmanInput = document.getElementById('sales_cheonman_' + rowId);
    
    if (!eokInput || !cheonmanInput) return;
    
    const eok = parseInt(eokInput.value) || 0;
    const cheonman = parseInt(cheonmanInput.value) || 0;
    
    // 총 금액 계산 (억 * 100000000 + 천만 * 10000000)
    const totalAmount = eok * 100000000 + cheonman * 10000000;
    
    // 전역 변수에 임시 저장
    window.tempSalesAmount = totalAmount;
}

// 매출 입력 저장
function saveSalesInput(rowId, fieldName) {
    const eokInput = document.getElementById('sales_eok_' + rowId);
    const cheonmanInput = document.getElementById('sales_cheonman_' + rowId);
    
    if (!eokInput || !cheonmanInput) return;
    
    const eok = parseInt(eokInput.value) || 0;
    const cheonman = parseInt(cheonmanInput.value) || 0;
    
    // 기존 값 가져오기
    const container = document.querySelector(`[data-field="${fieldName}"]`);
    let originalValue = 0;
    if (container && container.getAttribute('data-raw')) {
        originalValue = parseInt(container.getAttribute('data-raw')) || 0;
    }
    
    // 기존 값에서 억과 천만 단위를 제외한 나머지 부분 추출 (백만 단위 이하만)
    const remainingAmount = originalValue % 1000000; // 백만 단위 이하만 추출
    
    // 새로운 총 금액 계산 (새로운 억 * 100000000 + 새로운 천만 * 10000000 + 기존 나머지)
    const totalAmount = eok * 100000000 + cheonman * 10000000 + remainingAmount;
    
    // 즉시 UI 업데이트 (사용자 경험 향상) - 억, 천만 단위 입력 형태 유지
    if (container) {
        // 새로운 억, 천만 값으로 입력 필드 업데이트
        eokInput.value = eok;
        cheonmanInput.value = cheonman;
        
        container.setAttribute('data-raw', totalAmount);
        
        // 값이 있으면 빨간 테두리 제거
        if (totalAmount > 0) {
            highlightRequiredField(container, false);
        }
    }
    
    // 테이블 셀도 즉시 업데이트 (모달 외부 테이블)
    if (typeof updateTableCell === 'function') {
        updateTableCell(rowId, fieldName, totalAmount);
    }
    
    // 백그라운드에서 서버 업데이트 (비동기)
    fetch('/sales/update_row_field/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken()
        },
        body: 'id=' + encodeURIComponent(rowId) + '&field=' + encodeURIComponent(fieldName) + '&value=' + encodeURIComponent(totalAmount)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('매출 정보가 업데이트되었습니다.');
            
            // 종속된 행들만 업데이트 (전체 테이블 새로고침 대신)
            if (typeof updateDependentRows === 'function') {
                updateDependentRows(rowId, fieldName, totalAmount);
            }
        } else {
            console.error('매출 업데이트 실패:', data.error);
            showNotification('매출 정보 업데이트에 실패했습니다.', 'error');
            
            // 실패 시 원래 값으로 복원
            if (container && originalValue) {
                const originalEok = Math.floor(originalValue / 100000000);
                const originalCheonman = Math.floor((originalValue % 100000000) / 10000000);
                eokInput.value = originalEok;
                cheonmanInput.value = originalCheonman;
                container.setAttribute('data-raw', originalValue);
            }
        }
    })
    .catch(error => {
        console.error('매출 업데이트 오류:', error);
        showNotification('매출 정보 업데이트 중 오류가 발생했습니다.', 'error');
        
        // 오류 시 원래 값으로 복원
        if (container && originalValue) {
            const originalEok = Math.floor(originalValue / 100000000);
            const originalCheonman = Math.floor((originalValue % 100000000) / 10000000);
            eokInput.value = originalEok;
            cheonmanInput.value = originalCheonman;
            container.setAttribute('data-raw', originalValue);
        }
    });
}

// 매출 입력 취소
function cancelSalesInput(rowId, fieldName) {
    const container = document.querySelector(`[data-field="${fieldName}"]`);
    if (container) {
        const originalValue = container.getAttribute('data-raw');
        const numericValue = originalValue && !isNaN(parseInt(originalValue, 10)) ? parseInt(originalValue, 10) : 0;
        
        // 원래 값으로 억, 천만 입력 필드 복원
        const eokInput = document.getElementById('sales_eok_' + rowId);
        const cheonmanInput = document.getElementById('sales_cheonman_' + rowId);
        
        if (eokInput && cheonmanInput) {
            const originalEok = Math.floor(numericValue / 100000000);
            const originalCheonman = Math.floor((numericValue % 100000000) / 10000000);
            eokInput.value = originalEok;
            cheonmanInput.value = originalCheonman;
        }
    }
    
    // 전역 변수 정리
    delete window.tempSalesAmount;
}

// 개업년월 필드 업데이트 함수
function updateBusinessField(rowId, fieldName, dataType, value) {
    // 현재 저장된 개업 데이터 가져오기
    let currentBusinessData = {};
    const businessElement = document.querySelector(`[data-field="${fieldName}"]`);
    
    try {
        // 기존 데이터 파싱 시도
        if (businessElement && businessElement.dataset.currentValue) {
            currentBusinessData = JSON.parse(businessElement.dataset.currentValue);
        }
    } catch (e) {
        console.log('기존 개업 데이터 없음, 새로 생성');
    }
    
    if (dataType === 'opening_date') {
        // 개업일 입력 시 년전 입력 해제
        currentBusinessData.opening_date = value;
        currentBusinessData.years_ago = '';
        
        // 년전 입력 해제
        const yearsAgoInput = document.querySelector(`input[onchange*="'${fieldName}'"][onchange*="years_ago"]`);
        if (yearsAgoInput) yearsAgoInput.value = '';
        
    } else if (dataType === 'years_ago') {
        // 년전 입력 시 개업일 입력 해제
        currentBusinessData.years_ago = value;
        currentBusinessData.opening_date = '';
        
        // 개업일 입력 해제
        const openingDateInput = document.querySelector(`input[onchange*="'${fieldName}'"][onchange*="opening_date"]`);
        if (openingDateInput) openingDateInput.value = '';
    }
    
    // 현재 데이터를 element에 저장
    if (businessElement) {
        businessElement.dataset.currentValue = JSON.stringify(currentBusinessData);
    }
    
    // 서버에 업데이트 요청
    const businessDataToSend = JSON.stringify(currentBusinessData);
    detailUpdateRowField(rowId, fieldName, businessDataToSend);
}

// 모달에서 필드 업데이트 함수
function detailUpdateRowField(rowId, field, value) {
    console.log('detailUpdateRowField, 디테일2')
    
    fetch('/sales/update_row_field/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'id='+encodeURIComponent(rowId)+'&field='+encodeURIComponent(field)+'&value='+encodeURIComponent(value)
    })
    .then(r=>r.json())
    .then(function(data){
        if(!data.success) {
            alert('수정 실패: '+(data.error||''));
            return;
        }
        
        // 모달에서 변경사항이 있었음을 표시
        window.modalHasChanges = true;
        
        // 부분 업데이트로 변경 (전체 테이블 새로고침 대신)
        if (typeof updateTableCell === 'function') {
            updateTableCell(rowId, field, value);
        }
        
        // 매출 관련 필드인 경우 종속된 행들 업데이트
        if (field === '매출' || field.includes('매출')) {
            if (typeof updateDependentRows === 'function') {
                updateDependentRows(rowId, field, value);
            }
        }
        
        // F/U 일정 필드인 경우 캘린더도 새로고침
        if(field === 'F/U 일정' && window.calendar) {
            window.calendar.refetchEvents();
        }
        
        // datetime 타입 필드인 경우 캘린더 리렌더링
        const fieldElement = document.querySelector(`td[data-field="${field}"]`);
        if (fieldElement && fieldElement.getAttribute('data-type') === 'datetime' && window.calendar) {
            window.calendar.refetchEvents();
        }
        
        // 모든 datetime 필드 변경 시 캘린더 리렌더링
        if (typeof refreshCalendar === 'function') {
            refreshCalendar();
        }
        
        // datetime 타입 속성이 수정된 경우 캘린더 설정 새로고침
        if (typeof refreshCalendarSettings === 'function') {
            refreshCalendarSettings();
        }
        
        // 모달 리랜더링 제거 - 모달은 그대로 유지
        // if (document.getElementById('detailModal') && document.getElementById('detailModal').style.display !== 'none') {
        //     fetch('/sales/get_row_details/'+rowId+'/')
        //       .then(r => r.json())
        //       .then(function(data){
        //           if(data.success) showDetailModal(data.row_data, data.row_id);
        //       });
        // }
    })
    .catch(function(err){
        alert('수정 실패: 네트워크 오류');
        console.error(err);
    });
}

// 파일 업로드 후 모달 필드 새로고침 함수
function updateFileFieldInModalAfterUpload(rowId, fieldName) {
    // 서버에서 최신 파일 정보를 가져와서 모달 업데이트
    fetch(`/sales/get_row_details/${rowId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.row_data) {
                const fileValue = data.row_data[fieldName];
                updateFileFieldInModal(rowId, fieldName, fileValue);
            }
        })
        .catch(error => {
            console.error('파일 업로드 후 모달 업데이트 오류:', error);
        });
}

// 행 복제 버튼 재생성 함수
function recreateDuplicateButtons() {
    const table = document.querySelector('#entryTable');
    if (!table) {
        console.log('테이블을 찾을 수 없습니다.');
        return;
    }
    
    const rows = table.querySelectorAll('tbody tr');
    console.log(`총 ${rows.length}개의 행을 찾았습니다.`);
    
    rows.forEach((row, index) => {
        const rowId = row.getAttribute('data-row-id') || row.getAttribute('data-id');
        if (!rowId) {
            console.log(`행 ${index}: ID를 찾을 수 없습니다.`);
            return;
        }
        
        // drag-cell 찾기
        const dragCell = row.querySelector('.drag-cell');
        if (!dragCell) {
            console.log(`행 ${index}: drag-cell을 찾을 수 없습니다.`);
            return;
        }
        
        // cell-button-container 찾기 또는 생성
        let buttonContainer = dragCell.querySelector('.cell-button-container');
        if (!buttonContainer) {
            buttonContainer = document.createElement('div');
            buttonContainer.className = 'cell-button-container';
            buttonContainer.style.cssText = `
                display: flex;
                align-items: center;
                gap: 6px;
                flex-wrap: nowrap;
                height: 100%;
            `;
            dragCell.appendChild(buttonContainer);
        }
        
        // 기존 버튼들 제거 (체크박스는 유지)
        const existingButtons = buttonContainer.querySelectorAll('.delete-row-btn, .duplicate-row-btn, .drag-handle');
        existingButtons.forEach(btn => btn.remove());
        
        // 삭제 버튼 생성
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-row-btn action-btn';
        deleteBtn.setAttribute('onclick', `deleteRow('${rowId}')`);
        deleteBtn.setAttribute('title', '행 삭제');
        deleteBtn.innerHTML = '×';
        buttonContainer.appendChild(deleteBtn);
        
        // 복제 버튼 생성
        const duplicateBtn = document.createElement('button');
        duplicateBtn.className = 'duplicate-row-btn action-btn';
        duplicateBtn.setAttribute('onclick', `duplicateRow('${rowId}')`);
        duplicateBtn.setAttribute('title', '행 복제');
        duplicateBtn.innerHTML = '📋';
        buttonContainer.appendChild(duplicateBtn);
        
        // 드래그 핸들 생성
        const dragHandle = document.createElement('span');
        dragHandle.className = 'drag-handle';
        dragHandle.innerHTML = '⋮⋮⋮';
        buttonContainer.appendChild(dragHandle);
    });
    
    console.log('recreateDuplicateButtons 함수 완료');
    
    // 체크박스와 상세보기 버튼 이벤트 재바인딩
    bindCheckboxEvents();
    
    // 상세보기 버튼 이벤트 바인딩 (지연 실행)
    setTimeout(() => {
        if (typeof bindDetailButtonEvents === 'function') {
            console.log('recreateDuplicateButtons에서 상세보기 버튼 이벤트 바인딩 시작...');
            bindDetailButtonEvents();
            console.log('recreateDuplicateButtons에서 상세보기 버튼 이벤트 바인딩 완료');
        } else {
            console.log('bindDetailButtonEvents 함수를 찾을 수 없습니다.');
        }
    }, 100);
    
    // 드래그 기능 다시 초기화
    if (typeof Sortable !== 'undefined') {
        const tbody = document.getElementById('entryTbody');
        if (tbody) {
            // 기존 Sortable 인스턴스들이 있다면 제거
            if (window.tableSortable) {
                window.tableSortable.destroy();
                window.tableSortable = null;
            }
            if (window.rowSortable) {
                window.rowSortable.destroy();
                window.rowSortable = null;
            }
            
            // 새로운 Sortable 인스턴스 생성 (window.rowSortable으로 통일)
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
            console.log('드래그 기능 재초기화 완료');
        }
    }
}

function uploadFile(rowId, fieldName, fileInput) {
    console.log('uploadFile 호출됨:', rowId, fieldName, fileInput);

    // AI 캐시 매니저가 초기화되지 않은 경우 초기화
    if (!window.aiCacheManager || window.aiCacheManager.currentRowCache?.rowId !== rowId) {
        console.log('파일 업로드 시 AI 캐시 매니저 초기화:', rowId);
        window.currentDetailRowId = rowId; // 임시로 설정
        initializeAICacheManager();
    }

    const files = fileInput.files;
    if (!files || files.length === 0) {
        alert('파일을 선택해주세요.');
        return;
    }

    if (files.length > 10) {
        alert('한 번에 최대 10개 파일까지 업로드할 수 있습니다.');
        return;
    }

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.size > 10 * 1024 * 1024) {
            alert(`파일 "${file.name}"의 크기가 10MB를 초과합니다.`);
            return;
        }
    }

    console.log('업로드할 파일들:', Array.from(files).map(f => f.name));

    // AI 캐시 추적은 업로드 완료 후에만 수행하도록 수정
    // 업로드 시작 시 임시 추적 제거

    showNotification(`${files.length}개 파일 업로드 중...`, 'info');

    let uploadedCount = 0;
    let failedCount = 0;

    function uploadNextFile(index) {
        if (index >= files.length) {
            showNotification(`${uploadedCount}개 파일이 성공적으로 업로드되었습니다.`, 'success');

            if (failedCount === 0) {
                showNotification(`${uploadedCount}개 파일이 성공적으로 업로드되었습니다.`, 'success');
            } else if (uploadedCount === 0) {
                showNotification('모든 파일 업로드에 실패했습니다.', 'error');
            } else {
                showNotification(`${uploadedCount}개 파일 업로드 성공, ${failedCount}개 실패`, 'warning');
            }

            refreshTable();

            const detailModal = document.getElementById('detailModal');
            if (detailModal && detailModal.style.display !== 'none') {
                fetch(`/sales/get_row_details/${rowId}/`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showDetailModal(data.row_data, data.row_id);
                        }
                    })
                    .catch(error => {
                        console.error('모달 새로고침 오류:', error);
                    });
            }

            fileInput.value = '';
            return;
        }

        const file = files[index];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('row_id', rowId);
        formData.append('field_name', fieldName);

        showNotification(`${index + 1}/${files.length}개 파일 업로드 중... (${file.name})`, 'info');

        fetch('/sales/upload_file/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(`파일 "${file.name}" 업로드 응답:`, data);

            if (data.success) {
                uploadedCount++;
                console.log(`파일 "${file.name}" 업로드 성공`);

                if (window.trackFileChange && data.file_info) {
                    const fileInfo = {
                        ...data.file_info,
                        file_hash: data.file_info.file_hash || `${file.name}_${file.size}_${file.lastModified}`,
                        last_modified: data.file_info.last_modified || file.lastModified,
                        file_size: data.file_info.file_size || file.size,
                        // 서버에서 받은 실제 파일 정보 추가
                        id: data.file_info.id,
                        s3_key: data.file_info.s3_key,
                        download_url: data.file_info.download_url,
                        preview_url: data.file_info.preview_url
                    };

                    // 기존 파일과 비교하여 정확한 변경 타입 결정 (파일명+해시까지 비교)
                    const existingFiles = window.aiCacheManager?.fileChanges?.added || [];
                    const existingFile = existingFiles.find(f => 
                        f.fileInfo?.original_filename === file.name && 
                        f.fileInfo?.file_hash === fileInfo.file_hash &&
                        f.fieldName === fieldName
                    );

                    if (existingFile) {
                        // 기존 파일이 있으면 수정으로 처리
                        window.trackFileChange(rowId, fieldName, 'modified', fileInfo);
                        console.log('AI 캐시에 파일 수정 추적 (기존 파일 존재):', fileInfo);
                    } else {
                        // 새 파일로 처리
                        window.trackFileChange(rowId, fieldName, 'added', fileInfo);
                        console.log('AI 캐시에 파일 추가 추적:', fileInfo);
                    }
                    
                    // 캐시 무효화 플래그 설정
                    if (window.aiCacheManager) {
                        window.aiCacheManager.cacheInvalidated = true;
                        console.log('AI 캐시 무효화 플래그 설정됨');
                    }
                }


                fetch('/sales/get_row_details/' + rowId + '/')
                    .then(r => r.json())
                    .then(function (data) {
                        if (data.success) {
                            showDetailModal(data.row_data, data.row_id);
                        }
                    });

                refreshTable();
                if (window.kanbanAttribute && '지역' === window.kanbanAttribute) {
                    refreshKanban();
                }
                refreshCalendar();
            } else {
                failedCount++;
                uploadNextFile(index + 1);  // ✅ 다음 파일 업로드 호출
            }
        })
        .catch(error => {
            console.error('파일 업로드 오류:', error);
            alert('파일 업로드 중 오류가 발생했습니다.');
            failedCount++;
            uploadNextFile(index + 1);  // ✅ 오류 발생 시에도 다음 파일 업로드
        });
    }

    uploadNextFile(0);  // ✅ 업로드 시작
}


// 파일 업로드 후 모달 필드 새로고침 함수
function updateFileFieldInModalAfterUpload(rowId, fieldName) {
    // 서버에서 최신 파일 정보를 가져와서 모달 업데이트
    fetch(`/sales/get_row_details/${rowId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.row_data) {
                const fileValue = data.row_data[fieldName];
                updateFileFieldInModal(rowId, fieldName, fileValue);
            }
        })
        .catch(error => {
            console.error('파일 업로드 후 모달 업데이트 오류:', error);
        });
}

// 파일 삭제 후 상세보기 모달의 파일 필드를 "파일 없음" 상태로 업데이트하는 함수
function updateFileFieldInModalAfterDelete(rowId, fieldName) {
    console.log('updateFileFieldInModalAfterDelete 호출됨:', rowId, fieldName);
    
    // AI 캐시 추적 - 파일 삭제
    if (window.trackFileChange) {
        const fileInfo = {
            fieldName: fieldName,
            rowId: rowId
        };
        window.trackFileChange(rowId, fieldName, 'deleted', fileInfo);
        console.log('AI 캐시에 파일 삭제 추적:', fileInfo);
    }
    
    const detailModal = document.getElementById('detailModal');
    if (!detailModal) {
        console.log('상세보기 모달이 열려있지 않음');
        return; // 모달이 열려있지 않으면 종료
    }
    
    // 실제 모달 구조에 맞게 필드를 찾기
    // 라벨 텍스트로 해당 필드의 부모 div를 찾기
    const labels = detailModal.querySelectorAll('label');
    let targetFieldDiv = null;
    
    for (let label of labels) {
        if (label.textContent.includes(fieldName + ':')) {
            targetFieldDiv = label.closest('div[style*="display:flex"]');
            break;
        }
    }
    
    if (!targetFieldDiv) {
        console.log(`필드를 찾을 수 없음: ${fieldName}`);
        return;
    }
    
    console.log('필드 div 찾음:', targetFieldDiv);
    
    // 서버에서 최신 파일 정보를 가져와서 업데이트
    fetch(`/sales/get_row_details/${rowId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.row_data) {
                const fileValue = data.row_data[fieldName];
                console.log('서버에서 받은 파일 값:', fileValue);
                
                if (fileValue) {
                    try {
                        let filesData;
                        
                        // fileValue가 이미 객체인지 문자열인지 확인
                        if (typeof fileValue === 'string') {
                            filesData = JSON.parse(fileValue);
                        } else if (typeof fileValue === 'object') {
                            filesData = fileValue;
                        } else {
                            console.error('예상치 못한 파일 값 타입:', typeof fileValue);
                            filesData = [];
                        }
                        
                        const files = Array.isArray(filesData) ? filesData : [filesData];
                        console.log('파싱된 파일 데이터:', files);
                        
                        if (files.length > 0) {
                            // 파일이 남아있는 경우: 파일 목록 표시
                            let filesHtml = '';
                            files.forEach((fileInfo, index) => {
                                const displayFileName = fileInfo.original_filename || fileInfo.filename || 'Unknown';
                                
                                if (fileInfo.type === 'img' || fileInfo.content_type?.startsWith('image/')) {
                                    filesHtml += `
                                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                            <span style="flex: 1; font-size: 14px;">📄 ${displayFileName}</span>
                                            <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, field_name: fieldName}).replace(/\"/g, '&quot;')})"
                                                    style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                미리보기
                                            </button>
                                            <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                                    style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                다운로드
                                            </button>
                                            <button onclick="deleteFile('${rowId}', '${fieldName}', '${index}')"
                                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                삭제
                                            </button>
                                        </div>
                                    `;
                                } else if (fileInfo.type === 'audio') {
                                    filesHtml += `
                                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                            <span style="flex: 1; font-size: 14px;">🎵 ${displayFileName}</span>
                                            <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, id: fileId, field_name: attr.name, row_id: rowId}).replace(/\"/g, '&quot;')})"
                                                    style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                미리보기
                                            </button>
                                            <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                                    style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                다운로드
                                            </button>
                                            <button class="delete-file-btn" 
                                                    data-row-id="${rowId}" 
                                                    data-field-name="${attr.name}" 
                                                    data-file-index="${index}"
                                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                삭제
                                            </button>
                                        </div>
                                    `;
                                } else {
                                    // 일반 파일
                                    filesHtml += `
                                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 8px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa;">
                                            <span style="flex: 1; font-size: 14px;">📄 ${displayFileName}</span>
                                            <button onclick="showFilePreviewModal(${JSON.stringify({...fileInfo, field_name: fieldName}).replace(/\"/g, '&quot;')})"
                                                    style="padding: 4px 8px; background: #ffc107; color: #333; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                미리보기
                                            </button>
                                            <button onclick="downloadFile('${rowId}', '${attr.name}', '${fileId}')"
                                                    style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                다운로드
                                            </button>
                                            <button onclick="deleteFile('${rowId}', '${fieldName}', '${index}')"
                                                    style="padding: 4px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: 500;">
                                                삭제
                                            </button>
                                        </div>
                                    `;
                                }
                            });
                            
                            // 파일 추가 버튼
                            filesHtml += `
                                <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; background: #fff;">
                                    <span style="flex: 1; color: #6c757d; font-size: 14px;">파일 추가</span>
                                    <button type="button" 
                                            onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                            style="padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                        + 파일 추가
                                    </button>
                                    <input type="file" 
                                           id="file_${fieldName}_${rowId}" 
                                           style="display: none;"
                                           onchange="uploadFile('${rowId}', '${fieldName}', this)">
                                </div>
                            `;
                            
                            // 파일 컨테이너 업데이트
                            const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                            if (fileContainer) {
                                fileContainer.innerHTML = filesHtml;
                                console.log('파일 목록 업데이트 완료');
                                
                                // 새로운 삭제 버튼에 이벤트 리스너 추가
                                setTimeout(() => {
                                    const deleteButtons = fileContainer.querySelectorAll('.delete-file-btn');
                                    console.log('새로 찾은 삭제 버튼 개수:', deleteButtons.length);
                                    
                                    deleteButtons.forEach((btn, index) => {
                                        console.log(`새 버튼 ${index}:`, btn);
                                        console.log(`새 버튼 ${index}의 data 속성:`, {
                                            rowId: btn.getAttribute('data-row-id'),
                                            fieldName: btn.getAttribute('data-field-name'),
                                            fileIndex: btn.getAttribute('data-file-index')
                                        });
                                        
                                        btn.addEventListener('click', function(e) {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            
                                            const rowId = this.getAttribute('data-row-id');
                                            const fieldName = this.getAttribute('data-field-name');
                                            const fileIndex = this.getAttribute('data-file-index');
                                            
                                            console.log('새 파일 삭제 버튼 클릭됨:', rowId, fieldName, fileIndex);
                                            console.log('fileIndex 타입:', typeof fileIndex);
                                            console.log('fileIndex 값:', fileIndex);
                                            
                                            // fileIndex를 숫자로 변환
                                            const numericFileIndex = parseInt(fileIndex, 10);
                                            console.log('변환된 fileIndex:', numericFileIndex);
                                            
                                            console.log('deleteFile 함수 호출 전');
                                            deleteFile(rowId, fieldName, numericFileIndex);
                                            console.log('deleteFile 함수 호출 후');
                                        });
                                    });
                                }, 100);
                            }
                        } else {
                            // 파일이 없는 경우: 파일 선택 버튼
                            const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                            if (fileContainer) {
                                fileContainer.innerHTML = `
                                    <div style="display: flex; align-items: center;">
                                        <span style="flex: 1; color: #6c757d; font-size: 14px; padding: 8px 0;">파일이 선택되지 않았습니다</span>
                                        <button type="button" 
                                                onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                                style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                            파일 선택
                                        </button>
                                        <input type="file" 
                                               id="file_${fieldName}_${rowId}" 
                                               style="display: none;"
                                               onchange="uploadFile('${rowId}', '${fieldName}', this)">
                                    </div>
                                `;
                                console.log('파일 표시 영역을 "파일 없음"으로 업데이트 완료');
                            }
                        }
                    } catch (e) {
                        console.error('파일 정보 파싱 오류:', e, 'fileValue:', fileValue);
                        // 파싱 오류 시 "파일 없음" 상태로 설정
                        const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                        if (fileContainer) {
                            fileContainer.innerHTML = `
                                <div style="display: flex; align-items: center;">
                                    <span style="flex: 1; color: #6c757d; font-size: 14px; padding: 8px 0;">파일이 선택되지 않았습니다</span>
                                    <button type="button" 
                                            onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                            style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                        파일 선택
                                    </button>
                                    <input type="file" 
                                           id="file_${fieldName}_${rowId}" 
                                           style="display: none;"
                                           onchange="uploadFile('${rowId}', '${fieldName}', this)">
                                </div>
                            `;
                        }
                    }
                } else {
                    // 파일 값이 없는 경우: 파일 선택 버튼
                    const fileContainer = targetFieldDiv.querySelector('div[style*="flex:1"]');
                    if (fileContainer) {
                        fileContainer.innerHTML = `
                            <div style="display: flex; align-items: center;">
                                <span style="flex: 1; color: #6c757d; font-size: 14px; padding: 8px 0;">파일이 선택되지 않았습니다</span>
                                <button type="button" 
                                        onclick="document.getElementById('file_${fieldName}_${rowId}').click()" 
                                        style="padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                                    파일 선택
                                </button>
                                <input type="file" 
                                       id="file_${fieldName}_${rowId}" 
                                       style="display: none;"
                                       onchange="uploadFile('${rowId}', '${fieldName}', this)">
                            </div>
                        `;
                        console.log('파일 표시 영역을 "파일 없음"으로 업데이트 완료');
                    }
                }
            } else {
                console.error('행 정보 가져오기 실패:', data.error);
            }
        })
        .catch(error => {
            console.error('파일 정보 업데이트 오류:', error);
        });
}

// 파일 미리보기 모달 함수
function showFilePreviewModal(fileInfo) {
    console.log('showFilePreviewModal 호출됨:', fileInfo);
    
    // 기존 showFilePreview 함수 사용
    // fileInfo에서 필요한 데이터 추출
    const fileId = fileInfo.id || fileInfo.stored_filename || fileInfo.filename || '';
    const rowId = window.currentDetailRowId || fileInfo.row_id || '';
    const fieldName = fileInfo.field_name || '';
    
    console.log('파일 미리보기 파라미터:', {
        fileId: fileId,
        fileInfo: fileInfo,
        rowId: rowId,
        fieldName: fieldName
    });
    
    // 필수 파라미터 검증
    if (!fileId) {
        showNotification('파일 ID를 찾을 수 없습니다.', 'error');
        return;
    }
    
    if (!rowId) {
        showNotification('행 ID를 찾을 수 없습니다.', 'error');
        return;
    }
    
    showFilePreview(fileId, fileInfo, rowId, fieldName);
}

// 파일 미리보기 모달 닫기 함수
function closeFilePreviewModal() {
    const modal = document.getElementById('filePreviewModal');
    if (modal) {
        modal.remove();
    }
}

// 체크박스 이벤트 바인딩 함수
function bindCheckboxEvents() {
    console.log('체크박스 이벤트 바인딩 시작');
    
    // 전체 선택 체크박스
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.onchange = function() {
            const isChecked = this.checked;
            const rowCheckboxes = document.querySelectorAll('.row-checkbox');
            
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            updateBulkDeleteButton();
        };
        console.log('전체 선택 체크박스 이벤트 바인딩 완료');
    }
    
    // 개별 행 체크박스
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    rowCheckboxes.forEach(checkbox => {
        checkbox.onchange = function() {
            updateBulkDeleteButton();
            
            // 모든 체크박스가 선택되었는지 확인
            const allCheckboxes = document.querySelectorAll('.row-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
            
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = allCheckboxes.length === checkedCheckboxes.length;
                selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length;
            }
        };
    });
    
    console.log(`개별 체크박스 ${rowCheckboxes.length}개 이벤트 바인딩 완료`);
}

// 상세보기 버튼 이벤트 바인딩 함수
function bindDetailButtonEvents() {
    console.log('=== bindDetailButtonEvents 함수 시작 ===');
    
    // 회사명 셀의 상세보기 버튼들
    const moreButtons = document.querySelectorAll('td[data-field="회사명"] .more-btn');
    
    if (moreButtons.length === 0) {
        console.log('상세보기 버튼을 찾을 수 없습니다. DOM 구조 확인 필요.');
        // DOM 구조 디버깅
        const companyCells = document.querySelectorAll('td[data-field="회사명"]');
        console.log(`회사명 셀 개수: ${companyCells.length}`);
        companyCells.forEach((cell, index) => {
            const nameContainer = cell.querySelector('.name-container');
            const moreBtn = cell.querySelector('.more-btn');
            console.log(`회사명 셀 ${index}:`, {
                hasNameContainer: !!nameContainer,
                hasMoreBtn: !!moreBtn,
                cellHTML: cell.innerHTML.substring(0, 100) + '...'
            });
        });
        return;
    }
    
    let processedCount = 0;
    let skippedCount = 0;
    
    moreButtons.forEach((btn, index) => {
        
        // 이미 처리된 버튼인지 확인 (data-event-bound 속성으로 추적)
        if (btn.getAttribute('data-event-bound') === 'true') {
            skippedCount++;
            console.log(`버튼 ${index}는 이미 이벤트가 바인딩되어 건너뜁니다.`);
            return;
        }
        
        // 버튼이 클릭 가능하도록 스타일 설정
        btn.style.cursor = 'pointer';
        btn.style.pointerEvents = 'auto';
        btn.style.userSelect = 'none';
        
        // 기존 이벤트 리스너 완전 제거
        btn.onclick = null;
        // 기존 addEventListener로 추가된 이벤트들도 제거하기 위해 클론 생성
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // 처리됨을 표시
        newBtn.setAttribute('data-event-bound', 'true');
        
        // 새 버튼에 단일 이벤트만 바인딩
        newBtn.addEventListener('click', function(e) {
            console.log(`상세보기 버튼 ${index} 클릭됨!`);
            e.stopPropagation();
            e.preventDefault();
            
            const tr = this.closest('tr');
            const id = tr.getAttribute('data-id') || tr.getAttribute('data-row-id');
            console.log(`클릭된 행 ID: ${id}`);
            
            if (!id) { 
                console.error('ID 정보가 없습니다.');
                alert('ID 정보가 없습니다.'); 
                return; 
            }
            
            console.log(`상세보기 버튼 클릭: ID = ${id}`);
            console.log('fetch 요청 시작...');
            
            fetch('/sales/get_row_details/' + id + '/')
                .then(r => {
                    console.log('fetch 응답 받음:', r.status);
                    return r.json();
                })
                .then(function(data) {
                    console.log('JSON 파싱 완료:', data);
                    if (data.success) {
                        console.log('showDetailModal 호출...');
                        showDetailModal(data.row_data, data.row_id);
                    } else {
                        console.error('상세정보 불러오기 실패:', data.error);
                        alert('상세정보 불러오기 실패: ' + (data.error || ''));
                    }
                })
                .catch(function(err) {
                    console.error('상세정보 불러오기 실패:', err);
                    alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                });
        });
        
        processedCount++;
    });
    
    console.log(`=== bindDetailButtonEvents 완료: 처리됨 ${processedCount}개, 건너뜀 ${skippedCount}개 ===`);
}

// 종속된 행들을 찾아서 업데이트하는 함수
function updateDependentRows(updatedRowId, fieldName, value) {
    console.log('종속된 행들 업데이트 시작:', {updatedRowId, fieldName, value});
    
    // 드롭다운 필드인지 확인
    const dropdownFields = (window.ATTR_FIELDS || [])
        .filter(attr => attr.attributeType_name === 'dropdown')
        .map(attr => attr.name);
    
    const isDropdownField = dropdownFields.includes(fieldName);
    
    // 서버에서 종속된 행들 정보 가져오기
    fetch('/sales/get_dependent_rows/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'row_id=' + encodeURIComponent(updatedRowId) + '&field=' + encodeURIComponent(fieldName)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.dependent_rows) {
            console.log('종속된 행들:', data.dependent_rows);
            
            // 드롭다운 필드가 아닌 경우 즉시 업데이트
            if (!isDropdownField) {
                data.dependent_rows.forEach(depRow => {
                    if (depRow.row_id && depRow.field && depRow.value !== undefined) {
                        console.log('종속된 행 업데이트:', depRow);
                        if (typeof updateTableCell === 'function') {
                            updateTableCell(depRow.row_id, depRow.field, depRow.value);
                        }
                    }
                });
                return;
            }
            
            // 드롭다운 필드인 경우 옵션 정보를 한 번에 가져와서 처리
            if (isDropdownField) {
                fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName))
                    .then(response => response.json())
                    .then(optionData => {
                        const options = optionData.options || [];
                        
                        data.dependent_rows.forEach(depRow => {
                            if (depRow.row_id && depRow.field && depRow.value !== undefined) {
                                console.log('종속된 행 업데이트:', depRow);
                                
                                let displayValue = depRow.value;
                                if (depRow.value && !isNaN(depRow.value)) {
                                    const option = options.find(opt => opt.id == depRow.value);
                                    if (option) {
                                        displayValue = option.option;
                                    }
                                }
                                
                                if (typeof updateTableCell === 'function') {
                                    updateTableCell(depRow.row_id, depRow.field, displayValue);
                                }
                            }
                        });
                    })
                    .catch(error => {
                        console.error('드롭다운 옵션 정보 가져오기 실패:', error);
                        // 실패 시 원래 값으로 업데이트
                        data.dependent_rows.forEach(depRow => {
                            if (depRow.row_id && depRow.field && depRow.value !== undefined) {
                                if (typeof updateTableCell === 'function') {
                                    updateTableCell(depRow.row_id, depRow.field, depRow.value);
                                }
                            }
                        });
                    });
            }
        } else {
            console.log('종속된 행이 없거나 오류 발생:', data);
        }
    })
    .catch(error => {
        console.error('종속된 행들 업데이트 실패:', error);
    });
}

// 오디오 미리보기 함수
function showAudioPreview(audioUrl, fileName) {
    // 기존 미리보기 모달이 있으면 제거
    const existingModal = document.getElementById('audioPreviewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 생성
    const modal = document.createElement('div');
    modal.id = 'audioPreviewModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    modal.innerHTML = `
        <div style="position: relative; width: 90%; max-width: 500px; background: white; border-radius: 8px; overflow: hidden;">
            <!-- 헤더 -->
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 60px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 10;">
                <div style="font-size: 16px; font-weight: bold; color: #333;">🎵 ${fileName}</div>
                <button onclick="closeAudioPreviewModal()" 
                        style="background: #dc3545; color: white; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer; font-size: 14px;">
                    닫기
                </button>
            </div>
            
            <!-- 오디오 콘텐츠 -->
            <div style="position: absolute; top: 60px; left: 0; right: 0; bottom: 0; padding: 40px; display: flex; align-items: center; justify-content: center;">
                <audio controls src="${audioUrl}" style="width: 100%; max-width: 400px;">
                    Your browser does not support the audio element.
                </audio>
            </div>
        </div>
    `;
    
    modal.onclick = function(e) {
        if (e.target === modal) {
            closeAudioPreviewModal();
        }
    };
    
    document.body.appendChild(modal);
}

// 오디오 미리보기 모달 닫기 함수
function closeAudioPreviewModal() {
    const modal = document.getElementById('audioPreviewModal');
    if (modal) {
        modal.remove();
    }
}

// 1. 전역에서 triggerKanbanRefreshIfNeeded가 없으면 import/정의
if (typeof triggerKanbanRefreshIfNeeded === 'undefined') {
    window.triggerKanbanRefreshIfNeeded = async function(fieldName) {
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
                if (typeof refreshKanban === 'function') refreshKanban();
                setTimeout(() => { window._kanbanRefreshing = false; }, 500);
            }
        }, 80);
    };
}

// 최신 presigned download URL로 파일 다운로드 (중복 방지)
if (!window.downloadFileWithFreshUrl) {
    window.downloadFileWithFreshUrl = function(fileId, fileName) {
        if (!window.currentDetailRowId) {
            alert('row_id가 없습니다.');
            return;
        }
        console.log(fileId, fileName);
        console.log('window.currentDetailRowId', window.currentDetailRowId);
        fetch(`/sales/download_file/${fileId}/?row_id=${window.currentDetailRowId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.download_url) {
                    const a = document.createElement('a');
                    a.href = data.download_url;
                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                } else {
                    alert('다운로드 URL을 가져오지 못했습니다.');
                }
            })
            .catch(() => alert('다운로드 요청 중 오류가 발생했습니다.'));
    }
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

// 추천 지원사업 모달 관련 함수들
function openRecommendModal(rowId, type) {
    if (type === 'recommend') {
        // 추천받기 - 새로운 데이터 조회
        getBizRecommendations(rowId);
    } else {
        // 저장된 데이터 보기
        getSavedBizRecommendations(rowId);
    }
}

function getBizRecommendations(rowId) {
    // 추천받기 전에 필수 필드 유효성 검사 수행
    if (!validateRequiredFieldsForBizRecommendation(rowId)) {
        return;
    }
    
    // 로딩 표시
    showRecommendModal('추천 지원사업', '데이터를 조회하고 있습니다...', true);
    
    fetch('/sales/get_biz_recommendations/', {
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
            showRecommendModal('추천 지원사업', '', false, data.data, rowId, 'recommend');
        } else {
            showRecommendModal('오류', data.error || '추천 데이터를 가져오는데 실패했습니다.', false);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showRecommendModal('오류', '네트워크 오류가 발생했습니다.', false);
    });
}

// 추천 지원사업을 위한 필수 필드 유효성 검사 함수
function validateRequiredFieldsForBizRecommendation(rowId) {
    console.log('=== 추천 지원사업 필수 필드 유효성 검사 시작 ===');
    
    const requiredFields = ['지역', '상세지역', '업종', '매출', '개업년월'];
    const missingFields = [];
    
    const detailModal = document.getElementById('detailModal');
    
    if (detailModal && detailModal.style.display !== 'none') {
        console.log('모달이 열려있음 - 모달 내 검증 시작');
        
        // 각 필수 필드 검증
        for (const fieldName of requiredFields) {
            console.log(`\n--- ${fieldName} 필드 검증 시작 ---`);
            
            if (fieldName === '지역' || fieldName === '상세지역') {
                // 지역과 상세지역은 특별한 버튼 형태로 처리
                const regionButtons = detailModal.querySelectorAll('button[onclick*="지역"], button[onclick*="상세지역"]');
                let hasValidRegion = false;
                
                regionButtons.forEach(btn => {
                    const buttonText = btn.textContent.trim();
                    if (buttonText && buttonText !== '선택') {
                        hasValidRegion = true;
                    }
                });
                
                if (!hasValidRegion) {
                    console.log(`${fieldName} - 누락됨`);
                    missingFields.push(fieldName);
                    // 지역 관련 버튼들에 빨간 테두리 표시
                    regionButtons.forEach(btn => {
                        highlightRequiredField(btn, true);
                    });
                } else {
                    console.log(`${fieldName} - 정상`);
                    // 정상인 경우 원래 스타일로 복원
                    regionButtons.forEach(btn => {
                        highlightRequiredField(btn, false);
                    });
                }
                
            } else if (fieldName === '업종') {
                const industrySelect = detailModal.querySelector('select[onchange*="업종"]');
                console.log('업종 select 요소:', {
                    found: !!industrySelect,
                    value: industrySelect ? industrySelect.value : 'N/A'
                });
                
                if (industrySelect && (!industrySelect.value || industrySelect.value === '')) {
                    console.log('업종 - 누락됨');
                    missingFields.push(fieldName);
                    // 빨간 테두리 표시
                    highlightRequiredField(industrySelect, true);
                } else if (industrySelect) {
                    console.log('업종 - 정상');
                    // 정상인 경우 원래 스타일로 복원
                    highlightRequiredField(industrySelect, false);
                } else {
                    console.log('업종 select를 찾을 수 없음');
                    missingFields.push(fieldName);
                }
                
            } else if (fieldName === '매출') {
                console.log('매출 필드 특별 처리 시작');
                
                // sales-field-container를 직접 찾기
                const salesContainer = detailModal.querySelector('.sales-field-container[data-field="매출"]');
                const salesInput = detailModal.querySelector('input[data-field="매출"]');
                
                console.log('매출 필드 검색 결과:', {
                    salesContainer: !!salesContainer,
                    salesInput: !!salesInput
                });
                
                if (salesContainer) {
                    const rawValue = salesContainer.getAttribute('data-raw');
                    const displayText = salesContainer.textContent.trim();
                    
                    console.log('매출 컨테이너 검증 디버깅:', {
                        rawValue: rawValue,
                        displayText: displayText,
                        hasDataRaw: salesContainer.hasAttribute('data-raw'),
                        containerHTML: salesContainer.innerHTML
                    });
                    
                    // 더 정확한 검증 로직
                    const hasValidValue = (
                        rawValue && 
                        rawValue !== '' && 
                        !isNaN(parseInt(rawValue, 10)) && 
                        parseInt(rawValue, 10) >= 0 &&
                        !displayText.includes('클릭하여 입력') &&
                        displayText !== ''
                    );
                    
                    console.log('매출 컨테이너 유효성 검사 결과:', hasValidValue);
                    
                    if (!hasValidValue) {
                        console.log('매출 - 누락됨 (컨테이너)');
                        missingFields.push(fieldName);
                        // 빨간 테두리 표시
                        highlightRequiredField(salesContainer, true);
                    } else {
                        console.log('매출 - 정상 (컨테이너)');
                        // 정상인 경우 원래 스타일로 복원
                        highlightRequiredField(salesContainer, false);
                    }
                } else if (salesInput) {
                    // input 형태의 매출 필드 처리
                    const inputValue = salesInput.value.trim();
                    console.log('매출 input 검증 디버깅:', {
                        inputValue: inputValue,
                        inputType: salesInput.type
                    });
                    
                    const hasValidInputValue = (
                        inputValue && 
                        inputValue !== '0' && 
                        inputValue !== '' && 
                        !isNaN(parseInt(inputValue.replace(/[^\d]/g, ''), 10)) && 
                        parseInt(inputValue.replace(/[^\d]/g, ''), 10) > 0
                    );
                    
                    console.log('매출 input 유효성 검사 결과:', hasValidInputValue);
                    
                    if (!hasValidInputValue) {
                        console.log('매출 - 누락됨 (input)');
                        missingFields.push(fieldName);
                        // 빨간 테두리 표시
                        highlightRequiredField(salesInput, true);
                    } else {
                        console.log('매출 - 정상 (input)');
                        // 정상인 경우 원래 스타일로 복원
                        highlightRequiredField(salesInput, false);
                    }
                } else {
                    console.log('매출 필드를 찾을 수 없음');
                    missingFields.push(fieldName);
                }
                
            } else if (fieldName === '개업년월') {
                const businessElement = detailModal.querySelector('[data-field="개업년월"]');
                if (businessElement) {
                    try {
                        const currentValue = businessElement.dataset.currentValue;
                        let businessData = {};
                        
                        if (currentValue) {
                            businessData = JSON.parse(currentValue);
                        }
                        
                        const hasValidValue = (
                            businessData.opening_date || 
                            businessData.years_ago
                        );
                        
                        if (!hasValidValue) {
                            console.log('개업년월 - 누락됨');
                            missingFields.push(fieldName);
                            // 빨간 테두리 표시
                            highlightRequiredField(businessElement, true);
                        } else {
                            console.log('개업년월 - 정상');
                            // 정상인 경우 원래 스타일로 복원
                            highlightRequiredField(businessElement, false);
                        }
                    } catch (e) {
                        console.log('개업년월 데이터 파싱 오류:', e);
                        missingFields.push(fieldName);
                        highlightRequiredField(businessElement, true);
                    }
                } else {
                    console.log('개업년월 필드를 찾을 수 없음');
                    missingFields.push(fieldName);
                }
            }
        }
        
        console.log('\n=== 모달 내 검증 완료 ===');
        console.log('누락된 필드들:', missingFields);
        
    } else {
        console.log('모달이 닫혀있음 - 서버에서 데이터 가져와서 검증');
        
        // 모달이 닫혀있는 경우 서버에서 데이터를 가져와서 확인
        return new Promise((resolve) => {
            fetch(`/sales/get_row_details/${rowId}/`)
                .then(response => response.json())
                .then(data => {
                    console.log('서버 응답:', data);
                    
                    if (data.success) {
                        const rowData = data.row_data;
                        console.log('행 데이터:', rowData);
                        
                        // 필수값 확인
                        if (!rowData['지역'] || rowData['지역'] === '') {
                            missingFields.push('지역');
                        }
                        if (!rowData['상세지역'] || rowData['상세지역'] === '') {
                            missingFields.push('상세지역');
                        }
                        if (!rowData['업종'] || rowData['업종'] === '') {
                            missingFields.push('업종');
                        }
                        
                        // 매출 검증
                        const revenueValue = rowData['매출'];
                        const hasValidRevenue = (
                            revenueValue && 
                            revenueValue !== '' && 
                            !isNaN(parseInt(revenueValue, 10)) && 
                            parseInt(revenueValue, 10) >= 0
                        );
                        
                        if (!hasValidRevenue) {
                            missingFields.push('매출');
                        }
                        
                        // 개업년월 검증
                        const businessValue = rowData['개업년월'];
                        let hasValidBusiness = false;
                        
                        if (businessValue) {
                            try {
                                const businessData = JSON.parse(businessValue);
                                hasValidBusiness = (businessData.opening_date || businessData.years_ago);
                            } catch (e) {
                                hasValidBusiness = false;
                            }
                        }
                        
                        if (!hasValidBusiness) {
                            missingFields.push('개업년월');
                        }
                        
                        console.log('서버 검증 결과 - 누락된 필드들:', missingFields);
                        
                        // 필수값이 누락된 경우 알림 표시
                        if (missingFields.length > 0) {
                            showNotification(`다음 필수 항목을 입력해주세요: ${missingFields.join(', ')}`, 'error');
                            resolve(false);
                            return;
                        }
                        
                        resolve(true);
                    } else {
                        showNotification('데이터를 가져올 수 없습니다.', 'error');
                        resolve(false);
                    }
                })
                .catch(error => {
                    console.error('필수값 검증 중 오류:', error);
                    showNotification('필수값 검증 중 오류가 발생했습니다.', 'error');
                    resolve(false);
                });
        });
    }
    
    // 모달이 열려있는 경우 즉시 검증
    console.log('\n=== 최종 검증 결과 ===');
    console.log('누락된 필드들:', missingFields);
    
    if (missingFields.length > 0) {
        console.log('필수값 누락 - 알림 표시');
        showNotification(`다음 필수 항목을 입력해주세요: ${missingFields.join(', ')}`, 'error');
        return false;
    }
    
    console.log('모든 필수값 확인됨 - 추천 요청 진행');
    return true;
}

function getSavedBizRecommendations(rowId) {
    // 로딩 표시
    showRecommendModal('저장된 추천 지원사업', '데이터를 조회하고 있습니다...', true);
    
    fetch('/sales/get_saved_biz_recommendations/', {
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
            console.log('저장된 추천 지원사업 데이터:', data);
            // 데이터가 실제로 있는지 확인
            if (data.data && data.data.length > 0) {
                showRecommendModal('저장된 추천 지원사업', '', false, data.data, rowId, 'view');
            } else {
                showRecommendModal('저장된 추천 지원사업', '저장된 추천 지원사업이 없습니다. 먼저 추천받기를 진행해주세요.', false);
            }
        } else {
            showRecommendModal('오류', data.error || '저장된 데이터를 가져오는데 실패했습니다.', false);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showRecommendModal('오류', '네트워크 오류가 발생했습니다.', false);
    });
}

function showRecommendModal(title, message, isLoading, data = null, rowId = null, type = null) {
    // 기존 모달이 있으면 제거
    const existingModal = document.getElementById('recommendModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    let modalContent = '';
    
    if (isLoading) {
        modalContent = `
            <div style="text-align: center; padding: 40px;">
                <div class="spinner-border" role="status" style="width: 3rem; height: 3rem;">
                    <span class="sr-only">Loading...</span>
                </div>
                <p style="margin-top: 20px; color: #666;">${message}</p>
            </div>
        `;
    } else if (data && data.length > 0) {
        modalContent = `
            <div style="max-height: 70vh; overflow-y: auto;">
                <div style="margin-bottom: 20px;">
                    ${type === 'view' && data.some(biz => biz.isNew) ? '<p style="color: #dc3545; font-size: 14px; font-weight: bold;">🔔 새로 추가된 공고가 있습니다!</p>' : ''}
                </div>
                <div style="display: grid; gap: 15px;">
                    ${data.map((biz, index) => `
                        <div class="biz-card" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; background: #fafafa; ${biz.isNew ? 'border-left: 4px solid #dc3545;' : ''}">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; cursor: pointer;" onclick="window.open('https://namatji.com/board/detail/${biz.pblanc_id}/', '_blank')">
                                <h6 style="margin: 0; color: #007bff; font-weight: 600;" >${biz.title || '제목 없음'}</h6>
                                ${biz.isNew ? '<span style="color: #dc3545; font-weight: bold; font-size: 12px;">NEW</span>' : ''}
                            </div>
                            <div style="display: none; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                                <div><strong>지역:</strong> ${biz.region || '정보 없음'}</div>
                                <div><strong>업종:</strong> ${biz.possible_industry || '정보 없음'}</div>
                                <div><strong>매출:</strong> ${biz.revenue || '정보 없음'}</div>
                                <div><strong>업력:</strong> ${biz.business_period || '정보 없음'}</div>
                                <div><strong>대상:</strong> ${biz.target || '정보 없음'}</div>
                            </div>
                            ${biz.noti_summary ? `
                                <div style="margin-top: 10px; padding: 10px; background: white; border-radius: 4px; border-left: 3px solid #007bff;">
                                    <strong>요약:</strong> ${biz.noti_summary}
                                </div>
                            ` : ''}
                            ${biz.hashtag ? `
                                <div style="margin-top: 8px;">
                                    <span style="color: #666; font-size: 12px;">태그: ${biz.hashtag}</span>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                ${type === 'recommend' ? `
                    <div style="margin-top: 20px; text-align: center;">
                        <button type="button" class="btn btn-primary" onclick="closeRecommendModal()" 
                                style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                            확인
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    } else {
        modalContent = `
            <div style="text-align: center; padding: 40px;">
                <p style="color: #666; font-size: 16px;">${message}</p>
                ${type === 'view' ? `
                    <div style="margin-top: 20px;">
                        <button type="button" class="btn btn-primary" onclick="closeRecommendModal()" 
                                style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                            확인
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // 모달 HTML 생성
    const modalHTML = `
        <div id="recommendModal" class="modal" style="display: flex; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); align-items: center; justify-content: center;">
            <div class="modal-content" style="background-color: #fefefe; margin: auto; padding: 0; border-radius: 8px; width: 90%; max-width: 800px; max-height: 90vh; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div class="modal-header" style="padding: 20px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #333;">${title}</h4>
                    <span class="close" onclick="closeRecommendModal()" style="color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer; line-height: 1;">&times;</span>
                </div>
                <div class="modal-body" style="padding: 20px;">
                    ${modalContent}
                </div>
            </div>
        </div>
    `;
    
    // 모달을 body에 추가
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // 모달 표시
    document.getElementById('recommendModal').style.display = 'flex';
}

function closeRecommendModal() {
    const modal = document.getElementById('recommendModal');
    if (modal) {
        modal.remove();
    }
}

function saveSelectedRecommendations(rowId) {
    const selectedCheckboxes = document.querySelectorAll('#recommendModal input[type="checkbox"]:checked');
    const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (selectedIds.length === 0) {
        alert('저장할 지원사업을 선택해주세요.');
        return;
    }
    
    // 로딩 표시
    const modalBody = document.querySelector('#recommendModal .modal-body');
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div class="spinner-border" role="status" style="width: 3rem; height: 3rem;">
                <span class="sr-only">Loading...</span>
            </div>
            <p style="margin-top: 20px; color: #666;">선택한 지원사업을 저장하고 있습니다...</p>
        </div>
    `;
    
    fetch('/sales/save_biz_recommendations/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            row_id: rowId,
            pblanc_ids: selectedIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            modalBody.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div style="color: #28a745; font-size: 48px; margin-bottom: 20px;">✓</div>
                    <h5 style="color: #333; margin-bottom: 15px;">저장 완료!</h5>
                    <p style="color: #666;">${data.message}</p>
                    <div style="margin-top: 20px;">
                        <button type="button" class="btn btn-primary" onclick="closeRecommendModal()" 
                                style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                            확인
                        </button>
                    </div>
                </div>
            `;
        } else {
            modalBody.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div style="color: #dc3545; font-size: 48px; margin-bottom: 20px;">✗</div>
                    <h5 style="color: #333; margin-bottom: 15px;">저장 실패</h5>
                    <p style="color: #666;">${data.error || '알 수 없는 오류가 발생했습니다.'}</p>
                    <div style="margin-top: 20px;">
                        <button type="button" class="btn btn-secondary" onclick="closeRecommendModal()" 
                                style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                            닫기
                        </button>
                    </div>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        modalBody.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div style="color: #dc3545; font-size: 48px; margin-bottom: 20px;">✗</div>
                <h5 style="color: #333; margin-bottom: 15px;">네트워크 오류</h5>
                <p style="color: #666;">저장 중 네트워크 오류가 발생했습니다.</p>
                <div style="margin-top: 20px;">
                    <button type="button" class="btn btn-secondary" onclick="closeRecommendModal()" 
                            style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                        닫기
                    </button>
                </div>
            </div>
        `;
    });
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

// 상세보기 모달 내의 추천 지원사업 공고 보기 버튼에 알림 표시를 추가하는 함수
function addNotificationToRecommendButton(rowId, recommendButton) {
    // 지원사업 속성에서 알림 데이터 확인
    fetch('/sales/get_saved_biz_recommendations/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ row_id: rowId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.data && data.data.length > 0) {
            // 새로 추가된 공고가 있는지 확인
            const hasNewRecommendations = data.data.some(item => item.isNew);
            if (hasNewRecommendations) {
                // 알림 표시 추가
                const notificationSpan = document.createElement('span');
                notificationSpan.innerHTML = '🔔';
                notificationSpan.style.cssText = 'color: #dc3545; font-weight: bold; margin-left: 8px; font-size: 14px;';
                notificationSpan.title = '새로운 추천 지원사업이 있습니다!';
                
                // 기존 알림이 있으면 제거
                const existingNotification = recommendButton.querySelector('.notification-bell');
                if (existingNotification) {
                    existingNotification.remove();
                }
                
                notificationSpan.className = 'notification-bell';
                recommendButton.appendChild(notificationSpan);
            }
        }
    })
    .catch(error => {
        console.error('알림 데이터 조회 실패:', error);
    });
}