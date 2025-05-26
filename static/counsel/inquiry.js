document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('form');
  const nameInput = document.getElementById('name');
  const phoneInput = document.getElementById('phone');
  const inquiryInput = document.getElementById('inquiry');
  const consentCheckbox = document.querySelector('.consent-checkbox');
  const consent2Checkbox = document.querySelector('.consent2-checkbox');

  // 전화번호 입력: 숫자만, 자동 하이픈 처리
  phoneInput.addEventListener('input', function (e) {
    let numbers = e.target.value.replace(/\D/g, ''); // 숫자만 남김
    if (numbers.length <= 3) {
      e.target.value = numbers;
    } else if (numbers.length <= 7) {
      e.target.value = numbers.slice(0, 3) + '-' + numbers.slice(3);
    } else if (numbers.length <= 11) {
      e.target.value = numbers.slice(0, 3) + '-' + numbers.slice(3, 7) + '-' + numbers.slice(7, 11);
    } else {
      e.target.value = numbers.slice(0, 3) + '-' + numbers.slice(3, 7) + '-' + numbers.slice(7, 11);
    }
  });

  // 제출 시 유효성 검사
  form.addEventListener('submit', function (e) {
    const name = nameInput.value.trim();
    const phone = phoneInput.value.trim();
    const inquiry = inquiryInput.value.trim();
    const isConsentChecked = consentCheckbox.checked;
    const isConsent2Checked = consent2Checkbox.checked;

    if (!name || !phone || !inquiry) {
      alert('모든 항목을 입력해 주세요.');
      e.preventDefault();
      return;
    }

    // 전화번호 형식 검사 (예: 010-1234-5678)
    const phonePattern = /^010-\d{4}-\d{4}$/;
    if (!phonePattern.test(phone)) {
      alert('전화번호 형식이 올바르지 않습니다. 예: 010-1234-5678');
      e.preventDefault();
      return;
    }

    if (!isConsentChecked || !isConsent2Checked) {
      alert('개인정보 수집 및 제3자 제공에 모두 동의해야 합니다.');
      e.preventDefault();
      return;
    }
  });
});
