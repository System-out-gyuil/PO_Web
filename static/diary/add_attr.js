// 속성 추가 모달 관련 함수들
function openAddAttributeModal() {
  console.log('openAddAttributeModal, 리스트')
  document.getElementById('addAttributeModal').style.display = 'flex';
  document.getElementById('attributeName').value = '';
  document.getElementById('attributeType').value = 'text';
  
  // 중복 체크 상태 초기화
  clearDuplicateCheck();
  
  // 속성명 입력 필드에 실시간 중복 체크 이벤트 추가 (한 번만)
  const nameInput = document.getElementById('attributeName');
  if (!nameInput.hasAttribute('data-duplicate-check-added')) {
    nameInput.addEventListener('input', debounce(checkDuplicateOnInput, 500));
    nameInput.setAttribute('data-duplicate-check-added', 'true');
  }
}

function closeAddAttributeModal() {
  console.log('closeAddAttributeModal, 리스트')
  document.getElementById('addAttributeModal').style.display = 'none';
  
  // 중복 체크 상태 초기화
  clearDuplicateCheck();
}

// 디바운스 함수 (연속 입력 방지)
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// 입력 시 실시간 중복 체크
async function checkDuplicateOnInput() {
  const nameInput = document.getElementById('attributeName');
  const name = nameInput.value.trim();
  
  if (!name) {
    clearDuplicateCheck();
    return;
  }
  
  const isDuplicate = await checkAttributeNameDuplicate(name);
  showDuplicateCheckResult(isDuplicate);
}

// 중복 체크 결과 표시
function showDuplicateCheckResult(isDuplicate) {
  const nameInput = document.getElementById('attributeName');
  const duplicateMessage = document.getElementById('duplicateMessage') || createDuplicateMessageElement();
  const saveButton = document.querySelector('.save-attribute-btn');
  
  // 기존 클래스 제거
  nameInput.classList.remove('duplicate', 'available');
  duplicateMessage.classList.remove('duplicate', 'available');
  
  if (isDuplicate) {
    nameInput.classList.add('duplicate');
    duplicateMessage.classList.add('duplicate');
    duplicateMessage.textContent = '이미 존재하는 속성명입니다.';
    duplicateMessage.style.display = 'block';
    
    // 저장 버튼 비활성화
    if (saveButton) {
      saveButton.disabled = true;
      saveButton.title = '중복된 속성명입니다.';
    }
  } else {
    nameInput.classList.add('available');
    duplicateMessage.classList.add('available');
    duplicateMessage.textContent = '사용 가능한 속성명입니다.';
    duplicateMessage.style.display = 'block';
    
    // 저장 버튼 활성화
    if (saveButton) {
      saveButton.disabled = false;
      saveButton.title = '속성 추가';
    }
  }
}

// 중복 체크 메시지 요소 생성
function createDuplicateMessageElement() {
  const nameInput = document.getElementById('attributeName');
  const duplicateMessage = document.createElement('div');
  duplicateMessage.id = 'duplicateMessage';
  duplicateMessage.style.fontSize = '12px';
  duplicateMessage.style.marginTop = '5px';
  duplicateMessage.style.display = 'none';
  
  // 속성명 입력 필드 다음에 메시지 삽입
  nameInput.parentNode.insertBefore(duplicateMessage, nameInput.nextSibling);
  
  return duplicateMessage;
}

// 중복 체크 상태 초기화
function clearDuplicateCheck() {
  const nameInput = document.getElementById('attributeName');
  const duplicateMessage = document.getElementById('duplicateMessage');
  const saveButton = document.querySelector('.save-attribute-btn');
  
  if (nameInput) {
    nameInput.classList.remove('duplicate', 'available');
  }
  
  if (duplicateMessage) {
    duplicateMessage.classList.remove('duplicate', 'available');
    duplicateMessage.style.display = 'none';
  }
  
  if (saveButton) {
    saveButton.disabled = false;
    saveButton.title = '속성 추가';
  }
}

// 사용자의 기존 속성 목록을 가져오는 함수
async function getUserAttributes() {
  try {
    const response = await fetch('/sales/get_user_attributes/');
    const data = await response.json();
    if (data.success) {
      return data.attributes.map(attr => attr.name);
    } else {
      console.error('속성 목록 가져오기 실패:', data.error);
      return [];
    }
  } catch (error) {
    console.error('속성 목록 가져오기 오류:', error);
    return [];
  }
}

// 속성명 중복 체크 함수
async function checkAttributeNameDuplicate(name) {
  const existingAttributes = await getUserAttributes();
  return existingAttributes.includes(name);
}

function saveNewAttribute() {
  console.log('saveNewAttribute, 리스트')
  const name = document.getElementById('attributeName').value.trim();
  const type = document.getElementById('attributeType').value;
  
  if (!name) {
      alert('속성명을 입력해주세요.');
      return;
  }
  
  // 중복 체크 후 속성 추가
  checkAttributeNameDuplicate(name).then(isDuplicate => {
    if (isDuplicate) {
      alert('이미 존재하는 속성명입니다. 다른 이름을 사용해주세요.');
      return;
    }
    
    // 중복이 아닌 경우 서버에 새 속성 추가 요청
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
  });
}

// 모달 외부 클릭 시 닫기
document.getElementById('addAttributeModal').onclick = function(e) {
  if (e.target === this) {
      closeAddAttributeModal();
  }
};