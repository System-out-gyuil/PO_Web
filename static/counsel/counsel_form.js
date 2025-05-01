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

// 유효성 검사
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

const counselForm = document.querySelector("form");
const phoneInput = document.getElementById("phone");
const inputElements = document.querySelectorAll(
  "select, input.inputs"
);

const phoneInputs = document.querySelectorAll("input.phone-input");
const dateInputs = document.querySelectorAll("input.date-input");
const sales24Inputs = document.querySelectorAll("input.sales-input24");
const sales25Inputs = document.querySelectorAll("input.sales-input25");


const submitBtn = document.querySelector("button");

submitBtn.addEventListener("click", e => {
  const tel1 = phone1.value.trim();
  const tel2 = phone2.value.trim();
  const tel3 = phone3.value.trim();

  // 유효성 검사는 여기에 해도 되고 따로 validateForm() 호출해도 됨
  if (tel1 && tel2 && tel3) {
    phoneHidden.value = `${tel1}-${tel2}-${tel3}`;
    
  }

  phoneInputs.forEach(input => {
    console.log(input)
    if (!input.value.trim()) {
      console.log(1234)
      input.classList.add("input-error");
    } else {
      input.classList.remove("input-error");
    }
  });

  dateInputs.forEach(input => {
    if (!input.value.trim()) {
      input.classList.add("input-error");
    } else {
      input.classList.remove("input-error");
    }
  });

  sales24Inputs.forEach(input => {
    if (!input.value.trim()) {
      input.classList.add("input-error");
    } else {
      input.classList.remove("input-error");
    }
  });

  sales25Inputs.forEach(input => {
    if (!input.value.trim()) {
      input.classList.add("input-error");
    } else {
      input.classList.remove("input-error");
    }
  });

  if (startYear.value && startMonth.value) {
    startDateHidden.value = `${startYear.value}년 ${startMonth.value}월`;
  }

  // 24년 매출 합치기
  if (sales2024Eok.value && sales2024Cheun.value && sales2024Baek.value) {
    sales2024Hidden.value = `${sales2024Eok.value}억 ${sales2024Cheun.value}천 ${sales2024Baek.value}백만원`;
  }

  // 25년 매출 합치기
  if (sales2025Eok.value && sales2025Cheun.value && sales2025Baek.value) {
    sales2025Hidden.value = `${sales2025Eok.value}억 ${sales2025Cheun.value}천 ${sales2025Baek.value}백만원`;
  }

  const hasInvalid = Array.from(inputElements).some(input => !validateForm(input));
  if (!hasInvalid) {
    counselForm.submit();
  }

  inputElements.forEach(input => {
    validateForm(input);
  })
});

phoneInput.addEventListener("input", e => {
  autoHyphenPhone(e.target);
})

