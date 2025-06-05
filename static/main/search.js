// view로 넘겨줄 데이터 양식
const selectedConditions = {
  region: null,
  business_style: null,
  big_industry: null,
  small_industry: null,
  business_period: null,
  sales: null,
  export: null,
  employees: null
};

const search_region_btn_container = document.querySelector('.search-region-btn-container');




const percentBox = document.querySelector('.percent-box-text');
let currentPercent = 0; // 현재 퍼센트 상태 저장

function animatePercent(targetPercent) {
  const duration = 500;
  const frameRate = 30;
  const totalFrames = duration / (1000 / frameRate);
  const increment = (targetPercent - currentPercent) / totalFrames;

  let frame = 0;

  const activePercentBox = document.querySelector('.search-container[style*="flex"] .percent-box-text');
  if (!activePercentBox) return;

  const interval = setInterval(() => {
    frame++;
    currentPercent += increment;
    if (frame >= totalFrames) {
      currentPercent = targetPercent;
      clearInterval(interval);
    }
    activePercentBox.innerText = `${Math.round(currentPercent)}%`;
  }, 1000 / frameRate);
}



const selectedColor = 'rgb(167 255 162)';
const defaultColor = '#fff';

// 검색 결과 기다리는 창
const searchResultContainer = document.querySelector('.search-result-container');

// 검색 결과 기다리는 창 빼고 display: none
function WatingSearchResult() {
  businessStyleContainer.style.display = 'none';
  industryCategoryContainer.style.display = 'none';
  businessPeriodContainer.style.display = 'none';
  billingLastYearContainer.style.display = 'none';
  exportPerformanceContainer.style.display = 'none';
  employeeNumberContainer.style.display = 'none';
  searchResultContainer.style.display = 'block';
}

// 검색 결과 없음 창
const searchNoneResultContainer = document.querySelector('.search-none-result-container');

function WatingNoneSearchResult() {
  businessStyleContainer.style.display = 'none';
  searchNoneResultContainer.style.display = 'block';
}

// 지역 선택 창
const search_region_container = document.querySelector('.search-region-container');
const search_region_button = document.querySelector('.search-region-btn-container');
regions = document.querySelectorAll('.region');

document.querySelectorAll('.region').forEach(region => {
  region.addEventListener('click', () => {
    document.querySelectorAll('.region').forEach(r => {
      r.style.backgroundColor = defaultColor; // 글자색도 초기화 (선택사항)
    });

    // 클릭한 region만 선택된 색으로 변경
    region.style.backgroundColor = selectedColor;

    // 선택값 저장
    selectedConditions.region = region.innerText;

  });
});

// function requireLogin(callback) {
//   if (window.IS_AUTHENTICATED === true || window.IS_AUTHENTICATED === 'true') {
//     // 로그인된 상태면 바로 콜백 실행
//     callback();
//     return;
//   }

//   // 로그인 안 된 경우 → 로그인 팝업
//   const width = 500;
//   const height = 600;
//   const left = (screen.width - width) / 2;
//   const top = (screen.height - height) / 2;

//   const popup = window.open(
//     "/accounts/kakao/login/",
//     "KakaoLoginPopup",
//     `width=${width},height=${height},top=${top},left=${left}`
//   );

//   const timer = setInterval(() => {
//     if (popup.closed) {
//       clearInterval(timer);

//       // 로그인 확인을 위해 서버에 인증 상태 요청
//       fetch("/member/whoami/")
//         .then(res => res.json())
//         .then(data => {
//           if (data.is_authenticated) {
//             window.IS_AUTHENTICATED = true;
//             callback();  // 로그인 완료 후 계속 진행
//           } else {
//             console.log("로그인이 필요합니다.");
//           }
//         });
//     }
//   }, 500);
// }

search_region_button.addEventListener('click', () => {
  fetch("/member/whoami/")
    .then(res => res.json())
    .then(data => {
      if (data.is_authenticated) {
        if (!selectedConditions.region) {
          warning();
        } else {
        
          console.log(selectedConditions.region);
          businessStyle();
          animatePercent(16);
        }
      } else {
        console.log("로그인이 필요합니다.");
        const width = 500;
        const height = 600;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;

        const popup = window.open(
          "/member/",
          "KakaoLoginPopup",
          `width=${width},height=${height},top=${top},left=${left}`
        );
      }
    });
});

    

