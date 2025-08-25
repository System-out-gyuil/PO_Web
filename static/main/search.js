// view로 넘겨줄 데이터 양식
const selectedConditions = {
  region: null,
  detail_region: null,
  business_style: null,
  big_industry: null,
  small_industry: null,
  business_period: null,
  sales: null,
  export: null,
  employees: null
};

const percentBox = document.querySelector('.percent-box-text');
let currentPercent = 0; // 현재 퍼센트 상태 저장

function animatePercent(targetPercent) {
  console.log(targetPercent);
  const duration = 500;
  const frameRate = 30;
  const totalFrames = duration / (1000 / frameRate);
  const increment = (targetPercent - currentPercent) / totalFrames;

  let frame = 0;

  const activePercentBox = document.querySelector('section[style*="flex"] .percent-box-text');
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

const selectedColor = '#bfc2fd';
const defaultColor = '#fff';

// 검색 결과 기다리는 창
const searchResultContainer = document.querySelector('#first-section');

// 검색 결과 기다리는 창 빼고 display: none
function WatingSearchResult() {
  businessStyleContainer.style.display = 'none';
  industryCategoryContainer.style.display = 'none';
  businessPeriodContainer.style.display = 'none';
  billingLastYearContainer.style.display = 'none';
  exportPerformanceContainer.style.display = 'none';
  employeeNumberContainer.style.display = 'none';
  searchResultContainer.style.display = 'flex';
}

// 검색 결과 없음 창
const searchNoneResultContainer = document.querySelector('.search-none-result-container-wrapper');
const html = document.querySelector('html');

function WatingNoneSearchResult() {
  businessStyleContainer.style.display = 'none';
  searchNoneResultContainer.style.display = 'block';
  html.style.removeProperty('height');
}

// 지역별 상세지역 데이터
const regionDetails = {
  "서울": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
  "경기": ["수원시", "성남시", "의정부시", "안양시", "부천시", "광명시", "평택시", "동두천시", "안산시", "고양시", "과천시", "구리시", "남양주시", "오산시", "시흥시", "군포시", "의왕시", "하남시", "용인시", "파주시", "이천시", "안성시", "김포시", "화성시", "광주시", "여주시", "양평군", "연천군", "포천시", "가평군", "양주시"],
  "인천": ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"],
  "강원": ["춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시", "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군", "양구군", "인제군", "고성군", "양양군"],
  "경북": ["포항시", "경주시", "김천시", "안동시", "구미시", "영주시", "영천시", "상주시", "문경시", "경산시", "군위군", "의성군", "청송군", "영양군", "영덕군", "청도군", "고령군", "성주군", "칠곡군", "예천군", "봉화군", "울진군", "울릉군"],
  "경남": ["창원시", "진주시", "통영시", "사천시", "김해시", "밀양시", "거제시", "양산시", "의령군", "함안군", "창녕군", "고성군", "남해군", "하동군", "산청군", "함양군", "거창군", "합천군"],
  "부산": ["중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"],
  "대구": ["중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군"],
  "울산": ["중구", "남구", "동구", "북구", "울주군"],
  "대전": ["중구", "동구", "서구", "유성구", "대덕구"],
  "충북": ["청주시", "충주시", "제천시", "보은군", "옥천군", "영동군", "증평군", "진천군", "괴산군", "음성군", "단양군"],
  "충남": ["천안시", "공주시", "보령시", "아산시", "서산시", "논산시", "계룡시", "당진시", "금산군", "부여군", "서천군", "청양군", "홍성군", "예산군", "태안군"],
  "전북": ["전주시", "군산시", "익산시", "정읍시", "남원시", "김제시", "완주군", "진안군", "무주군", "장수군", "임실군", "순창군", "고창군", "부안군"],
  "전남": ["목포시", "여수시", "순천시", "나주시", "광양시", "담양군", "곡성군", "구례군", "고흥군", "보성군", "화순군", "장흥군", "강진군", "해남군", "영암군", "무안군", "함평군", "영광군", "장성군", "완도군", "진도군", "신안군"],
  "광주": ["동구", "서구", "남구", "북구", "광산구"],
  "제주": ["제주시", "서귀포시"],
  "세종": ["세종특별자치시"]
};

// 지역 선택 창
const search_region_container = document.querySelector('#region-section');
const search_region_button = document.querySelector('.search-region-btn-container');
const detail_region_section = document.querySelector('#detail-region-section');
const detailRegionSelect = document.querySelector('#detail-region-select');
const search_detail_region_button = document.querySelector('.search-detail-region-btn-container');
const regions = document.querySelectorAll('.region');

document.querySelectorAll('.region').forEach(region => {
  region.addEventListener('click', () => {
    document.querySelectorAll('.region').forEach(r => {
      r.style.backgroundColor = defaultColor;
    });

    // 클릭한 region만 선택된 색으로 변경
    region.style.backgroundColor = selectedColor;

    // 선택된 지역 저장
    const selectedRegion = region.getAttribute('data-region');
    selectedConditions.region = selectedRegion;
    selectedConditions.detail_region = null; // 상세지역 초기화
  });
});

// 지역 선택 다음 버튼 클릭 시 상세지역 선택 탭으로 이동
search_region_button.addEventListener('click', () => {
  fetch("/member/whoami/")
    .then(res => res.json())
    .then(data => {
      if (data.is_authenticated) {
        if (!selectedConditions.region) {
          warning();
        } else {
          // 상세지역 선택 탭으로 이동
          showDetailRegionSection();
          animatePercent(8);
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

// 상세지역 선택 탭 표시
function showDetailRegionSection() {
  search_region_container.style.display = 'none';
  detail_region_section.style.display = 'flex';
  
  // 선택된 지역에 해당하는 상세지역 옵션 설정
  const selectedRegion = selectedConditions.region;
  if (regionDetails[selectedRegion]) {
    // 기존 옵션들을 모두 제거
    detailRegionSelect.innerHTML = '';
    
    // 기본 옵션 추가
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '상세지역 선택';
    defaultOption.selected = true; // 기본 옵션을 선택된 상태로 설정
    detailRegionSelect.appendChild(defaultOption);
    
    // 상세지역 옵션들 추가
    regionDetails[selectedRegion].forEach(detail => {
      const option = document.createElement('option');
      option.value = detail;
      option.textContent = detail;
      detailRegionSelect.appendChild(option);
    });
    
    // 초기 상태 설정
    detailRegionSelect.selectedIndex = 0;
  }
}

// 상세지역 선택 시 저장
detailRegionSelect.addEventListener('change', () => {
  const selectedValue = detailRegionSelect.value;
  const selectedText = detailRegionSelect.options[detailRegionSelect.selectedIndex].text;
  selectedConditions.detail_region = selectedValue;
  
  console.log('상세지역 선택됨 - value:', selectedValue);
  console.log('상세지역 선택됨 - text:', selectedText);
  console.log('selectedConditions:', selectedConditions);
  console.log('셀렉트 태그 현재 상태:', detailRegionSelect.value, detailRegionSelect.selectedIndex);
  console.log('전체 옵션들:', Array.from(detailRegionSelect.options).map(opt => ({value: opt.value, text: opt.text, selected: opt.selected})));
  
  // 선택된 옵션이 화면에 표시되도록 selectedIndex 설정
  if (selectedValue) {
    for (let i = 0; i < detailRegionSelect.options.length; i++) {
      if (detailRegionSelect.options[i].value === selectedValue) {
        detailRegionSelect.selectedIndex = i;
        console.log('selectedIndex 설정됨:', i);
        break;
      }
    }
  }
});

// 상세지역 선택 다음 버튼 클릭 시 사업자 현황 탭으로 이동
search_detail_region_button.addEventListener('click', () => {
  console.log('상세지역 다음 버튼 클릭됨');
  console.log('현재 selectedConditions:', selectedConditions);
  
  if (!selectedConditions.detail_region) {
    console.log('상세지역이 선택되지 않음');
    warning();
  } else {
    console.log('상세지역 선택 완료:', selectedConditions.region, selectedConditions.detail_region);
    businessStyle();
    animatePercent(16);
  }
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

// 사업자 현황 선택 창
const businessStyleContainer = document.querySelector('#business-style-section');
const businessStyleItems = document.querySelectorAll('.business-style-item-text');
const search_business_btn_container = document.querySelector('.search-business-btn-container');
function businessStyle() {
  detail_region_section.style.display = 'none';
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
const search_industry_container = document.querySelector('#industry-section');
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
const businessPeriodContainer = document.querySelector('#business-period-section');
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
  const year = businessPeriodYear.value.trim();
  const month = businessPeriodMonth.value.trim();
  
  // 에러 스타일 초기화
  businessPeriodYear.classList.remove('error');
  businessPeriodMonth.classList.remove('error');
  
  // 년도와 월이 모두 입력되었는지 확인
  if (!year || !month) {
    if (!year) businessPeriodYear.classList.add('error');
    if (!month) businessPeriodMonth.classList.add('error');
    showCustomWarning('개업일의 년도와 월을 모두 입력해주세요.');
    return;
  }
  
  // 년도가 2자리 숫자인지 확인
  if (year.length !== 2 || !/^\d{2}$/.test(year)) {
    businessPeriodYear.classList.add('error');
    showCustomWarning('년도를 2자리 숫자로 입력해주세요. (예: 25)');
    return;
  }
  
  // 월이 1~12 범위인지 확인
  const monthNum = parseInt(month, 10);
  if (monthNum < 1 || monthNum > 12) {
    businessPeriodMonth.classList.add('error');
    showCustomWarning('월을 1~12 사이의 숫자로 입력해주세요. (예: 03)');
    return;
  }
  
  businessPeriod = `${year}.${month}`;
  selectedConditions.business_period = businessPeriod;
  console.log(selectedConditions.business_period);

  billingLastYear();
  animatePercent(80);
});

// 입력 필드에 입력할 때 에러 스타일 제거
businessPeriodYear.addEventListener('input', () => {
  businessPeriodYear.classList.remove('error');
});

businessPeriodMonth.addEventListener('input', () => {
  businessPeriodMonth.classList.remove('error');
});

// 커스텀 경고 메시지 표시 함수
function showCustomWarning(message) {
  const warningContainer = document.querySelector('#select-warning-section');
  const warningText = warningContainer.querySelector('.select-warning-text');
  
  // 기존 메시지를 새로운 메시지로 변경
  warningText.innerText = message;
  
  // 경고 표시
  warningContainer.style.display = 'block';
  
  // 3초 후 자동으로 숨김
  setTimeout(() => {
    warningContainer.style.display = 'none';
    // 원래 메시지로 복원
    warningText.innerText = '옵션을 선택해주세요!';
  }, 3000);
}

// 전년도 매출 선택 창
const billingLastYearItems = document.querySelectorAll('.billing-last-year-item');
const billingLastYearContainer = document.querySelector('#billing-last-year-section');
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
const exportPerformanceContainer = document.querySelector('#export-performance-section');
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
const employeeNumberContainer = document.querySelector('#employee-number-section');
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

const warningContainer = document.querySelector('#select-warning-section');

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
  'detail-region-container': 8,
  'business-style-container': 16,
  'search-industry-container': 32,
  'business-period-container': 50,
  'billing-last-year-container': 80,
  'export-performance-container': 90,
  'employee-number-container': 100
};


searchBackIcons.forEach(searchBackIcon => {
  searchBackIcon.addEventListener('click', () => {
    let currentContainer = searchBackIcon.parentElement.parentElement;
    // console.log(currentContainer);
    let prevContainer;

    if (currentContainer.id === 'detail-region-section') {
      prevContainer = search_region_container;
    } else if (currentContainer.id === 'business-style-section') {
      prevContainer = detail_region_section;
    } else if (currentContainer.id === 'industry-section') {
      prevContainer = businessStyleContainer;
    } else if (currentContainer.id === 'business-period-section') {
      prevContainer = search_industry_container;
    } else if (currentContainer.id === 'billing-last-year-section') {
      prevContainer = businessPeriodContainer;
    } else if (currentContainer.id === 'export-performance-section') {
      prevContainer = billingLastYearContainer;
    } else if (currentContainer.id === 'employee-number-section') {
      prevContainer = exportPerformanceContainer;
    }

    if (prevContainer) {
      currentContainer.style.display = 'none';
      prevContainer.style.display = 'flex';

      // ✅ 퍼센트 복원 애니메이션
      const containerClass = [...prevContainer.children[0].classList].find(cls => percentMap.hasOwnProperty(cls));
      console.log("123", containerClass);
      if (containerClass) {
        animatePercent(percentMap[containerClass]);
      }
    }
  });
});


const searchModalBtn = document.querySelector('.industry-search-text2');
const indModalWrap = document.querySelector('#industry-search-section');
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






