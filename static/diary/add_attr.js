// 속성 추가 모달 관련 함수들
function openAddAttributeModal() {
  console.log('openAddAttributeModal, 리스트')
  document.getElementById('addAttributeModal').style.display = 'flex';
  document.getElementById('attributeName').value = '';
  document.getElementById('attributeType').value = 'text';
}

function closeAddAttributeModal() {
  console.log('closeAddAttributeModal, 리스트')
  document.getElementById('addAttributeModal').style.display = 'none';
}

function saveNewAttribute() {
  console.log('saveNewAttribute, 리스트')
  const name = document.getElementById('attributeName').value.trim();
  const type = document.getElementById('attributeType').value;
  
  if (!name) {
      alert('속성명을 입력해주세요.');
      return;
  }
  
  // 서버에 새 속성 추가 요청
  fetch('/sales/add_attribute/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'name=' + encodeURIComponent(name) + '&type=' + encodeURIComponent(type)
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          // 성공 시 테이블만 비동기 갱신, 속성관리 모달 리스트도 갱신
          refreshTable();
          closeAddAttributeModal();
          
          // 칸반보드 필터 업데이트
          refreshKanbanFilter();
          
          // 캘린더 설정 업데이트
          refreshCalendarSettings();

      } else {
          alert('속성 추가 실패: ' + (data.error || '알 수 없는 오류'));
      }
  })
  .catch(error => {
      console.error('속성 추가 중 오류:', error);
      alert('속성 추가 중 오류가 발생했습니다.');
  });
}

// 모달 외부 클릭 시 닫기
document.getElementById('addAttributeModal').onclick = function(e) {
  if (e.target === this) {
      closeAddAttributeModal();
  }
};
