const phone1 = document.getElementById("phone1");
const phone2 = document.getElementById("phone2");
const phone3 = document.getElementById("phone3");
const phoneHidden = document.getElementById("phone");

const startYear = document.getElementById("start_year");
const startMonth = document.getElementById("start_month");
const startDateHidden = document.getElementById("start_date");

const sales2024Eok = document.getElementById("sales_2024_eok");
const sales2024Cheun = document.getElementById("sales_2024_cheun");
const sales2024Baek = document.getElementById("sales_2024_baek");
const sales2024Hidden = document.getElementById("sales_2024");

const sales2025Eok = document.getElementById("sales_2025_eok");
const sales2025Cheun = document.getElementById("sales_2025_cheun");
const sales2025Baek = document.getElementById("sales_2025_baek");
const sales2025Hidden = document.getElementById("sales_2025");

const consentCheckbox = document.getElementById("consent");
const consentError = document.getElementById("consent-error");

const counselForm = document.querySelector("form");
const phoneInput = document.getElementById("phone");
const inputElements = document.querySelectorAll("select, input.inputs");

const phoneInputs = document.querySelectorAll("input.phone-input");
const dateInputs = document.querySelectorAll("input.date-input");
const sales24Inputs = document.querySelectorAll("input.sales-input24");
const sales25Inputs = document.querySelectorAll("input.sales-input25");

const consent2Checkbox = document.getElementById("consent2");
const consent2Error = document.getElementById("consent2-error");

const submitBtn = document.querySelector("button");

// 공통 유효성 검사 함수
function validateForm(Element) {
  let isValid = true;
  if (!Element.value.trim()) {
    Element.classList.add("input-error");
    Element.nextElementSibling.style.display = "block";
    isValid = false;
  } else {
    Element.classList.remove("input-error");
    Element.nextElementSibling.style.display = "none";
  }
  return isValid;
}

// 제출 버튼 클릭 시
submitBtn.addEventListener("click", e => {
  const tel1 = phone1.value.trim();
  const tel2 = phone2.value.trim();
  const tel3 = phone3.value.trim();

  if (tel1 && tel2 && tel3) {
    phoneHidden.value = `${tel1}-${tel2}-${tel3}`;
  }

  // 전화번호, 날짜, 매출 항목 유효성 체크
  phoneInputs.forEach(input => {
    input.classList.toggle("input-error", !input.value.trim());
  });

  dateInputs.forEach(input => {
    input.classList.toggle("input-error", !input.value.trim());
  });

  sales24Inputs.forEach(input => {
    input.classList.toggle("input-error", !input.value.trim());
  });

  sales25Inputs.forEach(input => {
    input.classList.toggle("input-error", !input.value.trim());
  });



  // 사업 개시일 문자열로 변환
  if (startYear.value && startMonth.value) {
    startDateHidden.value = `${startYear.value}년 ${startMonth.value}월`;
  }

  // 2024 매출 문자열 조합
  if (sales2024Eok.value && sales2024Cheun.value && sales2024Baek.value) {
    sales2024Hidden.value = `${sales2024Eok.value}억 ${sales2024Cheun.value}천 ${sales2024Baek.value}백만원`;
  }

  // 2025 매출 문자열 조합
  if (sales2025Eok.value && sales2025Cheun.value && sales2025Baek.value) {
    sales2025Hidden.value = `${sales2025Eok.value}억 ${sales2025Cheun.value}천 ${sales2025Baek.value}백만원`;
  }

  // 개인정보 수집 동의 체크 확인
  let isConsentChecked = consentCheckbox.checked;
  consentError.style.display = isConsentChecked ? "none" : "block";

  // 개인정보 제3자 제공 동의 체크 확인
  let isConsent2Checked = consent2Checkbox.checked;
  consent2Error.style.display = isConsent2Checked ? "none" : "block";

  // input/select 요소 중 하나라도 유효하지 않으면 true 반환
  const hasInvalid = Array.from(inputElements).some(input => !validateForm(input));

  // 모든 유효성 통과 + 동의 시 폼 제출
  if (!hasInvalid && isConsentChecked && isConsent2Checked) {
    counselForm.submit();
  }

  // 스타일 유지 목적 재검사
  inputElements.forEach(input => {
    validateForm(input);
  });
});
