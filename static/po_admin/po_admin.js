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

// const root = 'https://namatji.com/';
const root = 'http://127.0.0.1:8000/';

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
  if (startDate && endDate) url += `?start=${startDate}&end=${endDate}`;

  fetch(url)
    .then(res => res.json())
    .then(data => {
      const count_thead = document.getElementById("count-thead");
      const count_tbody = document.getElementById("body-items");
      const range       = document.getElementById("date-range");

      count_thead.innerHTML = "";
      count_tbody.innerHTML = "";
      range.innerText = `${data.start} ~ ${data.end}`;

      /* ────────────────────────────────────────── */

      const nameMap = {
        main:            "메인페이지",
        search:          "AI 진단하기",
        search_ai_result:"AI 진단 결과",
        inquiry:         "고객 문의",
        board:           "지원사업 게시판",
        board_detail:    "게시판 본문",
        counsel:         "상담 문의",
        ip_total:        "ip단위 조회수",
      };

      /* 날짜 리스트 */
      const dateList = Object.keys(data.counts).sort();

      /* 페이지 종류 수집 */
      const pageSet = new Set();
      for (const counts of Object.values(data.counts))
        for (const t of Object.keys(counts)) pageSet.add(t);

      const pageList        = Array.from(pageSet);
      const translatedPages = pageList.map(t => nameMap[t] || t);

      /* ── HEAD (날짜 + 합계) ───────────────────── */
      const getDayName = d => {
        const dt  = new Date(d);
        const day = ["일","월","화","수","목","금","토"][dt.getDay()];
        return `${dt.toISOString().slice(5,10)}(${day})`;
      };

      let theadRow = `<div class="thead-cell">페이지</div>`;
      for (const d of dateList) theadRow += `<div class="thead-cell">${getDayName(d)}</div>`;
      theadRow += `<div class="thead-cell total-head">1주 합계</div>`;  /* ← 추가 */
      count_thead.innerHTML = `<div class="row">${theadRow}</div>`;

      /* ── BODY (일별 값 + 총합) ────────────────── */
      const totals = data.totals || {};   // 백엔드에서 넘어온 totals

      pageList.forEach((type, idx) => {
        let row = `<div class="cell page-name">${translatedPages[idx]}</div>`;

        for (const d of dateList) {
          const cnt = data.counts[d]?.[type] ?? 0;
          row += `<div class="cell">${cnt}</div>`;
        }

        const sum = totals[type] ?? 0;     /* ← 페이지별 총합 */
        row += `<div class="cell total-cell">${sum}</div>`;

        count_tbody.innerHTML += `<div class="row">${row}</div>`;
      });
    });
}

/* 이전·다음 주 버튼 로직은 그대로 */



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
});

// --------------------------------------------------------------

document.getElementById("save-btn").addEventListener("click", () => {
  const companyName = document.getElementById("company_name").value;
  const region = document.getElementById("region_select").value;
  const region_detail = document.getElementById("region_detail_select").value;
  const startDate = document.getElementById("start_date").value;
  const employeeCount = document.getElementById("employee_count").value;
  const industry = document.getElementById("industry").value;
  const salesForYear = document.getElementById("sales_for_year").value;
  const exportExperience = document.getElementById("export_experience").value;
  const jobDescription = document.getElementById("job_description").value;

  

  const formData = new URLSearchParams();
  formData.append("company_name", companyName);
  formData.append("region", region);
  formData.append("region_detail", region_detail);
  formData.append("start_date", startDate);
  formData.append("employee_count", employeeCount);
  formData.append("industry", industry);
  formData.append("sales_for_year", salesForYear.replace(/,/g, ""));
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
      location.reload();
      
    }
  )
    .catch(err => console.error(err));
});

const custUserTbody = document.querySelector(".cust-user-tbody");
const possibleProductTbody = document.querySelector(".possible-product-tbody");
const possibleProductModal = document.querySelector(".possible-product-modal-wrapper");