// 사업자 현황 선택 창
const businessStyleContainer = document.querySelector('.business-style-container');
const businessStyleItems = document.querySelectorAll('.business-style-item-text');
const search_business_btn_container = document.querySelector('.search-business-btn-container');
function businessStyle() {
  search_region_container.style.display = 'none';
  businessStyleContainer.style.display = 'flex';
}

businessStyleItems.forEach(businessStyleItem => {
  businessStyleItem.addEventListener('click', () => {
    selectedConditions.business_style = businessStyleItem.innerText;

    document.querySelectorAll('.business-style-item-text').forEach(item => {
      item.style.backgroundColor = defaultColor;
    });

    businessStyleItem.style.backgroundColor = selectedColor;

    

  });
});

search_business_btn_container.addEventListener('click', () => {

  if (!selectedConditions.business_style) {
    warning();
  }
  else if (selectedConditions.business_style === '창업 전') {
    WatingNoneSearchResult();
  }
  else {

    if (selectedConditions.business_style === '창업 전') {
      WatingNoneSearchResult();
    } else {
      industry();
      animatePercent(32);
    }
  }
});

// 업종 선택 창
const search_industry_container = document.querySelector('.search-industry-container');
const industryInput = document.querySelector('.industry-category-input');
const bigCategoryBox = document.querySelector('.industry-big-category');
const smallCategoryBox = document.querySelector('.industry-small-category');
const industryCategoryTable = document.querySelector('.industry-category-table');
const industryCategoryContainer = document.querySelector('.industry-category-container');


function industry() {
  businessStyleContainer.style.display = 'none';
  search_industry_container.style.display = 'flex';
}

// 업종 검색창에 글자를 입력할때마다 검색 결과 표시
industryInput.addEventListener('keyup', (e) => {
    industrySection(e);
});

// 업종 검색 시 검색 결과 표시
function industrySection(e) {
  const keyword = e.target.value;

  // 검색이 만약 0글자이면 검색 결과 표시 안함
  if (keyword.length < 1) {
    industryCategoryTable.innerHTML = '';
    return;
  }

  // MySQL에 저장된 업종 대카테고리와 소카테고리에 검색
  fetch(`/search/industry/?q=${encodeURIComponent(keyword)}`)
  .then(res => res.json())
  .then(data => {
    industryCategoryTable.innerHTML = '';

    data.forEach(item => {
      const highlight = (text) => {
        const regex = new RegExp(`(${keyword})`, 'gi'); // 대소문자 구분 없이 매칭
        return text.replace(regex, '<mark>$1</mark>');
      };

      const bigCategory = highlight(item.big_category);
      const smallCategory = highlight(item.small_category);

      industryCategoryTable.innerHTML += `
        <div class="industry-table-row">
          <div class="industry-table-big">${bigCategory}</div>
          <div class="industry-table-small">${smallCategory}</div>
          <div class="industry-table-select"><button class="industry-category-button">선택</button></div>
        </div>
      `;
    });
  });
  
  // 업종 옆 선택 버튼 클릭 시 해당 대카테고리와 소카테고리를 전달
  industryCategoryContainer.addEventListener('click', (e) => {
    if (e.target.tagName === 'BUTTON') {

      big = e.target.parentElement.parentElement.children[0].innerText;
      small = e.target.parentElement.parentElement.children[1].innerText;
      selectedConditions.big_industry = big;
      selectedConditions.small_industry = small;
      businessPeriod();
      animatePercent(50);
    }
  });
}

// 사업개시일 선택 창
const businessPeriodYear = document.querySelector('.business-period-year');
const businessPeriodMonth = document.querySelector('.business-period-month');
const businessPeriodContainer = document.querySelector('.business-period-container');
const businessPeriodButton = document.querySelector('.search-business-period-btn-container');

// 연도: 숫자 2자리만 허용
document.querySelector('.business-period-year').addEventListener('input', function () {
  let value = this.value.replace(/[^0-9]/g, '');
  if (value.length > 2) value = value.slice(0, 2);
  this.value = value;
});

// 월: 숫자 2자리 + 1~12만 허용
document.querySelector('.business-period-month').addEventListener('input', function () {
  let value = this.value.replace(/[^0-9]/g, '');
  if (value.length > 2) value = value.slice(0, 2);

  if (value !== '') {
    const num = parseInt(value, 10);
    if (num < 1 || num > 12) {
      value = '';
    }
  }

  this.value = value;
});

function businessPeriod() {
  search_industry_container.style.display = 'none';
  businessPeriodContainer.style.display = 'flex';
}

