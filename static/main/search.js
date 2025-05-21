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
        <tr>
          <td>${bigCategory}</td>
          <td>${smallCategory}</td>
          <td><button class="industry-category-button">선택</button></td>
        </tr>
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
const billingLastYearItems = document.querySelectorAll('.billing-last-year-item');
const billingLastYearContainer = document.querySelector('.billing-last-year-container');
const billingLastYearButton = document.querySelector('.billing-last-year-button');

function billingLastYear() {
  businessPeriodContainer.style.display = 'none';
  billingLastYearContainer.style.display = 'block';
}

billingLastYearItems.forEach(billingLastYearItem => {
  billingLastYearItem.addEventListener('click', () => {
    billingLastYear = billingLastYearItem.innerText;
    selectedConditions.sales = billingLastYear;
    exportPerformance();
  });
});

// 전년도 매출 선택 시 전년도 매출 전달
// billingLastYearButton.addEventListener('click', () => {
//   billingLastYear = `${billingLastYearItems.value}`;
//   selectedConditions.sales = billingLastYear;
//   exportPerformance();
// });

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
    search(selectedConditions);
    WatingSearchResult();
  });
});

// 검색 결과 기다리는 창에서 검색 결과로 넘어가기
function search(selectedConditions) {
  console.log(selectedConditions);

  const query = new URLSearchParams(selectedConditions).toString();
  window.location.href = `/search/ai-result/?${query}`;
}
