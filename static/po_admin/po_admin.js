const counselWrapper = document.querySelector('.counsel-wrapper');
const inquiryWrapper = document.querySelector('.inquiry-wrapper');
const countWrapper = document.querySelector('.count-wrapper');

const counselNavItem = document.querySelector('.counsel-nav-item');
const inquiryNavItem = document.querySelector('.inquiry-nav-item');
const countNavItem = document.querySelector('.count-nav-item');

// 모든 섹션 숨기기
function hideAllSections() {
  counselWrapper.style.display = 'none';
  inquiryWrapper.style.display = 'none';
  countWrapper.style.display = 'none';
}

// 모든 탭 비활성화
function clearActiveTabs() {
  counselNavItem.classList.remove('active');
  inquiryNavItem.classList.remove('active');
  countNavItem.classList.remove('active');
}

// 상담 신청
counselNavItem.addEventListener('click', () => {
  hideAllSections();
  clearActiveTabs();
  counselWrapper.style.display = 'flex';
  counselNavItem.classList.add('active');
});

// 고객 문의
inquiryNavItem.addEventListener('click', () => {
  hideAllSections();
  clearActiveTabs();
  inquiryWrapper.style.display = 'flex';
  inquiryNavItem.classList.add('active');
});

// 조회수 통계
countNavItem.addEventListener('click', () => {
  hideAllSections();
  clearActiveTabs();
  countWrapper.style.display = 'flex';
  countNavItem.classList.add('active');
});

// 초기 상태 설정 (처음에 상담 신청 리스트만 표시)
document.addEventListener('DOMContentLoaded', () => {
  hideAllSections();
  counselWrapper.style.display = 'flex';
  counselNavItem.classList.add('active');
});


function fetchCounts(startDate = null, endDate = null) {
  let root = 'http://localhost:8000';
  let url = `${root}/po_admin/counts-by-date/`;
  if (startDate && endDate) {
    url += `?start=${startDate}&end=${endDate}`;
  }

  fetch(url)
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById('counts-body');
      const range = document.getElementById('date-range');
      tbody.innerHTML = '';
      range.innerText = `${data.start} ~ ${data.end}`;

      const nameMap = {
        main: "메인페이지",
        search: "AI 진단하기",
        search_ai_result: "AI 진단 결과",
        inquiry: "상담 문의",
        board: "지원사업 게시판",
        board_detail: "게시판 본문",
        counsel: "상담 문의"
      };

      const entries = Object.entries(data.counts).sort();
      for (const [date, counts] of entries) {
        for (const [type, count] of Object.entries(counts)) {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${date}</td>
            <td>${nameMap[type] || type}</td>
            <td>${count}</td>
          `;
          tbody.appendChild(tr);
        }
      }
    });
}

let currentOffset = 0;

document.getElementById("prev-week-btn").addEventListener("click", () => {
  currentOffset += 7;
  const today = new Date();
  const end = new Date(today);
  end.setDate(end.getDate() - currentOffset);
  const start = new Date(end);
  start.setDate(end.getDate() - 6);

  const format = d => d.toISOString().split("T")[0];
  fetchCounts(format(start), format(end));
});

document.addEventListener("DOMContentLoaded", () => {
  fetchCounts();
});