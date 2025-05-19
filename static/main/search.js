// view로 넘겨줄 데이터 양식
const selectedConditions = {
  region: null,
  business_style: null,
  industry: null,
  business_period: null,
  sales: null,
  export: null,
  employees: null
};

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

// 지역 선택 창
const search_region_container = document.querySelector('.search-region-container');
regions = document.querySelectorAll('.region');

document.querySelectorAll('.region').forEach(region => {
  region.addEventListener('click', () => {
    selectedConditions.region = region.innerText;
    businessStyle();
  });
});

// 사업자 현황 선택 창
const businessStyleContainer = document.querySelector('.business-style-container');
const businessStyleItems = document.querySelectorAll('.business-style-item-text');

function businessStyle() {
  search_region_container.style.display = 'none';
  businessStyleContainer.style.display = 'block';
}

businessStyleItems.forEach(businessStyleItem => {
  businessStyleItem.addEventListener('click', () => {
    selectedConditions.business_style = businessStyleItem.innerText;

    if (businessStyleItem.innerText === '창업 전') {
      WatingSearchResult();
    } else {
      industry();
    }
  });
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
  search_industry_container.style.display = 'block';
}

industryInput.addEventListener('keyup', (e) => {

  // 업종 검색창에 입력 후 엔터를 누르면
  if (e.key === 'Enter') {
    industrySection(e);
  }
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
        industryCategoryTable.innerHTML += `
          <tr>
            <td>${item.big_category}</td>
            <td>${item.small_category}</td>
            <td><button class="industry-category-button">선택</button></td>
          </tr>
        `;
      });
    });
  
  // 업종 옆 선택 버튼 클릭 시 소카테고리를 전달
  industryCategoryContainer.addEventListener('click', (e) => {
    if (e.target.tagName === 'BUTTON') {
      small = e.target.parentElement.parentElement.children[1].innerText;
      selectedConditions.industry = small;
      businessPeriod();
    }
  });
}

// 사업개시일 선택 창
const businessPeriodYear = document.querySelector('.business-period-year');
const businessPeriodMonth = document.querySelector('.business-period-month');
const businessPeriodContainer = document.querySelector('.business-period-container');
const businessPeriodButton = document.querySelector('.business-period-button');

function businessPeriod() {
  search_industry_container.style.display = 'none';
  businessPeriodContainer.style.display = 'block';
}

// 사업개시일 선택 시 사업개시일 전달
businessPeriodButton.addEventListener('click', () => {
  businessPeriod = `${businessPeriodYear.value}.${businessPeriodMonth.value}`

  selectedConditions.business_period = businessPeriod;
  billingLastYear();
});

// 전년도 매출 선택 창
const billingLastYearYear = document.querySelector('.billing-last-year-year');
const billingLastYearContainer = document.querySelector('.billing-last-year-container');
const billingLastYearButton = document.querySelector('.billing-last-year-button');

function billingLastYear() {
  businessPeriodContainer.style.display = 'none';
  billingLastYearContainer.style.display = 'block';
}

// 전년도 매출 선택 시 전년도 매출 전달
billingLastYearButton.addEventListener('click', () => {
  billingLastYear = `${billingLastYearYear.value}`;
  selectedConditions.sales = billingLastYear;
  exportPerformance();
});

// 수출 실적 선택 창
const exportPerformanceContainer = document.querySelector('.export-performance-container');
const exportPerformances = document.querySelectorAll('.export-performance-item-text');

function exportPerformance() {
  billingLastYearContainer.style.display = 'none';
  exportPerformanceContainer.style.display = 'block';
}

exportPerformances.forEach(exportPerformance => {
  exportPerformance.addEventListener('click', () => {
    selectedConditions.export = exportPerformance.innerText;
    employeeNumber();
  });
});

// 직원수 선택 창
const employeeNumberContainer = document.querySelector('.employee-number-container');
const employeeNumberInput = document.querySelector('.employee-number-input');
const employeeNumberButton = document.querySelector('.employee-number-button');
const employeeNumberItems = document.querySelectorAll('.employee-number-item');

function employeeNumber() {
  exportPerformanceContainer.style.display = 'none';
  employeeNumberContainer.style.display = 'block';
}

// 직원수 선택 시 직원수 전달
employeeNumberItems.forEach(employeeNumberItem => {
  employeeNumberItem.addEventListener('click', () => {
    selectedConditions.employees = employeeNumberItem.innerText;
    WatingSearchResult();
  });
});

// 검색 결과 기다리는 창에서 검색 결과로 넘어가기
function search(selectedConditions) {
  console.log(selectedConditions);
}