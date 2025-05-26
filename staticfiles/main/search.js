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

search_region_button.addEventListener('click', () => {
  if (!selectedConditions.region) {
    warning();
  } else {
    
    console.log(selectedConditions.region);
    businessStyle();
  }
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
  } else {

    if (selectedConditions.business_style === '창업 전') {
      WatingNoneSearchResult();
    } else {
      industry();
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

  if (!selectedConditions.business_period) {
    warning();
  } else {
    billingLastYear();
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

searchBackIcons.forEach(searchBackIcon => {
  searchBackIcon.addEventListener('click', () => {
    if (searchBackIcon.parentElement.classList.contains('business-style-container')) {
      search_region_container.style.display = 'flex';
      businessStyleContainer.style.display = 'none';

    } else if (searchBackIcon.parentElement.classList.contains('search-industry-container')) {
      businessStyleContainer.style.display = 'flex';
      search_industry_container.style.display = 'none';

    } else if (searchBackIcon.parentElement.classList.contains('business-period-container')) {
      search_industry_container.style.display = 'flex';
      businessPeriodContainer.style.display = 'none';

    } else if (searchBackIcon.parentElement.classList.contains('billing-last-year-container')) {
      businessPeriodContainer.style.display = 'flex';
      billingLastYearContainer.style.display = 'none';

    } else if (searchBackIcon.parentElement.classList.contains('export-performance-container')) {
      billingLastYearContainer.style.display = 'flex';
      exportPerformanceContainer.style.display = 'none';

    } else if (searchBackIcon.parentElement.classList.contains('employee-number-container')) {
      exportPerformanceContainer.style.display = 'flex';
      employeeNumberContainer.style.display = 'none';
    }
  });
});



