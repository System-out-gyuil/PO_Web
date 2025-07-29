// 캘린더 설정 변수
let calendarSettings = {
    date_field: 'F/U 일정',
    content_fields: ['회사명', '미팅', '영업진행']
};

// 한국어 단위로 변환하는 함수 (백만 단위 기준)
function formatToKoreanCurrency(amount) {
    if (!amount || amount === 0) return '0원';
    
    const numAmount = typeof amount === 'string' ? parseInt(amount.replace(/[^\d]/g, '')) : amount;
    if (isNaN(numAmount) || numAmount === 0) return '0원';
    
    let result = '';
    let remaining = numAmount;
    
    // 백만 단위 이상인지 확인
    const isOverBaekman = remaining >= 1000000;
    
    // 억 단위 처리
    if (remaining >= 100000000) {
        const eok = Math.floor(remaining / 100000000);
        result += eok + '억';
        remaining = remaining % 100000000;
    }
    
    // 천만 단위 처리 (천으로 표시)
    if (remaining >= 10000000) {
        const cheon = Math.floor(remaining / 10000000);
        result += ' ' + cheon + '천';
        remaining = remaining % 10000000;
    }
    
    // 백만 단위 처리
    if (remaining >= 1000000) {
        const baek = Math.floor(remaining / 1000000);
        result += ' ' + baek + '백';
        remaining = remaining % 1000000;
    }
    
    // 천만이나 백만 단위가 있으면 '만원'으로 끝냄
    if (result.includes('천') || result.includes('백')) {
        return result + '만원';
    }
    // 억 단위만 있으면 '원'으로 끝냄
    else if (result && result.includes('억')) {
        return result + '원';
    }
    // 백만 단위 이상이면 '만원'으로 끝냄
    else if (isOverBaekman) {
        return result + '만원';
    }
    
    // 백만 단위 이하일 때는 만 단위까지 표시
    if (remaining >= 10000) {
        if (!result) {  // 앞에 억/천/백이 없을 때만
            result = Math.floor(remaining / 10000) + '만';
        } else {
            // 앞에 억/천/백이 있을 때는 만 단위가 0이 아닐 때만 추가
            if (Math.floor(remaining / 10000) > 0) {
                result += Math.floor(remaining / 10000) + '만';
            }
        }
        remaining = remaining % 10000;
    }
    
    // 10,000 미만의 값은 그대로 표시
    if (remaining > 0 && remaining < 10000) {
        if (result) {
            result += remaining;
        } else {
            result = remaining.toString();
        }
    }
    
    return result + '원';
}

// 캘린더 리렌더링 함수
function refreshCalendar() {
    if (window.calendar && typeof window.calendar.refetchEvents === 'function') {
        window.calendar.refetchEvents();
    }
}

// 완전 랜덤 16진수 색상 함수
function randomColor() {
    return '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');
}

