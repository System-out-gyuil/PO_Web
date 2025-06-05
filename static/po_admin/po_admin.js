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
  let root = 'https://namatji.com';
  let url = `${root}/po_admin/counts-by-date/`;
  if (startDate && endDate) {
    url += `?start=${startDate}&end=${endDate}`;
  }

  fetch(url)
    .then(res => res.json())
    .then(data => {
      const count_thead = document.getElementById('count-thead');
      const count_tbody = document.getElementById('body-items');
      const range = document.getElementById('date-range');

      count_thead.innerHTML = '';
      count_tbody.innerHTML = '';
      range.innerText = `${data.start} ~ ${data.end}`;

      const nameMap = {
        main: "메인페이지",
        search: "AI 진단하기",
        search_ai_result: "AI 진단 결과",
        inquiry: "고객 문의",
        board: "지원사업 게시판",
        board_detail: "게시판 본문",
        counsel: "상담 문의",
        ip_total: "ip단위 조회수"  // ✅ 추가됨
      };

      const dateList = Object.keys(data.counts).sort();
      const pageSet = new Set();

      // ✅ 전체 페이지 종류 수집
      for (const counts of Object.values(data.counts)) {
        for (const type of Object.keys(counts)) {
          pageSet.add(type);
        }
      }

      const pageList = Array.from(pageSet);
      const translatedPages = pageList.map(type => nameMap[type] || type);

      // ✅ Thead 구성
      const getDayName = (dateString) => {
        const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
        const dateObj = new Date(dateString);
        const day = dateObj.getDay();
        const mmdd = dateObj.toISOString().slice(5, 10);
        return `${mmdd}(${dayNames[day]})`;
      };

      let theadRow = `<div class="thead-cell">페이지</div>`;
      for (const date of dateList) {
        theadRow += `<div class="thead-cell">${getDayName(date)}</div>`;
      }
      count_thead.innerHTML = `<div class="row">${theadRow}</div>`;

      // ✅ Body 구성
      for (let i = 0; i < pageList.length; i++) {
        const type = pageList[i];
        const translated = translatedPages[i];

        let row = `<div class="cell page-name">${translated}</div>`;
        for (const date of dateList) {
          const count = data.counts[date]?.[type] || 0;
          row += `<div class="cell">${count}</div>`;
        }

        count_tbody.innerHTML += `<div class="row">${row}</div>`;
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

document.getElementById("next-week-btn").addEventListener("click", () => {
  if (currentOffset <= 0) return; // 오늘 이후는 못 넘게 제한

  currentOffset -= 7;

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
  console.log("DOMContentLoaded");
});