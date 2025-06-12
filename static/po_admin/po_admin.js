const counselWrapper = document.querySelector('.counsel-wrapper');
const inquiryWrapper = document.querySelector('.inquiry-wrapper');
const countWrapper = document.querySelector('.count-wrapper');
const kakaoWrapper = document.querySelector('.kakao-wrapper');
const counselNavItem = document.querySelector('.counsel-nav-item');
const inquiryNavItem = document.querySelector('.inquiry-nav-item');
const countNavItem = document.querySelector('.count-nav-item');
const kakaoNavItem = document.querySelector('.kakao-nav-item');
const custUserNavItem = document.querySelector('.cust-user-nav-item');
const custUserWrapper = document.querySelector('.cust-user-wrapper');

const root = 'https://namatji.com/';
// const root = 'http://127.0.0.1:8000/';

// 모든 섹션 숨기기
function hideAllSections() {
  counselWrapper.style.display = 'none';
  inquiryWrapper.style.display = 'none';
  countWrapper.style.display = 'none';
  kakaoWrapper.style.display = 'none';
  custUserWrapper.style.display = 'none';
}

// 모든 탭 비활성화
function clearActiveTabs() {
  counselNavItem.classList.remove('active');
  inquiryNavItem.classList.remove('active');
  countNavItem.classList.remove('active');
  kakaoNavItem.classList.remove('active');
  custUserNavItem.classList.remove('active');
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

// 카카오 회원
kakaoNavItem.addEventListener('click', () => {
  hideAllSections();
  clearActiveTabs();
  kakaoWrapper.style.display = 'flex';
  kakaoNavItem.classList.add('active');
});

custUserNavItem.addEventListener('click', () => {
  hideAllSections();
  clearActiveTabs();
  custUserWrapper.style.display = 'flex';
  custUserNavItem.classList.add('active');
});
// 초기 상태 설정 (처음에 상담 신청 리스트만 표시)
document.addEventListener('DOMContentLoaded', () => {
  hideAllSections();
  custUserWrapper.style.display = 'flex';
  custUserNavItem.classList.add('active');
});

function fetchCounts(startDate = null, endDate = null) {

  let url = `${root}po_admin/counts-by-date/`;
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

// --------------------------------------------------------------

document.getElementById("save-btn").addEventListener("click", () => {
  const companyName = document.getElementById("company_name").value;
  const region = document.getElementById("region").value;
  const startDate = document.getElementById("start_date").value;
  const employeeCount = document.getElementById("employee_count").value;
  const industry = document.getElementById("industry").value;
  const salesForYear = document.getElementById("sales_for_year").value;
  const exportExperience = document.getElementById("export_experience").value;
  const jobDescription = document.getElementById("job_description").value;

  const formData = new URLSearchParams();
  formData.append("company_name", companyName);
  formData.append("region", region);
  formData.append("start_date", startDate);
  formData.append("employee_count", employeeCount);
  formData.append("industry", industry);
  formData.append("sales_for_year", salesForYear);
  formData.append("export_experience", exportExperience);
  formData.append("job_description", jobDescription);

  fetch(`${root}po_admin/cust-user/save/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken")  // 여전히 CSRF는 필요
    },
    body: formData
  }).then(res => res.text())
    .then(data => {
      console.log(data);
      location.reload();
      
    }
  )
    .catch(err => console.error(err));
});

const custUserTbody = document.querySelector(".cust-user-tbody");
const possibleProductTbody = document.querySelector(".possible-product-tbody");
const possibleProductModal = document.querySelector(".possible-product-modal-wrapper");

custUserTbody.addEventListener("click", (e) => {
  console.log(e.target);
  if (e.target.classList.contains("update-btn")) {
    const custUserId = e.target.parentElement.id;
    const companyName = e.target.parentElement.querySelector(`#company_name${custUserId}`).value;
    const region = e.target.parentElement.querySelector(`#region${custUserId}`).value;
    const startDate = e.target.parentElement.querySelector(`#start_date${custUserId}`).value;
    const employeeCount = e.target.parentElement.querySelector(`#employee_count${custUserId}`).value;
    const industry = e.target.parentElement.querySelector(`#industry${custUserId}`).value;
    const salesForYear = e.target.parentElement.querySelector(`#sales_for_year${custUserId}`).value;
    const exportExperience = e.target.parentElement.querySelector(`#export_experience${custUserId}`).value;
    const jobDescription = e.target.parentElement.querySelector(`#job_description${custUserId}`).value;

    console.log(companyName, region, startDate, employeeCount, industry, salesForYear, exportExperience, jobDescription);

    const formData = new URLSearchParams();
    formData.append("cust_user_id", custUserId);
    formData.append("company_name", companyName);
    formData.append("region", region);
    formData.append("start_date", startDate);
    formData.append("employee_count", employeeCount);
    formData.append("industry", industry);
    formData.append("sales_for_year", salesForYear);
    formData.append("export_experience", exportExperience);
    formData.append("job_description", jobDescription);

    fetch(`${root}po_admin/cust-user/update/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken")  // 여전히 CSRF는 필요
      },
      body: formData
    }).then(res => res.text()).then(data => {
      console.log(data);
      // location.reload();
    }).catch(err => console.error(err));

  } else if (e.target.classList.contains("possible_product")) {

    const custUserId = e.target.parentElement.parentElement.id;
    console.log(custUserId);

    const formData = new URLSearchParams();
    formData.append("cust_user_id", custUserId);

    fetch(`${root}po_admin/cust-user/possible-product/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken")  // 여전히 CSRF는 필요
      },
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        console.log(data);
        possibleProductTbody.innerHTML = "";
        data.data.forEach(item => {
          item.reception_start = item.reception_start === "1900-01-01" ? "" : item.reception_start;
          item.reception_end = item.reception_end === "9999-12-31" ? "상시접수" : item.reception_end;

          let receptionPeriod = "";

          if (item.reception_end === "상시접수") {
            receptionPeriod = "상시접수";
          } else if (item.reception_start === "") {
            receptionPeriod = item.reception_end;
          } else {
            receptionPeriod = `${item.reception_start} ~ ${item.reception_end}`;
          }

          possibleProductTbody.innerHTML += `
            <tr>
              <td>${item.title}</td>
              <td>${receptionPeriod}</td>
              <td class="possible-product-summary">${item.noti_summary}</td>
              <td><a href="${root}board/detail/${item.pblanc_id}/" target="_blank">본문보기</a></td>
            </tr>
          `;
        });
        possibleProductModal.style.display = "block";
      })
      .catch(err => console.error(err));
  }
});

window.addEventListener("click", function (event) {
  if (event.target === possibleProductModal) {
    possibleProductModal.style.display = "none";
  }
});



function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');