// 캘린더 설정 모달 함수
function showCalendarSettingsModal(forceSettings) {
    console.log('showCalendarSettingsModal');
    Promise.all([
        fetch('/sales/get_datetime_attributes/').then(r => r.json()),
        fetch('/sales/get_user_attributes/').then(r => r.json()),
        fetch('/sales/get_calendar_settings/').then(r => r.json())
    ]).then(([datetimeData, attributesData, settingsData]) => {
        if (!datetimeData.success || !attributesData.success || !settingsData.success) {
            alert('설정을 불러오는데 실패했습니다.');
            return;
        }

        // settings를 window.calendarSettings에 저장 (forceSettings가 있으면 그걸 사용)
        let settings = forceSettings || settingsData.settings || {};
        settings.date_fields = settings.date_fields || [];
        settings.custom_events = settings.custom_events || [];
        window.calendarSettings = settings;

        const datetimeAttrs = datetimeData.attributes;
        const allAttrs = attributesData.attributes;

        // 기준 날짜 필드 체크박스 - view_check 필드로 표시 여부 제어
        const dateFieldIds = settings.date_fields.map(df => df.attribute);
        // 컬러 정보 맵 생성 (DB에 저장된 값만 사용)
        const dateFieldColors = {};
        settings.date_fields.forEach(df => { 
            dateFieldColors[df.attribute] = df.color; 
        });
        
        const dateFieldOptions = datetimeAttrs
            .filter(attr => attr.name !== '개업년월') // 개업년월 제외
            .map(attr => {
            let color = dateFieldColors[attr.id];
            if (dateFieldIds.includes(attr.id) && !color) {
                color = randomColor();
                dateFieldColors[attr.id] = color;
                let df = settings.date_fields.find(df => df.attribute === attr.id);
                if (df) df.color = color;
            }
            const existingField = settings.date_fields.find(df => df.attribute === attr.id);
            const isChecked = existingField ? (existingField.view_check !== false) : false;
            const allowedTypes = ['text', 'datetime', 'region', 'region detail', 'number'];
            const filteredAttrs = allAttrs.filter(a => allowedTypes.includes(a.type) && a.name !== '회사명' && a.name !== '개업년월');
            const checkboxOptions = filteredAttrs.map(a => 
                `<div class="content-checkbox-row" style="display:flex;align-items:center;padding:4px 8px;margin:2px 0;">
                    <input type="checkbox" class="content-checkbox" data-date-attr="${attr.id}" value="${a.name}" ${existingField && existingField.content_fields.includes(a.name) ? 'checked' : ''} style="margin-right:8px; width: 10%;">
                    <label style="margin:0;cursor:pointer;font-size:13px; width: 90%;">${a.name}</label>
                </div>`
            ).join('');
            return `<div style="margin-bottom:12px;border:1px solid #e0e0e0;border-radius:6px;overflow:hidden;">
                <div style="display:flex;align-items:center;padding:8px 12px;background:#f8f9fa;">
                    <input type="checkbox" class="date-field-checkbox" value="${attr.id}" ${isChecked ? 'checked' : ''} style="margin-right:8px;">
                    <span style="margin-right:8px;min-width:80px;font-weight:500;">${attr.name}</span>
                    <input type="color" class="date-field-color" value="${color || '#e5e7eb'}" data-date-attr="${attr.id}" style="width:35px;height:35px;border:none;background:none;cursor:pointer;margin-right:8px;">
                    <button type="button" class="content-select-btn" data-date-attr="${attr.id}" style="padding:4px 10px;font-size:13px;border:1px solid #bbb;background:#fff;border-radius:4px;cursor:pointer;">카드에 표시할 내용 선택</button>
                </div>
                <div class="content-checkboxes-popup" data-date-attr="${attr.id}" style="display:none;position:absolute;z-index:2000;min-width:180px;max-width:320px;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #bbb;border-radius:8px;padding:10px 8px;">
                    ${checkboxOptions}
                </div>
            </div>`;
        }).join('');

        // 팝업 열기/닫기 및 바깥 클릭 처리
        setTimeout(() => {
            document.querySelectorAll('.content-select-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const attrId = this.getAttribute('data-date-attr');
                    const popup = document.querySelector(`.content-checkboxes-popup[data-date-attr="${attrId}"]`);
                    
                    // 현재 팝업이 열려있는지 확인
                    const isCurrentlyOpen = popup && popup.style.display === 'block';
                    
                    // 모든 팝업 닫기
                    document.querySelectorAll('.content-checkboxes-popup').forEach(p => p.style.display = 'none');
                    
                    // 현재 팝업이 닫혀있었다면 열기
                    if (!isCurrentlyOpen) {
                        if (popup) {
                            const rect = this.getBoundingClientRect();
                            popup.style.display = 'block';
                            popup.style.position = 'fixed';
                            popup.style.left = (rect.left) + 'px';
                            popup.style.top = (rect.bottom + 4) + 'px';
                        }
                    }
                });
            });
            // 바깥 클릭 시 팝업 닫기
            document.addEventListener('mousedown', function(e) {
                if (!e.target.closest('.content-checkboxes-popup') && !e.target.classList.contains('content-select-btn')) {
                    document.querySelectorAll('.content-checkboxes-popup').forEach(p => p.style.display = 'none');
                }
            });
        }, 0);

        // 날짜 필드별 카드에 표시할 내용 드롭다운
        function renderContentFieldsSection() {
            return datetimeAttrs.map(attr => {
                const df = settings.date_fields.find(df => df.attribute === attr.id) || { content_fields: ['회사명'], color: dateFieldColors[attr.id] || randomColor() };
                // 회사명은 항상 기본 포함, 드롭다운에는 안 보임
                const allowedTypes = ['text', 'datetime', 'region', 'region detail', 'number'];
                const filteredAttrs = allAttrs.filter(a => allowedTypes.includes(a.type) && a.name !== '회사명' && a.name !== '개업년월');
                
                // 드롭다운 옵션 생성
                const dropdownOptions = filteredAttrs.map(a => 
                    `<option value="${a.name}" ${df.content_fields.includes(a.name) ? 'selected' : ''}>${a.name}</option>`
                ).join('');
                
                // view_check 필드로 표시 여부 확인
                const isVisible = df.view_check !== false;
                
                return `
                    <div class="content-fields-section" data-date-attr="${attr.id}" style="margin-bottom:18px;${isVisible ? '' : 'display:none;'}">
                        <div style="font-weight:bold;color:#333;margin-bottom:6px;">[${attr.name}] 카드에 표시할 내용</div>
                        <select class="content-fields-dropdown" data-date-attr="${attr.id}" multiple style="width:100%;min-height:100px;padding:8px;border:1px solid #ddd;border-radius:4px;">
                            ${dropdownOptions}
                        </select>
                        <div style="font-size:12px;color:#666;margin-top:4px;">Ctrl+클릭으로 여러 항목 선택 가능</div>
                    </div>
                `;
            }).join('');
        }

        // 커스텀 이벤트 UI (color 필드 추가, 누락시 자동 랜덤색상 보정)
        function renderCustomEventsSection() {
            const events = settings.custom_events || [];
            // color가 없으면 랜덤 색상 부여
            events.forEach(ev => {
                if (!ev.color || ev.color === 'undefined' || ev.color === '') {
                    ev.color = randomColor();
                }
            });
            return `
                <div style="margin-top:18px;">
                    <div style="font-weight:bold;color:#333;margin-bottom:6px;">일정 추가</div>
                    <div id="customEventsList">
                        ${events.map((ev, idx) => `
                            <div class="custom-event-row" data-idx="${idx}" style="display:flex;align-items:center;margin-bottom:6px;gap:4px;">
                                <input type="text" class="custom-event-title" value="${ev.title || ''}" placeholder="제목" style="width:80px;">
                                <input type="date" class="custom-event-start" value="${ev.start || ev.date || ''}" style="width:120px;">
                                <span style="margin:0 2px;">~</span>
                                <input type="date" class="custom-event-end" value="${ev.end || ev.date || ''}" style="width:120px;">
                                <input type="text" class="custom-event-content" value="${ev.content || ''}" placeholder="내용" style="width:100px;">
                                <input type="color" class="custom-event-color" value="${ev.color || '#e5e7eb'}" style="width:28px;height:28px;border:none;background:none;cursor:pointer;">
                                <button type="button" class="remove-custom-event" style="color:#fff;background:#dc3545;border:none;border-radius:3px;padding:2px 8px;cursor:pointer;">삭제</button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" id="addCustomEventBtn" style="margin-top:6px;padding:4px 12px;background:#007bff;color:#fff;border:none;border-radius:4px;cursor:pointer;">+ 일정 추가</button>
                </div>
            `;
        }

        // 스타일(한 번만)
        if (!document.getElementById('calendarSettingRowStyle')) {
            const style = document.createElement('style');
            style.id = 'calendarSettingRowStyle';
            style.innerHTML = `
                .calendar-setting-row {
                    display: flex;
                    align-items: center;
                    padding: 4px 8px;
                    border-radius: 4px;
                    transition: background 0.2s;
                    cursor: pointer;
                }
                .calendar-setting-row.checked-row {
                    background: #e6f0fa;
                }
                .calendar-setting-row label {
                    width: 90%;
                    margin-left: 8px;
                    margin-bottom: 0;
                    cursor: pointer;
                }
                /* 캘린더 스크롤바 숨김 */
                #calendar {
                    overflow-x: auto;
                    overflow-y: auto;
                    /* 스크롤은 되지만 스크롤바는 안 보이게 */
                    scrollbar-width: none; /* Firefox */
                    -ms-overflow-style: none; /* IE, Edge */
                }
                #calendar::-webkit-scrollbar {
                    display: none; /* Chrome, Safari, Opera */
                }
            `;
            document.head.appendChild(style);
        }

        // 모달 HTML
        const modalHTML = `
            <div id="calendarSettingsModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000;">
                <div style="background:white;border-radius:8px;padding:20px;width:640px;max-width:95vw;max-height:90vh;overflow-y:auto;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <h3 style="margin:0;color:#333;">캘린더 설정</h3>
                        <button onclick="closeCalendarSettingsModal()" style="background:none;border:none;font-size:20px;cursor:pointer;">&times;</button>
                    </div>
                    <div style="margin-bottom:18px;">
                        <label style="display:block;margin-bottom:8px;font-weight:bold;color:#333;">카드 생성 기준 날짜 필드(복수 선택):</label>
                        <div style="font-size:12px;color:#666;margin-bottom:8px;">각 필드 오른쪽에서 카드의 색상과 카드에 표시할 내용을 선택하세요.</div>
                        <div id="dateFieldCheckboxes">${dateFieldOptions}</div>
                    </div>
                    ${renderCustomEventsSection()}
                    <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:18px;">
                        <button onclick="closeCalendarSettingsModal()" style="padding:8px 16px;border:1px solid #ddd;background:#f8f9fa;border-radius:4px;cursor:pointer;">취소</button>
                        <button onclick="saveCalendarSettings()" style="padding:8px 16px;border:none;background:#007bff;color:white;border-radius:4px;cursor:pointer;">저장</button>
                    </div>
                </div>
            </div>
        `;

        // 기존 모달 제거 후 새 모달 추가
        const existingModal = document.getElementById('calendarSettingsModal');
        if (existingModal) existingModal.remove();
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // 동적 이벤트 바인딩
        // 1. 기준 날짜 필드 체크박스 → settings.date_fields 업데이트 (view_check 필드로 제어)
        document.querySelectorAll('.date-field-checkbox').forEach(cb => {
            cb.addEventListener('change', function() {
                const attrId = parseInt(this.value);
                let df = settings.date_fields.find(df => df.attribute === attrId);
                
                if (this.checked) {
                    // 없으면 settings.date_fields에 추가 (랜덤 색상)
                    if (!df) {
                        df = { attribute: attrId, content_fields: ['회사명'], color: dateFieldColors[attrId] || randomColor(), view_check: true };
                        settings.date_fields.push(df);
                    } else {
                        // 기존 설정 유지하면서 view_check만 true로 설정
                        df.view_check = true;
                    }
                } else {
                    // settings.date_fields에서 제거하지 않고 view_check만 false로 설정
                    if (df) {
                        df.view_check = false;
                    }
                }
            });
        });

        // 1-2. 컬러피커 변경 시 settings.date_fields의 color 동기화
        document.querySelectorAll('.date-field-color').forEach(input => {
            input.addEventListener('input', function() {
                const attrId = parseInt(this.getAttribute('data-date-attr'));
                let df = settings.date_fields.find(df => df.attribute === attrId);
                if (df) df.color = this.value;
                dateFieldColors[attrId] = this.value;
            });
        });

        // 1-3. 카드 생성 기준 날짜 필드의 드롭다운 변경 시 settings.date_fields 동기화
        document.querySelectorAll('.date-field-content-dropdown').forEach(dropdown => {
            dropdown.addEventListener('change', function() {
                const attrId = parseInt(this.getAttribute('data-date-attr'));
                let df = settings.date_fields.find(df => df.attribute === attrId);
                if (!df) {
                    df = { attribute: attrId, content_fields: ['회사명'], color: dateFieldColors[attrId] || randomColor(), view_check: true };
                    settings.date_fields.push(df);
                }
                // 선택된 옵션들로 content_fields 업데이트
                df.content_fields = ['회사명'].concat(
                    Array.from(this.options).filter(opt => opt.selected).map(opt => opt.value)
                );
            });
        });

        // 1-4. 체크박스 변경 시 settings.date_fields 동기화
        document.querySelectorAll('.content-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const attrId = parseInt(this.getAttribute('data-date-attr'));
                const value = this.value;
                let df = settings.date_fields.find(df => df.attribute === attrId);
                if (!df) {
                    df = { attribute: attrId, content_fields: ['회사명'], color: dateFieldColors[attrId] || randomColor(), view_check: true };
                    settings.date_fields.push(df);
                }
                
                if (this.checked) {
                    if (!df.content_fields.includes(value)) {
                        df.content_fields.push(value);
                    }
                } else {
                    df.content_fields = df.content_fields.filter(f => f !== value);
                }
                
                // 회사명은 항상 포함
                if (!df.content_fields.includes('회사명')) df.content_fields.unshift('회사명');
            });
        });
        // 3. 커스텀 이벤트 추가/삭제/수정
        document.getElementById('addCustomEventBtn').onclick = function() {
            window.calendarSettings.custom_events = window.calendarSettings.custom_events || [];
            // 새 커스텀 일정 추가 (color도 포함)
            window.calendarSettings.custom_events.push({ title: '', date: '', content: '', color: '#e5e7eb' });
            // 모달 리렌더링 없이 행만 동적으로 추가
            const idx = window.calendarSettings.custom_events.length - 1;
            const rowHtml = `
                <div class="custom-event-row" data-idx="${idx}" style="gap:4px;display:flex;align-items:center;margin-bottom:6px;">
                    <input type="text" class="custom-event-title" value="" placeholder="제목" style="width:80px;">
                    <input type="date" class="custom-event-start" value="" style="width:120px;">
                    <span style="margin:0 2px;">~</span>
                    <input type="date" class="custom-event-end" value="" style="width:120px;">
                    <input type="text" class="custom-event-content" value="" placeholder="내용" style="width:100px;">
                    <input type="color" class="custom-event-color" value="#e5e7eb" style="width:28px;height:28px;border:none;background:none;cursor:pointer;">
                    <button type="button" class="remove-custom-event" style="color:#fff;background:#dc3545;border:none;border-radius:3px;padding:2px 8px;cursor:pointer;">삭제</button>
                </div>
            `;
            document.getElementById('customEventsList').insertAdjacentHTML('beforeend', rowHtml);
            bindCustomEventRowEvents(idx);
        };
        // 삭제/수정 이벤트 바인딩 함수
        function bindCustomEventRowEvents(idx) {
            const row = document.querySelector(`.custom-event-row[data-idx="${idx}"]`);
            if (!row) return;
            row.querySelector('.remove-custom-event').onclick = function() {
                window.calendarSettings.custom_events.splice(idx, 1);
                row.remove();
                // 인덱스 재정렬
                document.querySelectorAll('.custom-event-row').forEach((r, i) => r.setAttribute('data-idx', i));
            };
            row.querySelector('.custom-event-title').addEventListener('input', function() {
                window.calendarSettings.custom_events[idx].title = this.value;
            });
            row.querySelector('.custom-event-start').addEventListener('input', function() {
                window.calendarSettings.custom_events[idx].start = this.value;
            });
            row.querySelector('.custom-event-end').addEventListener('input', function() {
                window.calendarSettings.custom_events[idx].end = this.value;
            });
            row.querySelector('.custom-event-content').addEventListener('input', function() {
                window.calendarSettings.custom_events[idx].content = this.value;
            });
            row.querySelector('.custom-event-color').addEventListener('input', function() {
                window.calendarSettings.custom_events[idx].color = this.value;
            });
        }
        // 기존 커스텀 이벤트 행에도 바인딩
        document.querySelectorAll('.custom-event-row').forEach((row, idx) => bindCustomEventRowEvents(idx));
    }).catch(error => {
        console.error('캘린더 설정 모달 생성 오류:', error);
        alert('설정을 불러오는데 실패했습니다.');
    });
}

function closeCalendarSettingsModal() {
    const modal = document.getElementById('calendarSettingsModal');
    if (modal) {
        modal.remove();
    }
}

// 드롭다운 토글 함수
function toggleContentDropdown(attrId) {
    const checkboxes = document.querySelector(`.content-checkboxes[data-date-attr="${attrId}"]`);
    const arrow = document.querySelector(`[onclick="toggleContentDropdown(${attrId})"] .dropdown-arrow`);
    
    if (checkboxes.style.display === 'none') {
        checkboxes.style.display = 'block';
        arrow.textContent = '▲';
    } else {
        checkboxes.style.display = 'none';
        arrow.textContent = '▼';
    }
}

function saveCalendarSettings() {
    const modal = document.getElementById('calendarSettingsModal');
    if (!modal) return;

    // 1. 기준 날짜 필드
    const dateFieldIds = Array.from(modal.querySelectorAll('.date-field-checkbox:checked')).map(cb => parseInt(cb.value));

    // 1-1. 각 필드의 컬러 값 매핑
    const colorInputs = Array.from(modal.querySelectorAll('.date-field-color'));
    const colorMap = {};
    colorInputs.forEach(input => {
        const attrId = parseInt(input.getAttribute('data-date-attr'));
        colorMap[attrId] = input.value;
    });

    // 2. 각 날짜 필드별 표시 내용 + color + view_check
    const date_fields = [];
    
    // 모든 datetime 속성에 대해 처리
    const allDateTimeAttrs = Array.from(modal.querySelectorAll('.date-field-checkbox')).map(cb => parseInt(cb.value));
    
    allDateTimeAttrs.forEach(attrId => {
        const isChecked = modal.querySelector(`.date-field-checkbox[value="${attrId}"]`).checked;
        const checkedFields = ['회사명'].concat(
            Array.from(modal.querySelectorAll(`.content-checkbox[data-date-attr="${attrId}"]:checked`)).map(cb => cb.value)
        ).filter((v, i, arr) => arr.indexOf(v) === i);
        
        // 기존 설정이 있으면 유지하고 view_check만 업데이트
        const existingField = window.calendarSettings.date_fields.find(df => df.attribute === attrId);
        if (existingField) {
            existingField.view_check = isChecked;
            existingField.color = colorMap[attrId] || existingField.color;
            existingField.content_fields = checkedFields;
            date_fields.push(existingField);
        } else {
            // 새로 추가되는 경우
            date_fields.push({ 
                attribute: attrId, 
                content_fields: checkedFields, 
                color: colorMap[attrId] || '#e5e7eb',
                view_check: isChecked
            });
        }
    });

    // 3. 커스텀 이벤트 (color 포함)
    const custom_events = Array.from(modal.querySelectorAll('.custom-event-row')).map(row => ({
        title: row.querySelector('.custom-event-title').value,
        start: row.querySelector('.custom-event-start').value,
        end: row.querySelector('.custom-event-end').value,
        date: row.querySelector('.custom-event-start').value, // 호환성
        content: row.querySelector('.custom-event-content').value,
        color: row.querySelector('.custom-event-color').value
    }));

    const settings = { date_fields, custom_events };

    fetch('/sales/save_calendar_settings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ settings })
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            if (window.calendar && typeof window.calendar.refetchEvents === 'function') {
                window.calendar.refetchEvents();
            } else {
                initializeCalendarWithSettings();
            }
            closeCalendarSettingsModal();
            alert('캘린더 설정이 저장되었습니다.');
        } else {
            alert('설정 저장에 실패했습니다: ' + (data.error || ''));
        }
    }).catch(error => {
        console.error('설정 저장 오류:', error);
        alert('설정 저장 중 오류가 발생했습니다.');
    });
}

// 개업년월 필드의 새로운 JSON 형식 처리 함수
function formatBusinessOpeningDate(value) {
    if (!value) return '';
    
    try {
        // JSON 형식인지 확인
        if (typeof value === 'string' && value.startsWith('{')) {
            const data = JSON.parse(value);
            
            // opening_date가 있으면 그대로 반환
            if (data.opening_date) {
                return data.opening_date;
            }
            
            // years_ago가 있으면 "n년전" 형식으로 반환
            if (data.years_ago) {
                return `${data.years_ago}년전`;
            }
        }
        
        // 기존 형식이거나 파싱 실패시 그대로 반환
        return value;
    } catch (e) {
        // JSON 파싱 실패시 그대로 반환
        return value;
    }
}

// 캘린더 초기화 함수 (설정을 반영한 버전)
function initializeCalendarWithSettings() {
    console.log('initializeCalendarWithSettings 호출됨');
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;
    
    // 기존 설정이 있으면 그대로 사용하고, 없을 때만 기본 설정 생성
    if (!window.calendarSettings) {
        window.calendarSettings = { 
            date_fields: [], 
            custom_events: [] 
        };
        
        // 기본 datetime 속성들을 자동으로 찾아서 설정 (기존 설정이 없을 때만)
        if (window.ATTR_FIELDS) {
            const datetimeAttrs = window.ATTR_FIELDS.filter(attr => 
                attr.attributeType_name === 'datetime' && attr.name !== '개업년월'
            );
            
            datetimeAttrs.forEach(attr => {
                window.calendarSettings.date_fields.push({
                    attribute: attr.id,
                    content_fields: ['회사명'],
                    color: randomColor(),
                    view_check: true
                });
            });
        }
    }

    // 모든 기준 날짜 필드의 이벤트를 한 번에 불러옴
    const eventUrl = `/sales/calendar_events/`;

    // 캘린더 렌더 직후 한 번만 모든 셀의 테두리 초기화
    function clearAllCellBorders() {
        document.querySelectorAll('.fc-daygrid-day').forEach(cell => {
            cell.style.border = '';
        });
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'ko',
        height: 900,
        events: eventUrl,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,listMonth'
        },
        eventOrder: function(a, b) {
            // 커스텀 일정이 항상 먼저(위에) 오도록
            if ((b.extendedProps.is_custom ? 1 : 0) - (a.extendedProps.is_custom ? 1 : 0) !== 0) {
                return (b.extendedProps.is_custom ? 1 : 0) - (a.extendedProps.is_custom ? 1 : 0);
            }
            // 같은 종류면 기본 정렬
            return a.start - b.start;
        },
        eventContent: function(arg) {
            const name = arg.event.title;
            const content = arg.event.extendedProps.content || {};
            const status = arg.event.extendedProps.status_name;
            const statusColor = arg.event.extendedProps.status_color || '#bbb';
            const dateFieldName = arg.event.extendedProps.date_field_name || '';
            let dateFieldColor = arg.event.extendedProps.date_field_color || arg.event.extendedProps.color;
            if (!dateFieldColor || dateFieldColor === 'undefined' || dateFieldColor === '') dateFieldColor = '#e5e7eb';
            if (arg.event.extendedProps.is_custom) {
                console.log('커스텀 일정 카드 color:', name, dateFieldColor);
            }
            let colorRgba = hexToRgba(dateFieldColor, arg.event.extendedProps.is_custom ? 0.45 : 0.5);

            const fields = Object.keys(content)
                .filter(field => field !== '회사명')
                .map((field, idx, arr) => {
                    const isLast = idx === arr.length - 1;
                    let fieldValue = content[field] || '';
                    
                    // 개업년월 필드인 경우 특별 처리
                    if (field === '개업년월') {
                        fieldValue = formatBusinessOpeningDate(fieldValue);
                    }
                    // 매출 관련 필드인 경우 한국어 숫자 형식으로 변환
                    else if (field.includes('매출') || field.includes('매출액') || field.includes('매출금') || field.includes('매출액') || field.includes('매출금액')) {
                        if (fieldValue && fieldValue !== '0' && fieldValue !== '') {
                            fieldValue = formatToKoreanCurrency(fieldValue);
                        }
                    }
                    
                    return `
                        <div style="
                            display:flex;
                            align-items:center;
                            font-size:0.97em;
                            padding:3px 0 3px 0;
                            ${!isLast ? 'border-bottom:1px solid #e5e7eb;' : ''}
                        ">
                            <span style="color:#888;min-width:70px;flex-shrink:0;">${field}</span>
                            <span style="margin-left:8px;color:#222;word-break:break-all;white-space:normal;display:inline-block;max-width:180px;text-align:left;">${fieldValue}</span>
                        </div>
                    `;
                }).join('');

            let statusHtml = '';
            if (status) {
                statusHtml = `<span style="display:inline-block;background:${statusColor};color:#fff;padding:2px 8px;border-radius:6px;font-size:0.92em;margin-top:6px;">${status}</span>`;
            }

            return {
                html: `
                    <div style="
                        width:100%;
                        box-sizing:border-box;
                        padding:10px 12px 8px 12px;
                        border-radius:12px;
                        background:${colorRgba};
                        box-shadow:0 2px 8px 0 rgba(0,0,0,0.06);
                        border:1px solid rgb(158, 158, 158);
                        color:#222;
                    ">
                    <div style="display:flex;align-items:center;justify-content:space-between;">
                        ${dateFieldName !== '커스텀' ? `<div style="width:30%; font-size:1.05em;font-weight:bold;color:000;margin-bottom:2px;">${dateFieldName}</div>` : ''}
                        <div style="width:70%; font-weight:bold; font-size:1.08em; margin-bottom:6px;">${name}</div>
                    </div>
                        ${fields}
                        ${statusHtml}
                    </div>
                `
            };
        },
        eventClick: function(info) {
            // 커스텀 일정이면 상세보기 모달을 띄우지 않음
            if (info.event.extendedProps.is_custom) {
                return;
            }
            // 이벤트 클릭 시 기존 상세보기 모달 표시
            const rowId = info.event.id.split('_')[0];
            fetch(`/sales/get_row_details/${rowId}/`)
                .then(r => r.json())
                .then(function(data) {
                    if (data.success) {
                        showDetailModal(data.row_data, data.row_id);
                    } else {
                        alert('상세정보 불러오기 실패: ' + (data.error || ''));
                    }
                });
        },
        eventDidMount: function(arg) {
            // 커스텀 일정 기간 지원: start~end
            if (arg.event.extendedProps.is_custom) {
                let color = arg.event.extendedProps.date_field_color || arg.event.extendedProps.color;
                if (!color || color === 'undefined' || color === '') color = '#e5e7eb';
                // 기간 처리 - 백엔드에서 이미 하루를 더해서 보내주므로 그대로 사용
                let start = arg.event.start;
                let end = arg.event.end ? arg.event.end : start;
                let current = new Date(start);
                while (current < end) {
                    const dateStr = current.toISOString().slice(0, 10);
                    const cell = document.querySelector(`.fc-daygrid-day[data-date='${dateStr}']`);
                    // if (cell) {
                    //     cell.style.border = `2.5px solid ${color}`;
                    // }
                    current.setDate(current.getDate() + 1);
                }
            }
        },
        datesSet: function() {
            // 뷰가 바뀔 때마다 셀 테두리 초기화
            clearAllCellBorders();
        }
    });

    calendar.render();
    window.calendar = calendar;
    // 렌더 직후 한 번 초기화
    clearAllCellBorders();
}

// DOMContentLoaded 시점에 캘린더 자동 렌더링
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCalendarWithSettings);
} else {
    initializeCalendarWithSettings();
}