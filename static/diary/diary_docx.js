function openAutoDocx() {
  console.log("openAutoDocx 함수 호출됨");
  
  if (window.currentDetailRowId) {
    console.log('행 ID:', window.currentDetailRowId);

    const rowId = window.currentDetailRowId;

    fetch(`/sales/auto_docx/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify({
        row_id: rowId
      })
    })
    .then(response => response.json())
    .then(data => {
      console.log('API 응답:', data);
    })
    .catch(error => {
      console.error('API 요청 중 오류 발생:', error);
    });

  } else {
    alert('현재 행 정보를 찾을 수 없습니다. 상세보기를 다시 열어주세요.');
  }

}