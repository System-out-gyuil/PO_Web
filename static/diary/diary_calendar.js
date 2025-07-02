// 캘린더 상세 모달 함수
function showCalendarDetailModal(rowData) {
  // 모달 HTML 생성
  const modalHTML = `
      <div id="calendarDetailModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000;">
          <div style="background:white;border-radius:8px;padding:20px;width:400px;max-width:90%;max-height:80%;overflow-y:auto;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                  <h3 style="margin:0;color:#333;">일정 상세 정보</h3>
                  <button onclick="closeCalendarDetailModal()" style="background:none;border:none;font-size:20px;cursor:pointer;">&times;</button>
              </div>
              <div id="calendarDetailContent">
                  ${Object.keys(rowData).map(key => {
                      let value = rowData[key] || '(정보 없음)';
                      
                      // 날짜 필드 포맷팅
                      if (key.includes('일정') || key.includes('날짜') || key === '미팅') {
                          if (value && value !== '(정보 없음)') {
                              try {
                                  const date = new Date(value);
                                  if (!isNaN(date.getTime())) {
                                      value = date.toLocaleDateString('ko-KR');
                                  }
                              } catch (e) {
                                  // 날짜 파싱 실패 시 원본 값 유지
                              }
                          }
                      }
                      
                      return `
                          <div style="margin-bottom:12px;">
                              <strong style="color:#666;display:inline-block;width:100px;">${key}:</strong>
                              <span style="color:#333;">${value}</span>
                          </div>
                      `;
                  }).join('')}
              </div>
          </div>
      </div>
  `;
  
  // 기존 모달 제거 후 새 모달 추가
  const existingModal = document.getElementById('calendarDetailModal');
  if (existingModal) {
      existingModal.remove();
  }
  
  document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeCalendarDetailModal() {
  const modal = document.getElementById('calendarDetailModal');
  if (modal) {
      modal.remove();
  }
}

// 캘린더 모달 외부 클릭 시 닫기
document.addEventListener('click', function(e) {
  if (e.target && e.target.id === 'calendarDetailModal') {
      closeCalendarDetailModal();
  }
});