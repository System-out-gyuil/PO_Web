// 모달창 CSS 스타일
const modalStyles = `
  <style>
    .docx-modal {
      position: fixed;
      z-index: 1000;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .docx-modal-content {
      background-color: #fefefe;
      margin: auto;
      padding: 0;
      border: 1px solid #888;
      width: 90%;
      max-width: 600px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .docx-modal-header {
      padding: 20px;
      border-bottom: 1px solid #ddd;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background-color: #f8f9fa;
      border-radius: 8px 8px 0 0;
    }
    
    .docx-modal-header h3 {
      margin: 0;
      color: #333;
      font-size: 18px;
    }
    
    .docx-modal-close {
      color: #aaa;
      font-size: 28px;
      font-weight: bold;
      cursor: pointer;
      line-height: 1;
    }
    
    .docx-modal-close:hover {
      color: #000;
    }
    
    .docx-modal-body {
      padding: 20px;
    }
    
    .form-group {
      margin-bottom: 20px;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
      color: #333;
    }
    
    .form-group input,
    .form-group textarea {
      width: 100%;
      padding: 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      box-sizing: border-box;
    }
    
    .form-group input:focus,
    .form-group textarea:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
    }
    
    .form-group textarea {
      resize: vertical;
      min-height: 100px;
      height: 350px;
    }
    
    .button-group {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
      margin-top: 30px;
    }
    
    .btn-recommend,
    .btn-generate {
      padding: 12px 24px;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .btn-recommend {
      background-color: #28a745;
      color: white;
    }
    
    .btn-recommend:hover:not(:disabled) {
      background-color: #218838;
    }
    
    .btn-generate {
      background-color: #007bff;
      color: white;
    }
    
    .btn-generate:hover:not(:disabled) {
      background-color: #0056b3;
    }
    
    .btn-recommend:disabled,
    .btn-generate:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    @media (max-width: 768px) {
      .docx-modal-content {
        width: 95%;
        margin: 20px;
      }
      
      .button-group {
        flex-direction: column;
      }
      
      .btn-recommend,
      .btn-generate {
        width: 100%;
      }
    }
  </style>
`;

// 페이지 로드 시 스타일 추가
if (!document.getElementById('docxModalStyles')) {
  const styleElement = document.createElement('div');
  styleElement.id = 'docxModalStyles';
  styleElement.innerHTML = modalStyles;
  document.head.appendChild(styleElement);
}

function openAutoDocx() {
  console.log("openAutoDocx 함수 호출됨");
  
  if (window.currentDetailRowId) {
    console.log('행 ID:', window.currentDetailRowId);
    
    // 모달창 HTML 생성
    const modalHTML = `
      <div id="docxModal" class="docx-modal" style="display: none;">
        <div class="docx-modal-content">
          <div class="docx-modal-header">
            <h3>사업계획서 생성</h3>
            <span class="docx-modal-close" onclick="closeDocxModal()">&times;</span>
          </div>
          <div class="docx-modal-body">
            <div class="form-group">
              <label for="serviceProduct">주 서비스·생산품목 *</label>
              <input type="text" id="serviceProduct" placeholder="예: 웹사이트 개발, 커피 제조 등" required>
            </div>
            <div class="form-group">
              <label for="businessOverview">사업 개요</label>
              <textarea id="businessOverview" rows="4" placeholder="AI 추천을 받으려면 '추천받기' 버튼을 클릭하세요" readonly></textarea>
            </div>
            <div class="button-group">
              <button type="button" onclick="getOpenAIRecommendation()" class="btn-recommend">추천받기</button>
              <button type="button" onclick="generateDocx()" class="btn-generate">DOCX 생성</button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // 모달창이 이미 존재하면 제거
    const existingModal = document.getElementById('docxModal');
    if (existingModal) {
      existingModal.remove();
    }
    
    // 모달창 추가
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // 모달창 표시
    const modal = document.getElementById('docxModal');
    modal.style.display = 'block';
    
    // 모달창 표시 후 입력 필드 확인
    setTimeout(() => {
      const serviceProductField = document.getElementById('serviceProduct');
      const businessOverviewField = document.getElementById('businessOverview');
      
      console.log('모달창 표시 후 필드 상태:');
      console.log('  - serviceProduct:', serviceProductField);
      console.log('  - businessOverview:', businessOverviewField);
      
      if (serviceProductField) {
        serviceProductField.focus();
        console.log('주 서비스·생산품목 필드에 포커스 설정됨');
      }
    }, 100);
    
    // 모달창 외부 클릭 시 닫기
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeDocxModal();
      }
    });
    
  } else {
    alert('현재 행 정보를 찾을 수 없습니다. 상세보기를 다시 열어주세요.');
  }
}

function closeDocxModal() {
  const modal = document.getElementById('docxModal');
  if (modal) {
    modal.remove();
  }
}

function getOpenAIRecommendation() {
  const serviceProduct = document.getElementById('serviceProduct').value.trim();
  
  console.log('입력된 값들:', { serviceProduct });
  
  if (!serviceProduct) {
    alert('주 서비스·생산품목을 입력해주세요.');
    return;
  }
  
  // 로딩 상태 표시
  const recommendBtn = document.querySelector('.btn-recommend');
  const originalText = recommendBtn.textContent;
  recommendBtn.textContent = '추천 중...';
  recommendBtn.disabled = true;
  
  const requestData = {
    row_id: window.currentDetailRowId,
    service_product: serviceProduct
  };
  
  console.log('전송할 데이터:', requestData);
  
  // OpenAI API 호출
  fetch(`/sales/auto_docx_recommend/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify(requestData)
  })
  .then(response => {
    console.log('응답 상태:', response.status);
    console.log('응답 헤더:', Object.fromEntries(response.headers.entries()));
    return response.json();
  })
  .then(data => {
    console.log('OpenAI 추천 응답:', data);
    
    if (data.success) {
      // 사업 개요 업데이트
      document.getElementById('businessOverview').value = data.business_overview || '추천 정보를 받을 수 없습니다.';
      
    } else {
      alert('추천을 받는 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'));
    }
  })
  .catch(error => {
    console.error('OpenAI 추천 요청 중 오류:', error);
    alert('추천을 받는 중 오류가 발생했습니다.');
  })
  .finally(() => {
    // 버튼 상태 복원
    recommendBtn.textContent = originalText;
    recommendBtn.disabled = false;
  });
}