custUserTbody.addEventListener("input", function (e) {
  if (!e.target.classList.contains("comma-input")) return;

  const raw = e.target.value.replace(/[^\d]/g, "");
  e.target.value = raw ? raw.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "";
});

custUserTbody.addEventListener("click", (e) => {
  if (e.target.classList.contains("update-btn")) {

    const custUserId = e.target.parentElement.id;

    const tr = document.getElementById(custUserId);

    const companyName = tr.querySelector(`#company_name${custUserId}`);
    const region = tr.querySelector(`#region${custUserId}`);
    const region_detail = tr.querySelector(`#region_detail${custUserId}`);
    const startDate = tr.querySelector(`#start_date${custUserId}`);
    const employeeCount = tr.querySelector(`#employee_count${custUserId}`);
    const industry = tr.querySelector(`#industry${custUserId}`);
    const salesForYear = tr.querySelector(`#sales_for_year${custUserId}`);
    const exportExperience = tr.querySelector(`#export_experience${custUserId}`);
    const jobDescription = tr.querySelector(`#job_description${custUserId}`);
    const updateBtn = tr.querySelector(`.update-btn${custUserId}`);

    companyName.innerHTML = `<input type='text' id='company_name' value='${companyName.innerText}'>`;
    region.innerHTML = `<select id='region_update'>
                          <option value='${region.innerText}' selected>${region.innerText}</option>
                          <option value='서울'>서울</option>
                          <option value='부산'>부산</option>
                          <option value='대구'>대구</option>
                          <option value='인천'>인천</option>
                          <option value='광주'>광주</option>
                          <option value='대전'>대전</option>
                          <option value='울산'>울산</option>
                          <option value='세종'>세종</option>
                          <option value='경기'>경기</option>
                          <option value='강원'>강원</option>
                          <option value='충북'>충북</option>
                          <option value='충남'>충남</option>
                          <option value='전북'>전북</option>
                          <option value='전남'>전남</option>
                          <option value='경북'>경북</option>
                          <option value='경남'>경남</option>
                          <option value='제주'>제주</option>
                        </select>`;
    
   
    region_detail.innerHTML = `<select id='region_detail_update${custUserId}' class='region_detail_update'>
                                  <option value='${region_detail.innerText}' selected>${region_detail.innerText}</option>
                                </select>`;
    

    startDate.innerHTML = `<input type='text' id='start_date' value='${startDate.innerText}'>`;
    employeeCount.innerHTML = `<input type='text' id='employee_count' value='${employeeCount.innerText}'>`;
    industry.innerHTML = `<select id='industry'>
                            <option value='${industry.innerText}' selected>${industry.innerText}</option>
                            <option value='농업, 임업 및 어업'>농업, 임업 및 어업</option>
                            <option value='광업'>광업</option>
                            <option value='제조업'>제조업</option>
                            <option value='전기, 가스, 증기 및 공기 조절 공급업'>전기, 가스, 증기 및 공기 조절 공급업</option>
                            <option value='수도, 하수 및 폐기물 처리, 원료 재생업'>수도, 하수 및 폐기물 처리, 원료 재생업</option>
                            <option value='건설업'>건설업</option>
                            <option value='도매 및 소매업'>도매 및 소매업</option>
                            <option value='운수 및 창고업'>운수 및 창고업</option>
                            <option value='숙박 및 음식점업'>숙박 및 음식점업</option>
                            <option value='정보통신업'>정보통신업</option>
                            <option value='금융 및 보험업'>금융 및 보험업</option>
                            <option value='부동산업'>부동산업</option>
                            <option value='전문, 과학 및 기술 서비스업'>전문, 과학 및 기술 서비스업</option>
                            <option value='사업시설 관리, 사업 지원 및 임대 서비스업'>사업시설 관리, 사업 지원 및 임대 서비스업</option>
                            <option value='교육서비스업'>교육서비스업</option>
                            <option value='보건업 및 사회복지 서비스업'>보건업 및 사회복지 서비스업</option>
                            <option value='예술 스포츠 및 여가관련 서비스업'>예술 스포츠 및 여가관련 서비스업</option>
                            <option value='협회 및 단체, 수리 및 기타 개인서비스업'>협회 및 단체, 수리 및 기타 개인서비스업</option>
                          </select>`;
    salesForYear.innerHTML = `<input type='text' id='sales_for_year_update${custUserId}' class='sales_for_year_update comma-input' value='${salesForYear.innerText}'>`;
    exportExperience.innerHTML = `<select id='export_experience'>
                                    <option value='${exportExperience.innerText}' selected>${exportExperience.innerText}</option>
                                    <option value="있음">있음</option>
                                    <option value="없음">없음</option>
                                    <option value="희망">희망</option>
                                  </select>`;
    jobDescription.innerHTML = `<input type='text' id='job_description' value='${jobDescription.innerText}'>`;

    updateBtn.innerHTML = `저장`;
    updateBtn.classList.add("save-btn");
    updateBtn.classList.remove("update-btn");


  } else if (e.target.classList.contains("possible_product")) {

    const custUserId = e.target.parentElement.id;

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
      .then(datas => {
        console.log(datas);
        possibleProductTbody.innerHTML = "";
        datas.datas.forEach(item => {
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

          if (item.registered_at == datas.today || item.registered_at == datas.yesterday) {
            possibleProductTbody.innerHTML += `
            <tr>
              <td class="today-registered-at">${item.registered_at}</td>
              <td>${item.title}</td>
              <td>${receptionPeriod}</td>
              <td class="possible-product-summary">${item.noti_summary}</td>
              <td><a href="${root}board/detail/${item.pblanc_id}/" target="_blank">본문보기</a></td>
            </tr>
          `;
          }else {
            possibleProductTbody.innerHTML += `
            <tr>
              <td class="other-registered-at">${item.registered_at}</td>
              <td>${item.title}</td>
              <td>${receptionPeriod}</td>
              <td class="possible-product-summary">${item.noti_summary}</td>
              <td><a href="${root}board/detail/${item.pblanc_id}/" target="_blank">본문보기</a></td>
            </tr>
          `;
          }

        });
        possibleProductModal.style.display = "block";
      })
      .catch(err => console.error(err));
    
    
  } else if (e.target.classList.contains("save-btn")) {

    const custUserId = e.target.parentElement.id;

    const formData = new URLSearchParams();

    const companyName = document.getElementById("company_name").value;
    const region = document.getElementById("region_update").value;
    const region_detail = document.getElementById(`region_detail_update${custUserId}`).value;
    const startDate = document.getElementById("start_date").value;
    const employeeCount = document.getElementById("employee_count").value;
    const industry = document.getElementById("industry").value;
    const salesForYear = document.getElementById(`sales_for_year_update${custUserId}`).value;
    const exportExperience = document.getElementById("export_experience").value;
    const jobDescription = document.getElementById("job_description").value;

    console.log(custUserId, companyName, region, region_detail, startDate, employeeCount, industry, salesForYear, exportExperience, jobDescription);

    formData.append("cust_user_id", custUserId);
    formData.append("company_name", companyName);
    formData.append("region", region);
    formData.append("region_detail", region_detail);
    formData.append("start_date", startDate);
    formData.append("employee_count", employeeCount);
    formData.append("industry", industry);
    formData.append("sales_for_year", salesForYear.replace(/,/g, ""));
    formData.append("export_experience", exportExperience);
    formData.append("job_description", jobDescription);

    fetch(`${root}po_admin/cust-user/update/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken")  // 여전히 CSRF는 필요
      },
      body: formData
    }).then(res => res.text()).then(data => {
      location.reload(); 
    }).catch(err => console.error(err));
    

  } else if (e.target.id === "region_select") {

    const region_detail = document.getElementById(`region_detail`);
    const selectedRegion = e.target.value;
    console.log(e.target);

    let detailedArea = [];
    switch (selectedRegion) {
      case "서울":
        detailedArea = seoulList;
        break;
  
      case "인천":
        detailedArea = incheonList;
        break;
  
      case "대전":
        detailedArea = daejeonList;
        break;
  
      case "세종":
        detailedArea = sejongList;
        break;
  
      case "광주":
        detailedArea = gwangjuList;
        break;
  
      case "부산":
        detailedArea = busanList;
        break;
  
      case "대구":
        detailedArea = daeguList;
        break;
  
      case "울산":
        detailedArea = ulsanList;
        break;
  
      case "제주":
        detailedArea = jejuList;
        break;
  
      case "경기":
        detailedArea = gyeonggiList;
        break;
  
      case "강원":
        detailedArea = gangwonList;
        break;
  
      case "충북":
        detailedArea = chungBukList;
        break;
  
      case "충남":
        detailedArea = chungNamList;
        break;
  
      case "전북":
        detailedArea = jeonBukList;
        break;
  
      case "전남":
        detailedArea = jeonNamList;
        break;
  
      case "경북":
        detailedArea = gyeongBukList;
        break;
  
      case "경남":
        detailedArea = gyeongNamList;
        break;

      case "제주":
        detailedArea = jejuList;
        break;
    }

    region_detail.innerHTML = `<select id='region_detail_select'>
                                  ${detailedArea.map(item => `<option value='${item}'>${item}</option>`).join('')}
                                </select>`;
    
  } else if (e.target.id === "region_update") {
    const custUserId = e.target.parentElement.parentElement.id;

    console.log(custUserId);

    const region_detail = document.getElementById(`region_detail${custUserId}`);
    const selectedRegion = e.target.value;
    console.log(e.target);

    let detailedArea = [];
    switch (selectedRegion) {
      case "서울":
        detailedArea = seoulList;
        break;
  
      case "인천":
        detailedArea = incheonList;
        break;
  
      case "대전":
        detailedArea = daejeonList;
        break;
  
      case "세종":
        detailedArea = sejongList;
        break;
  
      case "광주":
        detailedArea = gwangjuList;
        break;
  
      case "부산":
        detailedArea = busanList;
        break;
  
      case "대구":
        detailedArea = daeguList;
        break;
  
      case "울산":
        detailedArea = ulsanList;
        break;
  
      case "제주":
        detailedArea = jejuList;
        break;
  
      case "경기":
        detailedArea = gyeonggiList;
        break;
  
      case "강원":
        detailedArea = gangwonList;
        break;
  
      case "충북":
        detailedArea = chungBukList;
        break;
  
      case "충남":
        detailedArea = chungNamList;
        break;
  
      case "전북":
        detailedArea = jeonBukList;
        break;
  
      case "전남":
        detailedArea = jeonNamList;
        break;
  
      case "경북":
        detailedArea = gyeongBukList;
        break;
  
      case "경남":
        detailedArea = gyeongNamList;
        break;
      
      case "제주":
        detailedArea = jejuList;
        break;
    }

    region_detail.innerHTML = `<select id='region_detail_update${custUserId}'>
                                  ${detailedArea.map(item => `<option value='${item}'>${item}</option>`).join('')}
                                </select>`;

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

// 컴마 추가 함수
function addCommas(numStr) {
  return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// 숫자만 추출 함수
function uncomma(str) {
  return str.replace(/[^\d]/g, "");
}

// 이벤트 연결
document.getElementById("sales_for_year").addEventListener("input", function (e) {
  const val = uncomma(e.target.value); // 숫자만 남기기
  if (val === "") {
    e.target.value = "";
    return;
  }
  e.target.value = addCommas(val); // 컴마 붙여서 다시 세팅
});

document.getElementById("writer-filter").addEventListener("change", function () {
  const writer = this.value;                     // "po_admin" or "all"
  const url    = new URL(window.location.href);

  if (writer === "all") {
    url.searchParams.delete("writer");           // 전체 보기
  } else {
    url.searchParams.set("writer", writer);      // 선택한 작성자
  }
  window.location.href = url.toString();         // 새로고침
});

document.getElementById("industry-filter").addEventListener("change", function () {
  const industry = this.value;
  const url = new URL(window.location.href);
  
  if (industry === "all") {
    url.searchParams.delete("industry");
  } else {
    url.searchParams.set("industry", industry);
  }
  window.location.href = url.toString();
});

document.getElementById("region-filter").addEventListener("change", function () {
  const region = this.value;
  const url = new URL(window.location.href);

  console.log(region);

  if (region === "all") {
    url.searchParams.delete("region");
    url.searchParams.delete("region_detail");
  } else {
    url.searchParams.set("region", region);
  }
  window.location.href = url.toString();
});

document.getElementById("region-detail-filter").addEventListener("change", function () {
  const region_detail = this.value;
  const url = new URL(window.location.href);

  if (region_detail === "all") {
    url.searchParams.delete("region_detail");
  } else {
    url.searchParams.set("region_detail", region_detail);
  }
  window.location.href = url.toString();
});

document.getElementById("export-experience-filter").addEventListener("change", function () {
  const export_experience = this.value;
  const url = new URL(window.location.href);

  if (export_experience === "all") {
    url.searchParams.delete("export_experience");
  } else {
    url.searchParams.set("export_experience", export_experience);
  }
  window.location.href = url.toString();
});



// ------------------------------------------------------------

// ---------------------------고객 정보 삭제----------------------------------
document.getElementById("cust-user-delete-btn").addEventListener("click", function (e) {
  document.querySelectorAll(".cust-user-tr").forEach(tr => {
    tr.classList.add("cust-user-tr-hover");
  });
  const custUserId = [];
  e.target.innerText = "선택된 고객 정보 삭제";
  const tBody = document.querySelector(".cust-user-tbody");
  tBody.addEventListener("click", function (f) {

    const id = f.target.parentElement.id;
    const index = custUserId.indexOf(id);

    if (index !== -1) {
      // 이미 있다면 제거
      custUserId.splice(index, 1);
      f.target.parentElement.classList.remove("cust-user-tr-red");
    } else {
      // 없으면 추가
      custUserId.push(id);
      f.target.parentElement.classList.add("cust-user-tr-red");
    }

  });

  e.target.addEventListener("click", function () {
    console.log(custUserId);
    fetch(`${root}po_admin/cust-user/delete/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        cust_user_ids: custUserId
      })
    }).then(res => res.json()).then(data => {
      location.reload();
    }).catch(err => console.error(err));
  });

});

