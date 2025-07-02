let dropdown = null;
let dropdownCloseHandler = null;

function closeDropdown() {
    console.log('closeDropdown 호출됨, dropdown:', dropdown);
    if (dropdown && dropdown.parentNode) {
        dropdown.parentNode.removeChild(dropdown);
        dropdown = null;
    }
    if (window.dropdown && window.dropdown.parentNode) {
        window.dropdown.parentNode.removeChild(window.dropdown);
        window.dropdown = null;
    }
    // 이벤트 리스너 정리
    if (dropdownCloseHandler) {
        document.removeEventListener('click', dropdownCloseHandler);
        document.removeEventListener('mousedown', dropdownCloseHandler);
        dropdownCloseHandler = null;
    }
}

// 숫자에 콤마 추가하는 함수
function formatNumberWithComma(value) {
    if (!value || value === '') return '';
    const numericValue = value.toString().replace(/[^0-9.-]/g, '');
    if (numericValue === '' || isNaN(numericValue)) return value;
    return parseInt(numericValue).toLocaleString();
}

// 콤마 제거하고 숫자 값 반환하는 함수
function removeCommaFromNumber(value) {
    if (!value || value === '') return '';
    return value.toString().replace(/[,]/g, '');
}

// 드롭다운 외부 클릭 이벤트 설정 함수
function setupDropdownCloseHandler(dropdownElement) {
    closeDropdown(); // 기존 드롭다운 먼저 닫기
    
    dropdownCloseHandler = function(e) {
        if (dropdownElement && !dropdownElement.contains(e.target)) {
            closeDropdown();
        }
    };
    
    // click과 mousedown 모두 처리
    setTimeout(() => {
        document.addEventListener('click', dropdownCloseHandler);
        document.addEventListener('mousedown', dropdownCloseHandler);
    }, 100);
}

function refreshKanban() {
    fetch('/').then(r=>r.text()).then(html=>{
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const newBoard = temp.querySelector('#boardView');
        if (newBoard) {
            document.getElementById('boardView').innerHTML = newBoard.innerHTML;
            bindKanbanSortable(); // 드래그 기능 복구
        }
    });
}

function hexToRgba(hex, alpha) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(x => x + x).join('');
  const r = parseInt(hex.substring(0,2), 16);
  const g = parseInt(hex.substring(2,4), 16);
  const b = parseInt(hex.substring(4,6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}


function updateEntryField(id, field, value) {
  fetch('/diary/update/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'id='+encodeURIComponent(id)+'&field='+encodeURIComponent(field)+'&value='+encodeURIComponent(value)
  })
  .then(r=>r.json())
  .then(function(data){
      if(!data.success) {
          alert('수정 실패: '+(data.error||''));
          return;
      }
      // 항상 최신 entry로 모달/테이블/보드 동기화
      return fetch('/diary/update/?id='+id);
  })
  .then(r => r ? r.json() : null)
  .then(function(data){
      if(data && data.success && data.entry) {
          showDetailModal(data.entry);
          updateTableRow(data.entry);
          // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
          if (window.kanbanAttribute && field === window.kanbanAttribute) {
              refreshKanban();
          }
          if(field === 'fu_date' && window.calendar) window.calendar.refetchEvents();
      }
  })
  .catch(function(err){
      alert('수정 실패: 네트워크 오류');
      console.error(err);
  });
}