// 사업개시일 선택 시 사업개시일 전달
businessPeriodButton.addEventListener('click', () => {
  businessPeriod = `${businessPeriodYear.value}.${businessPeriodMonth.value}`

  
  selectedConditions.business_period = businessPeriod;
  console.log(selectedConditions.business_period);

  if (!selectedConditions.business_period) {
    warning();
  } else {
    billingLastYear();
    animatePercent(80);
  }
});

// 전년도 매출 선택 창
const billingLastYearItems = document.querySelectorAll('.billing-last-year-item');
const billingLastYearContainer = document.querySelector('.billing-last-year-container');
const billingLastYearButton = document.querySelector('.billing-last-year-button');
const billingLastYearButtonContainer = document.querySelector('.search-billing-btn-container');

function billingLastYear() {
  businessPeriodContainer.style.display = 'none';
  billingLastYearContainer.style.display = 'flex';
}

billingLastYearItems.forEach(billingLastYearItem => {
  billingLastYearItem.addEventListener('click', () => {

    document.querySelectorAll('.billing-last-year-item').forEach(item => {
      item.style.backgroundColor = defaultColor;
    });

    billingLastYearItem.style.backgroundColor = selectedColor;

    billingLastYearValue = billingLastYearItem.innerText;
    selectedConditions.sales = billingLastYearValue;
  });
});

billingLastYearButtonContainer.addEventListener('click', () => {
  if (!selectedConditions.sales) {
    warning();
  } else {
    exportPerformance();
    animatePercent(90);
  }

});

// 수출 실적 선택 창
const exportPerformanceContainer = document.querySelector('.export-performance-container');
const exportPerformances = document.querySelectorAll('.export-performance-item-text');
const exportPerformanceButton = document.querySelector('.search-export-performance-btn-container');

function exportPerformance() {
  billingLastYearContainer.style.display = 'none';
  exportPerformanceContainer.style.display = 'flex';
}

exportPerformances.forEach(exportPerformance => {
  exportPerformance.addEventListener('click', () => {

    document.querySelectorAll('.export-performance-item-text').forEach(item => {
      item.style.backgroundColor = defaultColor;
    });

    exportPerformance.style.backgroundColor = selectedColor;

    if (exportPerformance.innerText === '"없음"') {
      selectedConditions.export = '실적 없음';
    } else if (exportPerformance.innerText === '"있음"') {
      selectedConditions.export = '실적 있음';
    } else {
      selectedConditions.export = exportPerformance.innerText;
    }
  });
});

exportPerformanceButton.addEventListener('click', () => {
  if (!selectedConditions.export) {
    warning();
  } else {
    employeeNumber();
    animatePercent(100);
  }
});

// 직원수 선택 창
const employeeNumberContainer = document.querySelector('.employee-number-container');
const employeeNumberInput = document.querySelector('.employee-number-input');
const employeeNumberButton = document.querySelector('.employee-number-button');
const employeeNumberItems = document.querySelectorAll('.employee-number-item');
const employeeNumberButtonContainer = document.querySelector('.search-employee-number-btn-container');

function employeeNumber() {
  exportPerformanceContainer.style.display = 'none';
  employeeNumberContainer.style.display = 'flex';
}

// 직원수 선택 시 직원수 전달
employeeNumberItems.forEach(employeeNumberItem => {
  employeeNumberItem.addEventListener('click', () => {

    document.querySelectorAll('.employee-number-item').forEach(item => {
      item.style.backgroundColor = defaultColor;
    });

    employeeNumberItem.style.backgroundColor = selectedColor;

    selectedConditions.employees = employeeNumberItem.innerText;
  });
});

employeeNumberButtonContainer.addEventListener('click', () => {
  if (!selectedConditions.employees) {
    warning();
  } else {
    search(selectedConditions);
    WatingSearchResult();
  }
});

// 검색 결과 기다리는 창에서 검색 결과로 넘어가기
function search(selectedConditions) {
  console.log(selectedConditions);

  const query = new URLSearchParams(selectedConditions).toString();
  window.location.href = `/search/ai-result/?${query}`;
}

const warningContainer = document.querySelector('.select-warning-container-wrapper');

function warning() {
  console.log('warning');
  warningContainer.style.display = 'block';
  setTimeout(() => {
    warningContainer.style.display = 'none';
  }, 3000);
}

warningContainer.addEventListener('click', () => {
  warningContainer.style.display = 'none';
});

const searchBackIcons = document.querySelectorAll('.search-back-icon');

const percentMap = {
  'search-region-container': 0,
  'business-style-container': 16,
  'search-industry-container': 32,
  'business-period-container': 50,
  'billing-last-year-container': 80,
  'export-performance-container': 90,
  'employee-number-container': 100
};


