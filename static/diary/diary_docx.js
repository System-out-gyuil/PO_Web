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
      max-width: 900px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      overflow: hidden;
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
      padding: 0;
    }
    
    .tab-container {
      width: 100%;
    }
    
    .tab-buttons {
      display: flex;
      width: 100%;
      background-color: #f8f9fa;
      border-bottom: 1px solid #ddd;
    }
    
    .tab-button {
      flex: 1;
      padding: 15px 20px;
      border: none;
      background: none;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      color: #666;
      border-bottom: 3px solid transparent;
      transition: all 0.3s ease;
      text-align: center;
      position: relative;
    }
    
    .docx-modal .tab-button.active {
      color: #007bff;
      border-bottom-color: #007bff;
      background-color: white;
      z-index: 10;
      font-weight: bold;
    }
    
    .docx-modal .tab-button:hover:not(.active) {
      color: #007bff;
      background-color: #e9ecef;
    }
    
    .docx-modal .tab-content {
      display: none;
      padding: 20px;
      background-color: white;
      min-height: 400px;
      margin: 0 auto;
      width: 85%;
    }
    
    .docx-modal .tab-content.active {
      display: block;
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
    .form-group textarea,
    .form-group select {
      width: 100%;
      padding: 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      box-sizing: border-box;
    }
    
    .form-group input:focus,
    .form-group textarea:focus,
    .form-group select:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
    }
    
    .form-group textarea {
      resize: vertical;
      min-height: 100px;
      height: 200px;
    }
    
    .select-group {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    
    .select-group select {
      flex: 1;
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
    
    .innovation-result {
      background-color: #f8f9fa;
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 15px;
      margin-top: 15px;
    }
    
    .innovation-result h4 {
      margin: 0 0 10px 0;
      color: #333;
      font-size: 16px;
    }
    
    .innovation-result p {
      margin: 5px 0;
      color: #666;
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
      
      .select-group {
        flex-direction: column;
      }
      
      .tab-buttons {
        flex-direction: column;
      }
      
      .tab-button {
        border-radius: 0;
        border-bottom: 1px solid #ddd;
      }
      
      .tab-button.active {
        border-radius: 0;
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

// window 할당은 함수 정의 후에 수행됩니다

function openAutoDocx() {
  console.log("openAutoDocx 함수 호출됨");
  
  if (!window.currentDetailRowId) {
    alert('현재 행 정보를 찾을 수 없습니다. 상세보기를 다시 열어주세요.');
    return;
  }
  
  console.log('행 ID:', window.currentDetailRowId);
  
  // 기존 모달창 표시
  const modal = document.getElementById('docxModal');
  if (!modal) {
    console.error('docxModal을 찾을 수 없습니다.');
    alert('모달창을 찾을 수 없습니다. 페이지를 새로고침해주세요.');
    return;
  }
  
  // 모달 표시
  modal.style.display = 'flex';
  console.log('모달창 표시됨');
  
  // 입력 필드 초기화
  const serviceProductField = document.getElementById('serviceProduct');
  const businessOverviewField = document.getElementById('businessOverview');
  
  if (serviceProductField) {
    serviceProductField.value = '';
    serviceProductField.focus();
    console.log('주 서비스·생산품목 필드 초기화 및 포커스 설정');
  } else {
    console.error('serviceProduct 필드를 찾을 수 없습니다.');
  }
  
  if (businessOverviewField) {
    businessOverviewField.value = '';
    console.log('사업 개요 필드 초기화');
  } else {
    console.error('businessOverview 필드를 찾을 수 없습니다.');
  }
  
  // 혁신성장 탭 초기화
  const innovationTypeSelect = document.getElementById('innovationType');
  const innovationCategorySelect = document.getElementById('innovationCategory');
  const innovationResult = document.getElementById('innovationResult');
  
  if (innovationTypeSelect) {
    innovationTypeSelect.value = '';
    console.log('혁신성장 유형 선택 초기화');
  }
  
  if (innovationCategorySelect) {
    innovationCategorySelect.innerHTML = '<option value="">먼저 혁신성장 유형을 선택해주세요</option>';
    innovationCategorySelect.disabled = true;
    console.log('혁신성장 카테고리 선택 초기화');
  }
  
  if (innovationResult) {
    innovationResult.style.display = 'none';
    console.log('혁신성장 결과 숨김');
  }
  
  // 입력 필드들과 버튼을 다시 보이기
  const innovationTypeField = innovationTypeSelect ? innovationTypeSelect.closest('.form-group') : null;
  const innovationCategoryField = innovationCategorySelect ? innovationCategorySelect.closest('.form-group') : null;
  const buttonGroup = document.querySelector('#innovation-tab .button-group');
  
  if (innovationTypeField) innovationTypeField.style.display = 'block';
  if (innovationCategoryField) innovationCategoryField.style.display = 'block';
  if (buttonGroup) buttonGroup.style.display = 'flex';
  
  // 탭 초기화 (신용취약 탭 활성화) - HTML에 직접 정의된 함수 사용
  console.log('신용취약 탭으로 초기화 시작');
  if (typeof switchTabDirect === 'function') {
    switchTabDirect('credit');
  } else {
    console.error('switchTabDirect 함수를 찾을 수 없습니다.');
  }
  
  console.log('openAutoDocx 함수 완료');
}

function switchTab(tabName) {
  console.log('=== switchTab 함수 시작 ===');
  console.log('탭 전환 요청:', tabName);
  
  // 모든 탭 버튼 비활성화
  const tabButtons = document.querySelectorAll('.tab-button');
  console.log('찾은 탭 버튼 개수:', tabButtons.length);
  
  tabButtons.forEach(btn => {
    btn.classList.remove('active');
    console.log('버튼 active 제거:', btn.textContent);
  });
  
  // 모든 탭 콘텐츠 숨기기
  const tabContents = document.querySelectorAll('.tab-content');
  console.log('찾은 탭 콘텐츠 개수:', tabContents.length);
  
  tabContents.forEach(content => {
    content.classList.remove('active');
    content.style.display = 'none';
    console.log('콘텐츠 숨김:', content.id);
  });
  
  // 선택된 탭 활성화
  if (tabName === 'credit') {
    const creditButton = document.querySelector('.tab-button[data-tab="credit"]');
    const creditTab = document.getElementById('credit-tab');
    
    console.log('신용취약 탭 요소들:', { creditButton, creditTab });
    
    if (creditButton && creditTab) {
      creditButton.classList.add('active');
      creditTab.classList.add('active');
      creditTab.style.display = 'block';
      console.log('신용취약 탭 활성화됨');
    } else {
      console.error('신용취약 탭 요소를 찾을 수 없습니다');
    }
  } else if (tabName === 'innovation') {
    const innovationButton = document.querySelector('.tab-button[data-tab="innovation"]');
    const innovationTab = document.getElementById('innovation-tab');
    
    console.log('혁신성장 탭 요소들:', { innovationButton, innovationTab });
    
    if (innovationButton && innovationTab) {
      innovationButton.classList.add('active');
      innovationTab.classList.add('active');
      innovationTab.style.display = 'block';
      console.log('혁신성장 탭 활성화됨');
    } else {
      console.error('혁신성장 탭 요소를 찾을 수 없습니다');
    }
  }
  
  console.log('=== switchTab 함수 완료 ===');
  
  // 디버깅을 위한 최종 상태 확인
  setTimeout(() => {
    const activeTab = document.querySelector('.tab-content.active');
    const activeButton = document.querySelector('.tab-button.active');
    console.log('최종 상태 확인:');
    console.log('  - 활성 탭:', activeTab ? activeTab.id : '없음');
    console.log('  - 활성 버튼:', activeButton ? activeButton.textContent : '없음');
    
    if (activeTab) {
      console.log('  - 활성 탭 display:', activeTab.style.display);
    }
  }, 100);
}

// window 할당은 함수 정의 후에 수행됩니다

function updateInnovationCategories() {
  const modal = document.getElementById('docxModal');
  if (!modal) {
    console.error('모달을 찾을 수 없습니다.');
    return;
  }
  
  const innovationType = modal.querySelector('#innovationType').value;
  const categorySelect = modal.querySelector('#innovationCategory');
  
  console.log('updateInnovationCategories 호출됨:', innovationType);
  
  // 기존 옵션 제거
  categorySelect.innerHTML = '';
  
  if (innovationType === '혁신형') {
    const options = [
      '수출 소상공인',
      '2년 연속 매출 10%이상 신장',
      '스마트 공장 도입',
      '강한 소상공인, 로컬 크리에이터',
      '소상공인 졸업후보기업'
    ];
    
    options.forEach((option, index) => {
      const optionElement = document.createElement('option');
      optionElement.value = option;
      optionElement.textContent = `${index + 1}. ${option}`;
      categorySelect.appendChild(optionElement);
    });
  } else if (innovationType === '일반형') {
    const options = [
      '스마트 기술',
      '백년소공인, 백년가게',
      '사회적경제기업',
      '신사업 창업 사관학교 수료생'
    ];
    
    options.forEach((option, index) => {
      const optionElement = document.createElement('option');
      optionElement.value = option;
      optionElement.textContent = `${index + 1}. ${option}`;
      categorySelect.appendChild(optionElement);
    });
  }
  
  // 카테고리 선택 활성화
  categorySelect.disabled = false;
  console.log('카테고리 업데이트 완료');
}

function closeDocxModal() {
  console.log('closeDocxModal 함수 호출됨');
  
  const modal = document.getElementById('docxModal');
  if (modal) {
    modal.style.display = 'none';
    console.log('모달창 닫힘');
  } else {
    console.error('docxModal을 찾을 수 없습니다.');
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
      
      // 기업 정보가 있으면 표시
      if (data.company_info) {
        displayCreditRecommendationResult(data);
      }
      
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
        window.closeDocxModal();
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

function getInnovationRecommendation() {
  const modal = document.getElementById('docxModal');
  if (!modal) {
    console.error('모달을 찾을 수 없습니다.');
    return;
  }
  
  const innovationType = modal.querySelector('#innovationType').value;
  const innovationCategory = modal.querySelector('#innovationCategory').value;
  
  if (!innovationType || !innovationCategory) {
    alert('혁신성장 유형과 세부 카테고리를 모두 선택해주세요.');
    return;
  }
  
  // 로딩 상태 표시
  const recommendBtn = modal.querySelector('#innovationRecommendBtn');
  const originalText = recommendBtn.textContent;
  recommendBtn.textContent = '추천 중...';
  recommendBtn.disabled = true;
  
  const requestData = {
    row_id: window.currentDetailRowId,
    innovation_type: innovationType,
    innovation_category: innovationCategory
  };
  
  console.log('혁신성장 추천 요청 데이터:', requestData);
  
  // 혁신성장 추천 API 호출
  fetch(`/sales/auto_docx_innovation_recommend/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify(requestData)
  })
  .then(response => {
    console.log('응답 상태:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('혁신성장 추천 응답:', data);
    
    if (data.success) {
      // 결과 표시
      displayInnovationRecommendationResult(data);
    } else {
      alert('혁신성장 추천을 받는 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'));
    }
  })
  .catch(error => {
    console.error('혁신성장 추천 요청 중 오류:', error);
    alert('혁신성장 추천을 받는 중 오류가 발생했습니다.');
  })
  .finally(() => {
    // 버튼 상태 복원
    recommendBtn.textContent = originalText;
    recommendBtn.disabled = false;
  });
}

function displayCreditRecommendationResult(data) {
  const modal = document.getElementById('docxModal');
  if (!modal) {
    console.error('모달을 찾을 수 없습니다.');
    return;
  }
  
  // 신용취약 탭에서 결과를 표시할 영역 생성 또는 찾기
  let resultDiv = modal.querySelector('#creditResult');
  if (!resultDiv) {
    // 결과를 표시할 div가 없으면 생성
    const creditTab = modal.querySelector('#credit-tab');
    if (creditTab) {
      resultDiv = document.createElement('div');
      resultDiv.id = 'creditResult';
      resultDiv.style.cssText = `
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 15px;
        margin-top: 15px;
        display: none;
      `;
      creditTab.appendChild(resultDiv);
    }
  }
  
  if (!data || !data.company_info) {
    if (resultDiv) {
      resultDiv.innerHTML = '<h4>오류</h4><p>추천 정보를 가져올 수 없습니다.</p>';
      resultDiv.style.display = 'block';
    }
    return;
  }
  
  const companyInfo = data.company_info;
  const businessOverview = data.business_overview || '추천 정보가 없습니다.';
  
  const resultHTML = `
    <div style="max-height: 500px; overflow-y: auto; padding-right: 10px;">
      <h4>AI 추천 결과</h4>
      <div style="margin-bottom: 20px;">
        <p><strong>신용취약 소상공인 지원사업</strong></p>
      </div>
      
      <h5>기업 기본 정보</h5>
      <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 15px;">
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 10px; font-size: 14px;">
          <div><strong>업체명:</strong> ${companyInfo.업체명 || '정보 없음'}</div>
          <div><strong>대표자명:</strong> ${companyInfo.대표자명 || '정보 없음'}</div>
          <div><strong>설립일자:</strong> ${companyInfo.설립일자 || '정보 없음'}</div>
          <div><strong>법인번호:</strong> ${companyInfo.법인번호 || '정보 없음'}</div>
          <div><strong>주민번호:</strong> ${companyInfo.주민번호 || '정보 없음'}</div>
          <div><strong>사업자번호:</strong> ${companyInfo.사업자번호 || '정보 없음'}</div>
          <div><strong>본사주소:</strong> ${companyInfo.본사주소 || '정보 없음'}</div>
          <div><strong>전화번호:</strong> ${companyInfo.전화번호 || '정보 없음'}</div>
          <div><strong>이메일:</strong> ${companyInfo.email || '정보 없음'}</div>
          <div><strong>팩스번호:</strong> ${companyInfo.팩스번호 || '정보 없음'}</div>
        </div>
        <div style="margin-top: 15px;">
          <strong>사업내용:</strong><br>
          <span style="color: #666;">${companyInfo.사업내용 || '정보 없음'}</span>
        </div>
      </div>
      
      <h5>AI 추천 사업 개요</h5>
      <div style="background-color: #e8f4fd; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; margin-bottom: 20px;">
        <p style="margin: 0; line-height: 1.6; color: #333;">${businessOverview}</p>
      </div>
    </div>
  `;
  
  if (resultDiv) {
    resultDiv.innerHTML = resultHTML;
    resultDiv.style.display = 'block';
    console.log('신용취약 추천 결과 표시됨');
  }
}

function displayInnovationRecommendationResult(data) {
  const modal = document.getElementById('docxModal');
  if (!modal) {
    console.error('모달을 찾을 수 없습니다.');
    return;
  }
  
  const resultDiv = modal.querySelector('#innovationResult');
  
  if (!data || !data.company_info) {
    resultDiv.innerHTML = '<h4>오류</h4><p>추천 정보를 가져올 수 없습니다.</p>';
    resultDiv.style.display = 'block';
    return;
  }
  
  const companyInfo = data.company_info;
  const businessOverview = companyInfo.business_overview || '추천 정보가 없습니다.';
  
  // 입력 필드들과 버튼을 숨기기
  const innovationTypeField = modal.querySelector('#innovationType').closest('.form-group');
  const innovationCategoryField = modal.querySelector('#innovationCategory').closest('.form-group');
  const buttonGroup = modal.querySelector('#innovation-tab .button-group');
  
  if (innovationTypeField) innovationTypeField.style.display = 'none';
  if (innovationCategoryField) innovationCategoryField.style.display = 'none';
  if (buttonGroup) buttonGroup.style.display = 'none';
  
  const resultHTML = `
    <div style="max-height: 500px; overflow-y: auto; padding-right: 10px;">
      <h4>AI 추천 결과</h4>
      <div style="margin-bottom: 20px;">
        <p><strong>혁신성장 유형:</strong> ${data.innovation_type || '정보 없음'}</p>
        <p><strong>세부 카테고리:</strong> ${data.innovation_category || '정보 없음'}</p>
      </div>
      
      <h5>기업 기본 정보</h5>
      <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 15px;">
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 10px; font-size: 14px;">
          <div><strong>업체명:</strong> ${companyInfo.업체명 || '정보 없음'}</div>
          <div><strong>대표자명:</strong> ${companyInfo.대표자명 || '정보 없음'}</div>
          <div><strong>설립일자:</strong> ${companyInfo.설립일자 || '정보 없음'}</div>
          <div><strong>법인번호:</strong> ${companyInfo.법인번호 || '정보 없음'}</div>
          <div><strong>주민번호:</strong> ${companyInfo.주민번호 || '정보 없음'}</div>
          <div><strong>사업자번호:</strong> ${companyInfo.사업자번호 || '정보 없음'}</div>
          <div><strong>본사주소:</strong> ${companyInfo.본사주소 || '정보 없음'}</div>
          <div><strong>전화번호:</strong> ${companyInfo.전화번호 || '정보 없음'}</div>
          <div><strong>이메일:</strong> ${companyInfo.email || '정보 없음'}</div>
          <div><strong>팩스번호:</strong> ${companyInfo.팩스번호 || '정보 없음'}</div>
        </div>
        <div style="margin-top: 15px;">
          <strong>사업내용:</strong><br>
          <span style="color: #666;">${companyInfo.사업내용 || '정보 없음'}</span>
        </div>
      </div>
      
      <h5>AI 추천 사업 개요</h5>
      <div style="background-color: #e8f4fd; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; margin-bottom: 20px;">
        <p style="margin: 0; line-height: 1.6; color: #333;">${businessOverview}</p>
      </div>
      
      <h5>주요 생산 제품</h5>
      <div style="background-color: #f0f8ff; padding: 15px; border-radius: 4px; border-left: 4px solid #28a745; margin-bottom: 20px;">
        <p style="margin: 0; line-height: 1.6; color: #333;">${companyInfo.주요_생산_제품 || '정보 없음'}</p>
      </div>
      
      <h5>기술, 제품(상품), 공간(점포)의 경쟁력</h5>
      <div style="background-color: #fff8f0; padding: 15px; border-radius: 4px; border-left: 4px solid #ffc107; margin-bottom: 20px;">
        <p style="margin: 0; line-height: 1.6; color: #333;">${companyInfo.기술_제품_공간_경쟁력 || '정보 없음'}</p>
      </div>
      
      <h5>시장 상황</h5>
      <div style="background-color: #f8f0ff; padding: 15px; border-radius: 4px; border-left: 4px solid #6f42c1; margin-bottom: 20px;">
        <p style="margin: 0; line-height: 1.6; color: #333;">${companyInfo.시장상황 || '정보 없음'}</p>
      </div>
      
      <h5>생산 및 판매계획</h5>
      <div style="background-color: #f0fff0; padding: 15px; border-radius: 4px; border-left: 4px solid #20c997; margin-bottom: 20px;">
        <p style="margin: 0; line-height: 1.6; color: #333;">${companyInfo.생산_판매계획 || '정보 없음'}</p>
      </div>
    </div>
  `;
  
  resultDiv.innerHTML = resultHTML;
  resultDiv.style.display = 'block';
  console.log('혁신성장 추천 결과 표시됨 (입력 필드 숨김, 결과가 위로 올라옴)');
}

function generateInnovationDocx() {
  const innovationType = document.getElementById('innovationType').value.trim();
  const innovationCategory = document.getElementById('innovationCategory').value.trim();
  const innovationBusinessOverview = document.getElementById('innovationBusinessOverview').value.trim();
  
  if (!innovationType || !innovationCategory) {
    alert('혁신성장 유형과 세부 카테고리를 모두 선택해주세요.');
    return;
  }
  
  if (!innovationBusinessOverview) {
    alert('AI 추천을 먼저 받아주세요.');
    return;
  }
  
  // 로딩 상태 표시
  const generateBtn = document.querySelector('#innovation-tab .btn-generate');
  const originalText = generateBtn.textContent;
  generateBtn.textContent = '생성 중...';
  generateBtn.disabled = true;
  
  // 혁신성장 DOCX 생성 API 호출
  fetch(`/sales/auto_docx_innovation/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({
      row_id: window.currentDetailRowId,
      innovation_type: innovationType,
      innovation_category: innovationCategory,
      business_overview: innovationBusinessOverview
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
      console.log('혁신성장 DOCX 파일 다운로드 시작...');
      
      // 파일명 추출
      const contentDisposition = response.headers.get('content-disposition');
      let filename = '혁신성장_사업계획서.docx';
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
        
        console.log('혁신성장 DOCX 파일 다운로드 완료:', filename);
        
        // 모달창 닫기
        window.closeDocxModal();
      });
    }
  })
  .catch(error => {
    console.error('혁신성장 DOCX 생성 중 오류:', error);
    alert('혁신성장 DOCX 생성 중 오류가 발생했습니다.');
  })
  .finally(() => {
    // 버튼 상태 복원
    generateBtn.textContent = originalText;
    generateBtn.disabled = false;
  });
}

// 전역에서 접근할 수 있도록 window 객체에 할당
window.switchTab = switchTab;
window.updateInnovationCategories = updateInnovationCategories;
window.closeDocxModal = closeDocxModal;
window.getOpenAIRecommendation = getOpenAIRecommendation;
window.generateDocx = generateDocx;
window.getInnovationRecommendation = getInnovationRecommendation;
window.displayCreditRecommendationResult = displayCreditRecommendationResult;
window.displayInnovationRecommendationResult = displayInnovationRecommendationResult;
window.generateInnovationDocx = generateInnovationDocx;