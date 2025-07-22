// 칸반보드 설정 변수
let kanbanSettings = {
    main_attr: '',
    filters: [],
    custom_rules: []
};

// 완전 랜덤 16진수 색상 함수
function randomColor() {
    return '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');
}

// 칸반보드 설정 모달 함수
function showKanbanSettingsModal() {
    console.log('showKanbanSettingsModal');
    Promise.all([
        fetch('/sales/get_dropdown_attributes_for_kanban/').then(r => r.json()),
        fetch('/sales/get_kanban_settings/').then(r => r.json())
    ]).then(([attributesData, settingsData]) => {
        if (!attributesData.success || !settingsData.success) {
            alert('설정을 불러오는데 실패했습니다.');
            return;
        }

        // settings를 window.kanbanSettings에 저장
        let settings = settingsData.settings || {};
        settings.main_attr = settings.main_attr || '';
        settings.filters = settings.filters || [];
        settings.custom_rules = settings.custom_rules || [];
        window.kanbanSettings = settings;

        const attributes = attributesData.attributes;
        // 속성 데이터를 전역 변수로 저장
        window.attributes = attributes;

        // 메인 속성 선택 드롭다운
        const mainAttrOptions = attributes.map(attr => 
            `<option value="${attr.name}" ${settings.main_attr === attr.name ? 'selected' : ''}>${attr.name}</option>`
        ).join('');

        // 필터 UI 생성
        function renderFiltersSection() {
            const filters = settings.filters || [];
            return `
                <div style="margin-top:18px;">
                    <div style="font-weight:bold;color:#333;margin-bottom:8px;">조건부 필터 설정</div>
                    <div style="font-size:12px;color:#666;margin-bottom:12px;">
                        특정 조건이 만족될 때만 칸반보드에 표시되도록 설정합니다.
                    </div>
                    <div id="filtersList">
                        ${filters.map((filter, idx) => `
                            <div class="filter-row" data-idx="${idx}" style="display:flex;align-items:center;margin-bottom:8px;gap:8px;padding:12px;border:1px solid #e0e0e0;border-radius:6px;">
                                <select class="filter-attr" data-idx="${idx}" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                    ${attributes.map(attr => 
                                        `<option value="${attr.name}" ${filter.attribute === attr.name ? 'selected' : ''}>${attr.name}</option>`
                                    ).join('')}
                                </select>
                                <select class="filter-operator" data-idx="${idx}" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                    <option value="equals" ${filter.operator === 'equals' ? 'selected' : ''}>같음</option>
                                    <option value="not_equals" ${filter.operator === 'not_equals' ? 'selected' : ''}>다름</option>
                                    <option value="contains" ${filter.operator === 'contains' ? 'selected' : ''}>포함</option>
                                    <option value="not_contains" ${filter.operator === 'not_contains' ? 'selected' : ''}>포함안함</option>
                                </select>
                                <select class="filter-value" data-idx="${idx}" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                    ${getFilterValueOptions(filter.attribute, filter.value)}
                                </select>
                                <button type="button" class="remove-filter" data-idx="${idx}" style="color:#fff;background:#dc3545;border:none;border-radius:3px;padding:4px 8px;cursor:pointer;">삭제</button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" id="addFilterBtn" style="margin-top:8px;padding:6px 12px;background:#28a745;color:#fff;border:none;border-radius:4px;cursor:pointer;">+ 필터 추가</button>
                </div>
            `;
        }

        // 필터 값 옵션 생성 함수
        function getFilterValueOptions(attrName, selectedValue) {
            if (!attrName) return '<option value="">속성을 선택하세요</option>';
            
            const attr = attributes.find(a => a.name === attrName);
            if (!attr) return '<option value="">속성을 찾을 수 없습니다</option>';
            
            return `
                <option value="">값을 선택하세요</option>
                ${attr.options.map(opt => 
                    `<option value="${opt.id}" ${selectedValue == opt.id ? 'selected' : ''}>${opt.name}</option>`
                ).join('')}
            `;
        }

        // 커스텀 규칙 UI 생성
        function renderCustomRulesSection() {
            const rules = settings.custom_rules || [];
            return `
                <div style="margin-top:18px;">
                    <div style="font-weight:bold;color:#333;margin-bottom:8px;">커스텀 규칙 설정</div>
                    <div style="font-size:12px;color:#666;margin-bottom:12px;">
                        복잡한 조건을 설정하여 특정 상황에서만 카드가 표시되도록 합니다.
                    </div>
                    <div id="customRulesList">
                        ${rules.map((rule, idx) => `
                            <div class="custom-rule-row" data-idx="${idx}" style="margin-bottom:12px;padding:12px;border:1px solid #e0e0e0;border-radius:6px;">
                                <div style="display:flex;align-items:center;margin-bottom:8px;gap:8px;">
                                    <input type="text" class="custom-rule-name" value="${rule.name || ''}" placeholder="규칙 이름" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                    <select class="custom-rule-logic" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                        <option value="AND" ${rule.logic === 'AND' ? 'selected' : ''}>AND</option>
                                        <option value="OR" ${rule.logic === 'OR' ? 'selected' : ''}>OR</option>
                                    </select>
                                    <button type="button" class="remove-custom-rule" data-idx="${idx}" style="color:#fff;background:#dc3545;border:none;border-radius:3px;padding:4px 8px;cursor:pointer;">삭제</button>
                                </div>
                                <div class="custom-rule-conditions" style="margin-left:20px;">
                                    ${(rule.conditions || []).map((condition, condIdx) => `
                                        <div class="custom-condition-row" data-cond-idx="${condIdx}" style="display:flex;align-items:center;margin-bottom:6px;gap:8px;">
                                            <select class="custom-condition-attr" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                                ${attributes.map(attr => 
                                                    `<option value="${attr.name}" ${condition.attribute === attr.name ? 'selected' : ''}>${attr.name}</option>`
                                                ).join('')}
                                            </select>
                                            <select class="custom-condition-operator" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                                <option value="equals" ${condition.operator === 'equals' ? 'selected' : ''}>같음</option>
                                                <option value="not_equals" ${condition.operator === 'not_equals' ? 'selected' : ''}>다름</option>
                                                <option value="contains" ${condition.operator === 'contains' ? 'selected' : ''}>포함</option>
                                                <option value="not_contains" ${condition.operator === 'not_contains' ? 'selected' : ''}>포함안함</option>
                                            </select>
                                            <select class="custom-condition-value" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                                                ${getFilterValueOptions(condition.attribute, condition.value)}
                                            </select>
                                            <button type="button" class="remove-custom-condition" style="color:#fff;background:#ffc107;border:none;border-radius:3px;padding:2px 6px;cursor:pointer;">삭제</button>
                                        </div>
                                    `).join('')}
                                </div>
                                <button type="button" class="add-custom-condition" data-rule-idx="${idx}" style="margin-top:6px;padding:4px 8px;background:#17a2b8;color:#fff;border:none;border-radius:3px;cursor:pointer;font-size:12px;">+ 조건 추가</button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" id="addCustomRuleBtn" style="margin-top:8px;padding:6px 12px;background:#6f42c1;color:#fff;border:none;border-radius:4px;cursor:pointer;">+ 커스텀 규칙 추가</button>
                </div>
            `;
        }

        // 모달 HTML
        const modalHTML = `
            <div id="kanbanSettingsModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000;">
                <div style="background:white;border-radius:8px;padding:20px;width:700px;max-width:95vw;max-height:90vh;overflow-y:auto;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <h3 style="margin:0;color:#333;">칸반보드 설정</h3>
                        <button onclick="closeKanbanSettingsModal()" style="background:none;border:none;font-size:20px;cursor:pointer;">&times;</button>
                    </div>
                    
                    <div style="margin-bottom:18px;">
                        <label style="display:block;margin-bottom:8px;font-weight:bold;color:#333;">메인 칸반보드 속성:</label>
                        <select id="mainAttrSelect" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                            <option value="">속성을 선택하세요</option>
                            ${mainAttrOptions}
                        </select>
                        <div style="font-size:12px;color:#666;margin-top:4px;">
                            이 속성을 기준으로 칸반보드가 구성됩니다.
                        </div>
                    </div>
                    
                    ${renderFiltersSection()}
                    ${renderCustomRulesSection()}
                    
                    <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:20px;">
                        <button onclick="closeKanbanSettingsModal()" style="padding:8px 16px;border:1px solid #ddd;background:#f8f9fa;border-radius:4px;cursor:pointer;">취소</button>
                        <button onclick="saveKanbanSettings()" style="padding:8px 16px;border:none;background:#007bff;color:white;border-radius:4px;cursor:pointer;">저장</button>
                    </div>
                </div>
            </div>
        `;

        // 기존 모달 제거 후 새 모달 추가
        const existingModal = document.getElementById('kanbanSettingsModal');
        if (existingModal) existingModal.remove();
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // 동적 이벤트 바인딩
        bindFilterEvents();
        bindCustomRuleEvents();
    }).catch(error => {
        console.error('칸반보드 설정 모달 생성 오류:', error);
        alert('설정을 불러오는데 실패했습니다.');
    });
}

// 필터 이벤트 바인딩
function bindFilterEvents() {
    // 필터 추가 버튼
    document.getElementById('addFilterBtn').onclick = function() {
        window.kanbanSettings.filters = window.kanbanSettings.filters || [];
        window.kanbanSettings.filters.push({
            attribute: '',
            operator: 'equals',
            value: ''
        });
        
        const idx = window.kanbanSettings.filters.length - 1;
        const filterRow = createFilterRow(idx);
        document.getElementById('filtersList').insertAdjacentHTML('beforeend', filterRow);
        bindFilterRowEvents(idx);
    };

    // 기존 필터 행들에 이벤트 바인딩
    document.querySelectorAll('.filter-row').forEach((row, idx) => {
        bindFilterRowEvents(idx);
    });
}

// 필터 행 이벤트 바인딩
function bindFilterRowEvents(idx) {
    const row = document.querySelector(`.filter-row[data-idx="${idx}"]`);
    if (!row) return;

    // 삭제 버튼
    row.querySelector('.remove-filter').onclick = function() {
        window.kanbanSettings.filters.splice(idx, 1);
        row.remove();
        // 인덱스 재정렬
        document.querySelectorAll('.filter-row').forEach((r, i) => r.setAttribute('data-idx', i));
    };

    // 속성 변경 시 값 옵션 업데이트
    row.querySelector('.filter-attr').addEventListener('change', function() {
        const attrName = this.value;
        const valueSelect = row.querySelector('.filter-value');
        const attributes = window.attributes || [];
        const attr = attributes.find(a => a.name === attrName);
        
        if (attr) {
            valueSelect.innerHTML = `
                <option value="">값을 선택하세요</option>
                ${attr.options.map(opt => `<option value="${opt.id}">${opt.name}</option>`).join('')}
            `;
        }
        
        // 설정 업데이트
        window.kanbanSettings.filters[idx].attribute = attrName;
        window.kanbanSettings.filters[idx].value = '';
    });

    // 연산자 변경
    row.querySelector('.filter-operator').addEventListener('change', function() {
        window.kanbanSettings.filters[idx].operator = this.value;
    });

    // 값 변경
    row.querySelector('.filter-value').addEventListener('change', function() {
        window.kanbanSettings.filters[idx].value = this.value;
    });
}

// 커스텀 규칙 이벤트 바인딩
function bindCustomRuleEvents() {
    // 커스텀 규칙 추가 버튼
    document.getElementById('addCustomRuleBtn').onclick = function() {
        window.kanbanSettings.custom_rules = window.kanbanSettings.custom_rules || [];
        window.kanbanSettings.custom_rules.push({
            name: '',
            logic: 'AND',
            conditions: []
        });
        
        const idx = window.kanbanSettings.custom_rules.length - 1;
        const ruleRow = createCustomRuleRow(idx);
        document.getElementById('customRulesList').insertAdjacentHTML('beforeend', ruleRow);
        bindCustomRuleRowEvents(idx);
    };

    // 기존 커스텀 규칙 행들에 이벤트 바인딩
    document.querySelectorAll('.custom-rule-row').forEach((row, idx) => {
        bindCustomRuleRowEvents(idx);
    });
}

// 커스텀 규칙 행 이벤트 바인딩
function bindCustomRuleRowEvents(idx) {
    const row = document.querySelector(`.custom-rule-row[data-idx="${idx}"]`);
    if (!row) return;

    // 삭제 버튼
    row.querySelector('.remove-custom-rule').onclick = function() {
        window.kanbanSettings.custom_rules.splice(idx, 1);
        row.remove();
        // 인덱스 재정렬
        document.querySelectorAll('.custom-rule-row').forEach((r, i) => r.setAttribute('data-idx', i));
    };

    // 규칙 이름 변경
    row.querySelector('.custom-rule-name').addEventListener('input', function() {
        window.kanbanSettings.custom_rules[idx].name = this.value;
    });

    // 논리 연산자 변경
    row.querySelector('.custom-rule-logic').addEventListener('change', function() {
        window.kanbanSettings.custom_rules[idx].logic = this.value;
    });

    // 조건 추가 버튼
    row.querySelector('.add-custom-condition').onclick = function() {
        const rule = window.kanbanSettings.custom_rules[idx];
        rule.conditions = rule.conditions || [];
        rule.conditions.push({
            attribute: '',
            operator: 'equals',
            value: ''
        });
        
        const condIdx = rule.conditions.length - 1;
        const conditionRow = createCustomConditionRow(condIdx);
        row.querySelector('.custom-rule-conditions').insertAdjacentHTML('beforeend', conditionRow);
        bindCustomConditionEvents(idx, condIdx);
    };

    // 기존 조건들에 이벤트 바인딩
    row.querySelectorAll('.custom-condition-row').forEach((condRow, condIdx) => {
        bindCustomConditionEvents(idx, condIdx);
    });
}

// 커스텀 조건 이벤트 바인딩
function bindCustomConditionEvents(ruleIdx, condIdx) {
    const ruleRow = document.querySelector(`.custom-rule-row[data-idx="${ruleIdx}"]`);
    if (!ruleRow) return;
    
    const condRow = ruleRow.querySelector(`.custom-condition-row[data-cond-idx="${condIdx}"]`);
    if (!condRow) return;

    // 삭제 버튼
    condRow.querySelector('.remove-custom-condition').onclick = function() {
        window.kanbanSettings.custom_rules[ruleIdx].conditions.splice(condIdx, 1);
        condRow.remove();
        // 인덱스 재정렬
        ruleRow.querySelectorAll('.custom-condition-row').forEach((r, i) => r.setAttribute('data-cond-idx', i));
    };

    // 속성 변경
    condRow.querySelector('.custom-condition-attr').addEventListener('change', function() {
        const attrName = this.value;
        const valueSelect = condRow.querySelector('.custom-condition-value');
        const attributes = window.attributes || [];
        const attr = attributes.find(a => a.name === attrName);
        
        if (attr) {
            valueSelect.innerHTML = `
                <option value="">값을 선택하세요</option>
                ${attr.options.map(opt => `<option value="${opt.id}">${opt.name}</option>`).join('')}
            `;
        }
        
        // 설정 업데이트
        window.kanbanSettings.custom_rules[ruleIdx].conditions[condIdx].attribute = attrName;
        window.kanbanSettings.custom_rules[ruleIdx].conditions[condIdx].value = '';
    });

    // 연산자 변경
    condRow.querySelector('.custom-condition-operator').addEventListener('change', function() {
        window.kanbanSettings.custom_rules[ruleIdx].conditions[condIdx].operator = this.value;
    });

    // 값 변경
    condRow.querySelector('.custom-condition-value').addEventListener('change', function() {
        window.kanbanSettings.custom_rules[ruleIdx].conditions[condIdx].value = this.value;
    });
}

// 필터 행 HTML 생성
function createFilterRow(idx) {
    const attributes = window.attributes || [];
    const attrOptions = attributes.map(attr => 
        `<option value="${attr.name}">${attr.name}</option>`
    ).join('');
    
    return `
        <div class="filter-row" data-idx="${idx}" style="display:flex;align-items:center;margin-bottom:8px;gap:8px;padding:12px;border:1px solid #e0e0e0;border-radius:6px;">
            <select class="filter-attr" data-idx="${idx}" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                <option value="">속성을 선택하세요</option>
                ${attrOptions}
            </select>
            <select class="filter-operator" data-idx="${idx}" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                <option value="equals">같음</option>
                <option value="not_equals">다름</option>
                <option value="contains">포함</option>
                <option value="not_contains">포함안함</option>
            </select>
            <select class="filter-value" data-idx="${idx}" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                <option value="">속성을 먼저 선택하세요</option>
            </select>
            <button type="button" class="remove-filter" data-idx="${idx}" style="color:#fff;background:#dc3545;border:none;border-radius:3px;padding:4px 8px;cursor:pointer;">삭제</button>
        </div>
    `;
}

// 커스텀 규칙 행 HTML 생성
function createCustomRuleRow(idx) {
    const attributes = window.attributes || [];
    const attrOptions = attributes.map(attr => 
        `<option value="${attr.name}">${attr.name}</option>`
    ).join('');
    
    return `
        <div class="custom-rule-row" data-idx="${idx}" style="margin-bottom:12px;padding:12px;border:1px solid #e0e0e0;border-radius:6px;">
            <div style="display:flex;align-items:center;margin-bottom:8px;gap:8px;">
                <input type="text" class="custom-rule-name" value="" placeholder="규칙 이름" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                <select class="custom-rule-logic" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                    <option value="AND">AND</option>
                    <option value="OR">OR</option>
                </select>
                <button type="button" class="remove-custom-rule" data-idx="${idx}" style="color:#fff;background:#dc3545;border:none;border-radius:3px;padding:4px 8px;cursor:pointer;">삭제</button>
            </div>
            <div class="custom-rule-conditions" style="margin-left:20px;">
            </div>
            <button type="button" class="add-custom-condition" data-rule-idx="${idx}" style="margin-top:6px;padding:4px 8px;background:#17a2b8;color:#fff;border:none;border-radius:3px;cursor:pointer;font-size:12px;">+ 조건 추가</button>
        </div>
    `;
}

// 커스텀 조건 행 HTML 생성
function createCustomConditionRow(condIdx) {
    const attributes = window.attributes || [];
    const attrOptions = attributes.map(attr => 
        `<option value="${attr.name}">${attr.name}</option>`
    ).join('');
    
    return `
        <div class="custom-condition-row" data-cond-idx="${condIdx}" style="display:flex;align-items:center;margin-bottom:6px;gap:8px;">
            <select class="custom-condition-attr" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                <option value="">속성을 선택하세요</option>
                ${attrOptions}
            </select>
            <select class="custom-condition-operator" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                <option value="equals">같음</option>
                <option value="not_equals">다름</option>
                <option value="contains">포함</option>
                <option value="not_contains">포함안함</option>
            </select>
            <select class="custom-condition-value" style="width:120px;padding:4px;border:1px solid #ddd;border-radius:4px;">
                <option value="">속성을 먼저 선택하세요</option>
            </select>
            <button type="button" class="remove-custom-condition" style="color:#fff;background:#ffc107;border:none;border-radius:3px;padding:2px 6px;cursor:pointer;">삭제</button>
        </div>
    `;
}

function closeKanbanSettingsModal() {
    const modal = document.getElementById('kanbanSettingsModal');
    if (modal) {
        modal.remove();
    }
}

function saveKanbanSettings() {
    const modal = document.getElementById('kanbanSettingsModal');
    if (!modal) return;

    // 메인 속성
    const mainAttr = modal.querySelector('#mainAttrSelect').value;
    if (!mainAttr) {
        alert('메인 칸반보드 속성을 선택하세요.');
        return;
    }
    
    // 필터들
    const filters = [];
    modal.querySelectorAll('.filter-row').forEach(row => {
        const attr = row.querySelector('.filter-attr').value;
        const operator = row.querySelector('.filter-operator').value;
        const value = row.querySelector('.filter-value').value;
        
        if (attr && value) {
            filters.push({ attribute: attr, operator: operator, value: value });
        }
    });

    // 커스텀 규칙들
    const custom_rules = [];
    modal.querySelectorAll('.custom-rule-row').forEach(row => {
        const name = row.querySelector('.custom-rule-name').value;
        const logic = row.querySelector('.custom-rule-logic').value;
        const conditions = [];
        
        row.querySelectorAll('.custom-condition-row').forEach(condRow => {
            const attr = condRow.querySelector('.custom-condition-attr').value;
            const operator = condRow.querySelector('.custom-condition-operator').value;
            const value = condRow.querySelector('.custom-condition-value').value;
            
            if (attr && value) {
                conditions.push({ attribute: attr, operator: operator, value: value });
            }
        });
        
        if (name && conditions.length > 0) {
            custom_rules.push({ name: name, logic: logic, conditions: conditions });
        }
    });

    const settings = { main_attr: mainAttr, filters: filters, custom_rules: custom_rules };

    fetch('/sales/save_kanban_settings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ settings })
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            closeKanbanSettingsModal();
            alert('칸반보드 설정이 저장되었습니다.');
            
            // 칸반보드 새로고침
            if (typeof refreshKanban === 'function') {
                refreshKanban();
            }
        } else {
            alert('설정 저장에 실패했습니다: ' + (data.error || ''));
        }
    }).catch(error => {
        console.error('설정 저장 오류:', error);
        alert('설정 저장 중 오류가 발생했습니다.');
    });
} 