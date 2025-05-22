const conselBtn = document.querySelector('.consel-nav-item-box');
const conselModal = document.querySelector('.consel-nav-modal-container');
const modalContent = document.querySelector('.consel-nav-modal-item-box');
const confirmBtn = document.querySelector('.consel-nav-modal-text-box-btn-wrap');

// 모달 열기
conselBtn.addEventListener('click', () => {
  conselModal.style.display = 'block';
});

// 모달 닫기 (확인 버튼 클릭 시)
confirmBtn.addEventListener('click', () => {
  conselModal.style.display = 'none';
});

// 모달 외부 클릭 시 닫기
conselModal.addEventListener('click', (e) => {
  if (!modalContent.contains(e.target)) {
    conselModal.style.display = 'none';
  }
});