searchBackIcons.forEach(searchBackIcon => {
  searchBackIcon.addEventListener('click', () => {
    let currentContainer = searchBackIcon.parentElement;
    let prevContainer;

    if (currentContainer.classList.contains('business-style-container')) {
      prevContainer = search_region_container;
    } else if (currentContainer.classList.contains('search-industry-container')) {
      prevContainer = businessStyleContainer;
    } else if (currentContainer.classList.contains('business-period-container')) {
      prevContainer = search_industry_container;
    } else if (currentContainer.classList.contains('billing-last-year-container')) {
      prevContainer = businessPeriodContainer;
    } else if (currentContainer.classList.contains('export-performance-container')) {
      prevContainer = billingLastYearContainer;
    } else if (currentContainer.classList.contains('employee-number-container')) {
      prevContainer = exportPerformanceContainer;
    }

    if (prevContainer) {
      currentContainer.style.display = 'none';
      prevContainer.style.display = 'flex';

      // ✅ 퍼센트 복원 애니메이션
      const containerClass = [...prevContainer.classList].find(cls => percentMap.hasOwnProperty(cls));
      if (containerClass) {
        animatePercent(percentMap[containerClass]);
      }
    }
  });
});


const searchModalBtn = document.querySelector('.industry-search-text2');
const indModalWrap = document.querySelector('.ind-modal-wrap');
const indModalCloseBtn = document.querySelector('.ind-modal-close-btn');
const indIcon = document.querySelector('.industry-search-icon');

searchModalBtn.addEventListener('click', () => {
  search_industry_container.style.display = 'none';
  indModalWrap.style.display = 'flex';
});

indIcon.addEventListener('click', () => {
  search_industry_container.style.display = 'none';
  indModalWrap.style.display = 'flex';
});

indModalCloseBtn.addEventListener('click', () => {
  search_industry_container.style.display = 'flex';
  indModalWrap.style.display = 'none';
});

const modalGptContainer = document.querySelector('.modal-gpt-container');
const indModalBtn = document.querySelector('.ind-modal-btn');
const indModalInput = document.querySelector('.ind-modal-input');

let isLoading = false;  // 요청 중 여부를 추적

function handleSearch() {
  if (isLoading) return;

  const keyword = indModalInput.value.trim();
  if (keyword.length === 0) return;

  isLoading = true;
  indModalBtn.disabled = true;

  modalGptContainer.innerHTML += `
    <div class="modal-gpt-text-container2">
      <div class="modal-gpt-text2">${keyword}</div>
    </div>
  `;

  // 🔄 로딩 애니메이션 추가
  const loadingEl = document.createElement('div');
  loadingEl.className = 'modal-gpt-loading';
  loadingEl.innerHTML = `
    <div class="loading-dots">
      <span>.</span><span>.</span><span>.</span>
    </div>
  `;
  modalGptContainer.appendChild(loadingEl);

  const root = 'https://namatji.com';
  const local = 'http://127.0.0.1:8000';

  fetch(`${root}/search/industry-api/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ keyword })
  })
  .then(res => res.json())
  .then(data => {
    const cleanText = data.response
      .split('\n')
      .map(line => line.trimStart())
      .join('\n');

    // ✅ 로딩 애니메이션 제거
    const oldLoading = document.querySelector('.modal-gpt-loading');
    if (oldLoading) oldLoading.remove();

    // ✅ 결과 표시
    modalGptContainer.innerHTML += `
      <div class="modal-gpt-text-container">
        <div class="modal-gpt-text" style="white-space: pre-wrap;">${cleanText}</div>
      </div>
    `;

    // ✅ 스크롤 가장 아래로 이동
    modalGptContainer.scrollTo({
      top: modalGptContainer.scrollHeight,
      behavior: 'smooth'
    });
    
  })
  .finally(() => {
    console.log('finally');
    isLoading = false;
    const latestBtn = document.querySelector('.ind-modal-btn');
    if (latestBtn) latestBtn.disabled = false;
  });
}


// 클릭 or 엔터 이벤트 그대로 유지
indModalBtn.addEventListener('click', handleSearch);
indModalInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    handleSearch();
    indModalInput.value = '';
    // ✅ 스크롤 가장 아래로 이동
    modalGptContainer.scrollTo({
      top: modalGptContainer.scrollHeight,
      behavior: 'smooth'
    });
  }
});

// CSRF 토큰 가져오기 함수
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}






