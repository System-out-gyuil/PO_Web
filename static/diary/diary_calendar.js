// 캘린더 설정 변수
let calendarSettings = {
    date_field: 'F/U 일정',
    content_fields: ['회사명', '미팅', '영업진행']
};

// 캘린더 설정 모달 함수
function showCalendarSettingsModal() {
    // datetime 속성들과 모든 속성들을 가져와서 모달 생성
    Promise.all([
        fetch('/600/get_datetime_attributes/').then(r => r.json()),
        fetch('/600/get_user_attributes/').then(r => r.json()),
        fetch('/600/get_calendar_settings/').then(r => r.json())
    ]).then(([datetimeData, attributesData, settingsData]) => {
        if (!datetimeData.success || !attributesData.success || !settingsData.success) {
            alert('설정을 불러오는데 실패했습니다.');
            return;
        }

        // 현재 설정 업데이트
        calendarSettings = settingsData.settings;

        // datetime 속성들로 드롭다운 생성
        const dateFieldOptions = datetimeData.attributes.map(attr => 
            `<option value="${attr.name}" ${attr.name === calendarSettings.date_field ? 'selected' : ''}>${attr.name}</option>`
        ).join('');

        // 모든 속성들로 체크박스 생성 (type 필터링)
        const allowedTypes = ['text', 'datetime', 'region', 'region detail', 'number'];
        const filteredAttributes = attributesData.attributes.filter(attr =>
            allowedTypes.includes(attr.type) && attr.name !== '회사명'
        );

        // 스타일 추가 (최초 1회만)
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
            `;
            document.head.appendChild(style);
        }

        // 체크박스 + 이름, 체크시 배경색
        const contentFieldOptions = filteredAttributes.map(attr => {
            const checked = calendarSettings.content_fields.includes(attr.name);
            return `
                <div class="calendar-setting-row${checked ? ' checked-row' : ''}" data-attr="${attr.name}">
                    <input type="checkbox" class="calendar-setting-checkbox" id="content_${attr.name}" value="${attr.name}" ${checked ? 'checked' : ''} style="margin:0;">
                    <label for="content_${attr.name}">${attr.name}</label>
                </div>
            `;
        }).join('');

        // 모달 삽입 후, 체크박스 이벤트로 배경색 토글
        setTimeout(() => {
            document.querySelectorAll('.calendar-setting-row input[type="checkbox"]').forEach(cb => {
                cb.addEventListener('change', function() {
                    const rowDiv = this.closest('.calendar-setting-row');
                    if (this.checked) {
                        rowDiv.classList.add('checked-row');
                    } else {
                        rowDiv.classList.remove('checked-row');
                    }
                });
            });
        }, 10);

        const modalHTML = `
            <div id="calendarSettingsModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000;">
                <div style="background:white;border-radius:8px;padding:20px;width:500px;max-width:90%;max-height:80%;overflow-y:auto;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <h3 style="margin:0;color:#333;">캘린더 설정</h3>
                        <button onclick="closeCalendarSettingsModal()" style="background:none;border:none;font-size:20px;cursor:pointer;">&times;</button>
                    </div>
                    
                    <div style="margin-bottom:20px;">
                        <label style="display:block;margin-bottom:8px;font-weight:bold;color:#333;">카드 생성 기준 날짜 필드:</label>
                        <select id="dateFieldSelect" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                            ${dateFieldOptions}
                        </select>
                    </div>
                    
                    <div style="margin-bottom:20px;">
                        <label style="display:block;margin-bottom:8px;font-weight:bold;color:#333;">카드에 표시할 내용:</label>
                        <div style="max-height:200px;overflow-y:auto;border:1px solid #ddd;border-radius:4px;padding:10px;">
                            ${contentFieldOptions}
                        </div>
                    </div>
                    
                    <div style="display:flex;justify-content:flex-end;gap:10px;">
                        <button onclick="closeCalendarSettingsModal()" style="padding:8px 16px;border:1px solid #ddd;background:#f8f9fa;border-radius:4px;cursor:pointer;">취소</button>
                        <button onclick="saveCalendarSettings()" style="padding:8px 16px;border:none;background:#007bff;color:white;border-radius:4px;cursor:pointer;">저장</button>
                    </div>
                </div>
            </div>
        `;

        // 기존 모달 제거 후 새 모달 추가
        const existingModal = document.getElementById('calendarSettingsModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
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

function saveCalendarSettings() {
    // 선택된 값들 가져오기
    const dateField = document.getElementById('dateFieldSelect').value;
    let contentFields = Array.from(document.querySelectorAll('#calendarSettingsModal input[type="checkbox"]:checked'))
        .map(cb => cb.value);
    // '회사명'을 항상 맨 앞에 추가
    if (!contentFields.includes('회사명')) {
        contentFields.unshift('회사명');
    }

    // 최소 하나의 내용 필드는 선택되어야 함
    if (contentFields.length === 0) {
        alert('카드에 표시할 내용을 최소 하나 선택해주세요.');
        return;
    }

    const newSettings = {
        date_field: dateField,
        content_fields: contentFields
    };

    // 설정 저장
    fetch('/600/save_calendar_settings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(newSettings)
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            // 설정 업데이트
            calendarSettings = newSettings;
            
            // 캘린더 새로고침
            if (window.calendar) {
                window.calendar.refetchEvents();
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

// CSRF 토큰 가져오기 함수
function getCsrfToken() {
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (token) return token;
    
    // Django의 기본 CSRF 토큰 쿠키에서 가져오기
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// 캘린더 초기화 함수 (설정을 반영한 버전)
function initializeCalendarWithSettings() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    // 설정에 따른 이벤트 URL 생성
    const eventUrl = `/600/calendar_events/?date_field=${encodeURIComponent(calendarSettings.date_field)}&${calendarSettings.content_fields.map(field => `content_fields=${encodeURIComponent(field)}`).join('&')}`;

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
        eventContent: function(arg) {
            const name = arg.event.title;
            const content = arg.event.extendedProps.content || {};
            const status = arg.event.extendedProps.status_name;
            const statusColor = arg.event.extendedProps.status_color || '#bbb';

            // 카드 필드 렌더링
            const fields = calendarSettings.content_fields
                .filter(field => field !== '회사명')
                .map((field, idx, arr) => {
                    const isLast = idx === arr.length - 1;
                    return `
                        <div style="
                            display:flex;
                            align-items:center;
                            font-size:0.97em;
                            padding:3px 0 3px 0;
                            ${!isLast ? 'border-bottom:1px solid #e5e7eb;' : ''}
                        ">
                            <span style="color:#888;min-width:70px;flex-shrink:0;">${field}</span>
                            <span style="margin-left:8px;color:#222;word-break:break-all;white-space:normal;display:inline-block;max-width:180px;text-align:left;">${content[field] || ''}</span>
                        </div>
                    `;
                }).join('');

            // 상태 표시
            let statusHtml = '';
            if (status) {
                statusHtml = `<span style="display:inline-block;background:${statusColor};color:#fff;padding:2px 8px;border-radius:6px;font-size:0.92em;margin-top:6px;">${status}</span>`;
            }

            // 카드 전체 스타일
            return {
                html: `
                    <div style="
                        width:100%;
                        box-sizing:border-box;
                        padding:10px 12px 8px 12px;
                        border-radius:12px;
                        background:#fff;
                        box-shadow:0 2px 8px 0 rgba(0,0,0,0.06);
                        border:1px solid #e5e7eb;
                        color:#222;
                    ">
                        <div style="font-weight:bold; font-size:1.08em; margin-bottom:6px;">${name}</div>
                        ${fields}
                        ${statusHtml}
                    </div>
                `
            };
        },
        eventClick: function(info) {
            // 이벤트 클릭 시 기존 상세보기 모달 표시
            const rowId = info.event.id;
            fetch(`/600/get_row_details/${rowId}/`)
                .then(r => r.json())
                .then(function(data) {
                    if (data.success) {
                        showDetailModal(data.row_data, data.row_id);
                    } else {
                        alert('상세정보 불러오기 실패: ' + (data.error || ''));
                    }
                });
        }
    });

    calendar.render();
    window.calendar = calendar;
}

// 페이지 로드 시 캘린더 설정 불러오기 및 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 캘린더 설정 불러오기
    fetch('/600/get_calendar_settings/')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                calendarSettings = data.settings;
            }
            // 캘린더 초기화
            initializeCalendarWithSettings();
        })
        .catch(error => {
            console.error('캘린더 설정 불러오기 오류:', error);
            // 기본 설정으로 캘린더 초기화
            initializeCalendarWithSettings();
        });
});

// 캘린더 모달 외부 클릭 시 닫기
document.addEventListener('click', function(e) {
  if (e.target && e.target.id === 'calendarSettingsModal') {
      closeCalendarSettingsModal();
  }
});