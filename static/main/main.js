function toggleContent(counter) {
  const summary = document.getElementById(`summary-${counter}`);
  const full = document.getElementById(`full-${counter}`);
  const button = document.getElementById(`button-${counter}`);

  if (full.classList.contains('hidden')) {
    summary.style.display = "none";
    full.style.display = "block";
    full.classList.remove('hidden');
    button.textContent = "접기"; // 버튼 문구 변경
  } else {
    summary.style.display = "-webkit-box";
    full.style.display = "none";
    full.classList.add('hidden');
    button.textContent = "더보기";
  }
}

// 페이지 처음 로드할 때 'full'을 숨기는 초기화 코드 추가
document.addEventListener("DOMContentLoaded", function() {
  const fullTexts = document.querySelectorAll('.full-text');
  fullTexts.forEach(function(full) {
    full.style.display = "none"; // 처음엔 전체 내용 숨김
    full.classList.add('hidden'); // 숨김 상태 표시용 클래스 추가
  });
});