function generateDocx() {
  const serviceProduct = document.getElementById('serviceProduct').value.trim();
  const businessOverview = document.getElementById('businessOverview').value.trim();
  
  if (!serviceProduct) {
    alert('주 서비스·생산품목을 입력해주세요.');
    return;
  }
  
  // 로딩 상태 표시
  const generateBtn = document.querySelector('.btn-generate');
  const originalText = generateBtn.textContent;
  generateBtn.textContent = '생성 중...';
  generateBtn.disabled = true;
  
  // DOCX 생성 API 호출
  fetch(`/sales/auto_docx/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({
      row_id: window.currentDetailRowId,
      service_product: serviceProduct,
      business_overview: businessOverview
    })
  })
  .then(response => {
    // 응답 타입 확인
    const contentType = response.headers.get('content-type');
    console.log('응답 타입:', contentType);
    console.log('응답 헤더:', Object.fromEntries(response.headers.entries()));
    
    if (contentType && contentType.includes('application/json')) {
      // JSON 응답인 경우 (에러 등)
      return response.json().then(data => {
        console.log('API 응답:', data);
        if (!data.success) {
          alert('오류: ' + (data.error || '알 수 없는 오류가 발생했습니다.'));
        }
      });
    } else {
      // 파일 응답인 경우
      console.log('파일 다운로드 시작...');
      
      // 파일명 추출
      const contentDisposition = response.headers.get('content-disposition');
      let filename = '사업계획서.docx';
      if (contentDisposition) {
        console.log('Content-Disposition:', contentDisposition);
        const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/);
        if (filenameMatch) {
          filename = decodeURIComponent(filenameMatch[1]);
          console.log('추출된 파일명:', filename);
        }
      }
      
      // 파일 다운로드 처리
      return response.blob().then(blob => {
        console.log('Blob 생성 완료:', blob.size, 'bytes');
        
        // 다운로드 링크 생성
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        
        console.log('다운로드 링크 생성:', url);
        
        // 링크 클릭하여 다운로드 시작
        document.body.appendChild(a);
        a.click();
        
        // 정리
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('파일 다운로드 완료:', filename);
        
        // 모달창 닫기
        closeDocxModal();
      });
    }
  })
  .catch(error => {
    console.error('DOCX 생성 중 오류:', error);
    alert('DOCX 생성 중 오류가 발생했습니다.');
  })
  .finally(() => {
    // 버튼 상태 복원
    generateBtn.textContent = originalText;
    generateBtn.disabled = false;
  });
}