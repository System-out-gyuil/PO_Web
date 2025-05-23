const conselBtn = document.querySelector('.consel-nav-item-box');
const conselModal = document.querySelector('.consel-nav-modal-container');
const modalContent = document.querySelector('.consel-nav-modal-item-box');
const confirmBtn = document.querySelector('.consel-nav-modal-text-box-btn-wrap');
const nameInput = document.querySelector('.name-wrap-input');
const phoneInput = document.querySelector('.phone-wrap-input');

// 모달 열기
conselBtn.addEventListener('click', () => {
  conselModal.style.display = 'block';
});

confirmBtn.addEventListener('click', () => {
  const name = nameInput.value;
  const phone = phoneInput.value;
  const consent = document.querySelector('.consent-checkbox').checked;
  const consent2 = document.querySelector('.consent2-checkbox').checked;

  if (!name || !phone || !consent || !consent2) {
    alert("모든 항목을 입력하고 동의해주세요.");
    return;
  }

  const params = new URLSearchParams(window.location.search);
  params.set("name", name);
  params.set("phone", phone);
  params.set("consent", "on");
  params.set("consent2", "on");

  fetch(`/counsel/?${params.toString()}`)
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {
        alert("상담 신청이 완료되었습니다!");
        conselModal.style.display = 'none';
      } else {
        alert("신청 처리 중 오류가 발생했습니다.");
      }
    })
    .catch(error => {
      console.error(error);
      alert("서버 요청 실패");
    });
});


// 모달 외부 클릭 시 닫기
conselModal.addEventListener('click', (e) => {
  if (!modalContent.contains(e.target)) {
    conselModal.style.display = 'none';
  }
});