// --------------------직원 수 올름 내림차순-----------------------------
const employeeCountTh = document.querySelector(".employee-count-th");

employeeCountTh.addEventListener("click", function () {

  if (employeeCountTh.innerText === "사원수 △") {
    const url = new URL(window.location.href);
    url.searchParams.set("employee_count", "asc");
    window.location.href = url.toString();
  } else {
    const url = new URL(window.location.href);
    url.searchParams.set("employee_count", "desc");
    window.location.href = url.toString();
  }

  
});

// ------------------------------------------------------------
document.getElementById("file-input").addEventListener("change", function (e) {
  const file = e.target.files[0];
  const formData = new FormData();
  formData.append("file", file);

  fetch(`${root}po_admin/cust-user/upload/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: formData
  }).then(res => res.text()).then(data => {
    console.log(data);
    location.reload();
  }).catch(err => console.error(err));
});

// 초기화 버튼
document.getElementById("cust-user-reset-btn").addEventListener("click", function () {
  const url = new URL(window.location.href);
  url.searchParams.delete("writer");
  url.searchParams.delete("industry");
  url.searchParams.delete("region");
  url.searchParams.delete("region_detail");
  url.searchParams.delete("export_experience");
  url.searchParams.delete("employee_count");
  window.location.href = url.toString();
});
