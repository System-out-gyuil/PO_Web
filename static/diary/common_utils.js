function getCsrfToken() {
  const cookieValue = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
  return cookieValue || '';
}

function hexToRgba(hex, alpha) {
  if (!hex) return `rgba(238, 238, 238, ${alpha})`;
  
  // # 제거
  hex = hex.replace('#', '');
  
  // 3자리 hex를 6자리로 변환
  if (hex.length === 3) {
      hex = hex.split('').map(char => char + char).join('');
  }
  
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

let dropdown = null;
let dropdownCloseHandler = null;

function closeDropdown() {
    console.log('closeDropdown 호출됨');
    console.log('현재 상태:', {
        localDropdown: dropdown,
        windowDropdown: window.dropdown,
        localHandler: dropdownCloseHandler,
        windowHandler: window.dropdownCloseHandler
    });
    
    // 로컬 dropdown 변수 정리 (지역/상세지역 드롭다운 제외)
    if (dropdown && dropdown.parentNode && !dropdown.hasAttribute('data-region-type')) {
        console.log('로컬 dropdown 제거');
        dropdown.parentNode.removeChild(dropdown);
        dropdown = null;
    }
    
    // 전역 window.dropdown 변수 정리 (지역/상세지역 드롭다운 제외)
    if (window.dropdown && window.dropdown.parentNode && !window.dropdown.hasAttribute('data-region-type')) {
        console.log('전역 dropdown 제거');
        window.dropdown.parentNode.removeChild(window.dropdown);
        window.dropdown = null;
    }
    
    // 모달 드롭다운만 제거 (일반 드롭다운은 유지, 지역/상세지역 드롭다운 제외)
    const modalDropdowns = document.querySelectorAll('.dropdown-edit[data-modal="true"]:not([data-region-type])');
    if (modalDropdowns.length > 0) {
        console.log('모달 드롭다운 요소들 제거:', modalDropdowns.length);
        modalDropdowns.forEach(function(element) {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        });
    }
    
    // 일반 드롭다운 제거 (지역/상세지역 드롭다운 제외)
    const regularDropdowns = document.querySelectorAll('.dropdown-edit:not([data-region-type]):not([data-modal="true"])');
    if (regularDropdowns.length > 0) {
        console.log('일반 드롭다운 요소들 제거:', regularDropdowns.length);
        regularDropdowns.forEach(function(element) {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        });
    }
    
    // 이벤트 리스너 정리 - 로컬
    if (dropdownCloseHandler) {
        console.log('로컬 이벤트 리스너 제거');
        document.removeEventListener('click', dropdownCloseHandler);
        document.removeEventListener('mousedown', dropdownCloseHandler);
        dropdownCloseHandler = null;
    }
    
    // 이벤트 리스너 정리 - 전역
    if (window.dropdownCloseHandler) {
        console.log('전역 이벤트 리스너 제거');
        document.removeEventListener('click', window.dropdownCloseHandler);
        document.removeEventListener('mousedown', window.dropdownCloseHandler);
        window.dropdownCloseHandler = null;
    }
    
    console.log('closeDropdown 완료');
}

// 한국어 단위로 변환하는 함수 (백만 단위 기준)
function formatToKoreanCurrency(amount) {
    console.log(123)
  if (!amount || amount === 0) return '0원';
  
  const numAmount = typeof amount === 'string' ? parseInt(amount.replace(/[^\d]/g, '')) : amount;
  if (isNaN(numAmount) || numAmount === 0) return '0원';
  
  let result = '';
  let remaining = numAmount;
  
  // 백만 단위 이상인지 확인
  const isOverBaekman = remaining >= 1000000;
  
  // 억 단위 처리
  if (remaining >= 100000000) {
      const eok = Math.floor(remaining / 100000000);
      result += eok + '억';
      remaining = remaining % 100000000;
  }
  
  // 천만 단위 처리 (천으로 표시)
  if (remaining >= 10000000) {
      const cheon = Math.floor(remaining / 10000000);
      result += ' ' + cheon + '천';
      remaining = remaining % 10000000;
  }
  
  // 백만 단위 처리
  if (remaining >= 1000000) {
      const baek = Math.floor(remaining / 1000000);
      result += ' ' + baek + '백';
      remaining = remaining % 1000000;
  }
  
  // 천만이나 백만 단위가 있으면 '만원'으로 끝냄
  if (result.includes('천') || result.includes('백')) {
      return result + '만원';
  }
  // 억 단위만 있으면 '원'으로 끝냄
  else if (result && result.includes('억')) {
      return result + '원';
  }
  // 백만 단위 이상이면 '만원'으로 끝냄
  else if (isOverBaekman) {
      return result + '만원';
  }
  
  // 백만 단위 이하일 때는 만 단위까지 표시
  if (remaining >= 10000) {
      if (!result) {  // 앞에 억/천/백이 없을 때만
          result = Math.floor(remaining / 10000) + '만';
      } else {
          // 앞에 억/천/백이 있을 때는 만 단위가 0이 아닐 때만 추가
          if (Math.floor(remaining / 10000) > 0) {
              result += Math.floor(remaining / 10000) + '만';
          }
      }
      remaining = remaining % 10000;
  }
  
  // 10,000 미만의 값은 그대로 표시
  if (remaining > 0 && remaining < 10000) {
      if (result) {
          result += remaining;
      } else {
          result = remaining.toString();
      }
  }
  
  return result + '원';
}

// 한국어 단위를 숫자로 변환하는 함수
function parseKoreanCurrency(value) {
  if (!value || value === '') return 0;
  
  const str = value.toString().replace(/[원,\s]/g, '');
  
  // 이미 숫자인 경우
  if (/^\d+$/.test(str)) {
      return parseInt(str);
  }
  
  let result = 0;
  let temp = 0;
  
  // 억 단위 처리
  const 억Match = str.match(/(\d+)억/);
  if (억Match) {
      result += parseInt(억Match[1]) * 100000000;
  }
  
  // 나머지 부분 처리
  let remaining = str.replace(/\d+억/, '');
  
  // 천만, 백만, 십만, 만 단위 처리
  const 천만Match = remaining.match(/(\d+)천만/);
  if (천만Match) {
      temp += parseInt(천만Match[1]) * 10000000;
      remaining = remaining.replace(/\d+천만/, '');
  }
  
  const 백만Match = remaining.match(/(\d+)백만/);
  if (백만Match) {
      temp += parseInt(백만Match[1]) * 1000000;
      remaining = remaining.replace(/\d+백만/, '');
  }
  
  const 십만Match = remaining.match(/(\d+)십만/);
  if (십만Match) {
      temp += parseInt(십만Match[1]) * 100000;
      remaining = remaining.replace(/\d+십만/, '');
  }
  
  const 만Match = remaining.match(/(\d+)만/);
  if (만Match) {
      temp += parseInt(만Match[1]) * 10000;
      remaining = remaining.replace(/\d+만/, '');
  }
  
  // 천, 백, 십, 일 단위 처리
  const 천Match = remaining.match(/(\d+)천/);
  if (천Match) {
      temp += parseInt(천Match[1]) * 1000;
      remaining = remaining.replace(/\d+천/, '');
  }
  
  const 백Match = remaining.match(/(\d+)백/);
  if (백Match) {
      temp += parseInt(백Match[1]) * 100;
      remaining = remaining.replace(/\d+백/, '');
  }
  
  const 십Match = remaining.match(/(\d+)십/);
  if (십Match) {
      temp += parseInt(십Match[1]) * 10;
      remaining = remaining.replace(/\d+십/, '');
  }
  
  // 남은 숫자 처리
  if (remaining && /^\d+$/.test(remaining)) {
      temp += parseInt(remaining);
  }
  
  return result + temp;
}

// 콤마 제거하고 숫자 값 반환하는 함수
function removeCommaFromNumber(value) {
  if (!value || value === '') return '';
  return value.toString().replace(/[,]/g, '');
}

// 브라우저 알림 표시 함수 (크롬 아이콘 깜빡임)
function showBrowserNotification(message, title = '알림') {
    // 브라우저 알림 권한 확인 및 요청 (포커스 상태와 관계없이 실행)
    if ('Notification' in window) {
        if (Notification.permission === 'granted') {
            try {
                // 알림 생성 (크롬 아이콘 깜빡임 효과)
                const browserNotification = new Notification(title, {
                    body: message,
                    // favicon 오류 방지를 위해 icon 제거 또는 기본값 사용
                    tag: 'important-notification', // 중복 알림 방지
                    requireInteraction: false,
                    silent: true // 소리 없이
                });
                
                // 5초 후 알림 자동 닫기
                setTimeout(() => {
                    browserNotification.close();
                }, 5000);
            } catch (error) {
                console.log('브라우저 알림 생성 중 오류:', error);
            }
            
        } else if (Notification.permission !== 'denied') {
            // 권한 요청
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    try {
                        const browserNotification = new Notification(title, {
                            body: message,
                            // favicon 오류 방지를 위해 icon 제거
                            tag: 'important-notification',
                            requireInteraction: false,
                            silent: true
                        });
                        
                        setTimeout(() => {
                            browserNotification.close();
                        }, 5000);
                    } catch (error) {
                        console.log('브라우저 알림 생성 중 오류:', error);
                    }
                }
            });
        }
    }
}

// 알림 표시 함수 (기존에 없다면 추가)
function showNotification(message, type = 'info', important = false) {
    console.log("show noti 호출됨", { message, type, important });
    
  // 기존 알림 제거 로직 개선
  if (important) {
      // important 알림인 경우: 일반 알림만 제거 (important 알림은 유지)
      const regularNotifications = document.querySelectorAll('.notification:not([data-important="true"])');
      console.log("일반 알림 개수:", regularNotifications.length);
      regularNotifications.forEach(notification => notification.remove());
  } else {
      // 일반 알림인 경우: 모든 알림 제거
      const existingNotifications = document.querySelectorAll('.notification');
      console.log("기존 알림 개수:", existingNotifications.length);
      existingNotifications.forEach(notification => notification.remove());
  }
  
  const notification = document.createElement('div');
  notification.className = 'notification';
  
  // important 알림 표시
  if (important) {
      notification.setAttribute('data-important', 'true');
  }
  
  console.log("알림 요소 생성됨:", notification);
  
  notification.style.cssText = `
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      padding: 12px 20px;
      border-radius: 6px;
      color: white;
      font-weight: bold;
      z-index: 10000;
      max-width: 500px;
      word-wrap: break-word;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      animation: slideIn 0.3s ease;
      text-align: center;
  `;
  
  // 메시지 설정
  notification.textContent = message;
  console.log("메시지 설정됨:", message);
  
  // important일 때만 특별한 처리
  if (important) {
      console.log("important=true 처리 시작");
      notification.style.paddingRight = '40px';
      notification.style.position = 'absolute';
      
      const closeButton = document.createElement('span');
      closeButton.innerHTML = '&times;';
      closeButton.style.cssText = `
          position: absolute;
          top: 8px;
          right: 12px;
          font-size: 20px;
          cursor: pointer;
          color: white;
          font-weight: bold;
          line-height: 1;
      `;
      closeButton.onclick = function() {
          if (notification.parentNode) {
              notification.style.animation = 'slideOut 0.3s ease';
              setTimeout(() => {
                  if (notification.parentNode) {
                      notification.remove();
                  }
              }, 300);
          }
      };
      notification.appendChild(closeButton);
      console.log("X 버튼 추가됨");
      
      // important일 때 브라우저 알림도 시도 (오류가 있어도 페이지 내 알림은 표시됨)
      try {
          console.log("브라우저 알림 호출 시작");
          showBrowserNotification(message, '알림');
          console.log("브라우저 알림 호출 완료");
      } catch (error) {
          console.log('브라우저 알림 오류:', error);
      }
  }
  
  // 타입별 스타일 설정
  switch (type) {
      case 'success':
          notification.style.background = '#28a745';
          break;
      case 'error':
          notification.style.background = '#dc3545';
          break;
      case 'warning':
          notification.style.background = '#ffc107';
          notification.style.color = '#333';
          break;
      default:
          notification.style.background = '#17a2b8';
  }
  console.log("스타일 설정 완료, 배경색:", notification.style.background);
  
  console.log("DOM에 추가하기 전 body 확인:", document.body);
  document.body.appendChild(notification);
  console.log("DOM에 추가 완료, 현재 알림 요소:", notification);
  console.log("현재 DOM의 .notification 요소들:", document.querySelectorAll('.notification'));
  
  // important가 아닐 때만 자동 제거
  if (!important) {
      console.log("자동 제거 타이머 설정");
      // 3초 후 자동 제거
      setTimeout(() => {
          if (notification.parentNode) {
              notification.style.animation = 'slideOut 0.3s ease';
              setTimeout(() => {
                  if (notification.parentNode) {
                      notification.remove();
                  }
              }, 300);
          }
      }, 3000);
  } else {
      console.log("important=true이므로 자동 제거 안함");
  }
  
  // CSS 애니메이션 추가
  if (!document.getElementById('notification-styles')) {
      console.log("CSS 애니메이션 스타일 추가");
      const style = document.createElement('style');
      style.id = 'notification-styles';
      style.textContent = `
          @keyframes slideIn {
              from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
              to { transform: translateX(-50%) translateY(0); opacity: 1; }
          }
          @keyframes slideOut {
              from { transform: translateX(-50%) translateY(0); opacity: 1; }
              to { transform: translateX(-50%) translateY(-100%); opacity: 0; }
          }
      `;
      document.head.appendChild(style);
  } else {
      console.log("CSS 애니메이션 스타일 이미 존재함");
  }
}

// 지역별 상세지역 매핑 함수
function getSubregions(region) {
  const regionMap = {
    "서울": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
    "경기": ["수원시", "성남시", "의정부시", "안양시", "부천시", "광명시", "평택시", "동두천시", "안산시", "고양시", "과천시", "구리시", "남양주시", "오산시", "시흥시", "군포시", "의왕시", "하남시", "용인시", "파주시", "이천시", "안성시", "김포시", "화성시", "광주시", "여주시", "양평군", "연천군", "포천시", "가평군", "양주시"],
    "인천": ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"],
    "강원": ["춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시", "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군", "양구군", "인제군", "고성군", "양양군"],
    "경북": ["포항시", "경주시", "김천시", "안동시", "구미시", "영주시", "영천시", "상주시", "문경시", "경산시", "군위군", "의성군", "청송군", "영양군", "영덕군", "청도군", "고령군", "성주군", "칠곡군", "예천군", "봉화군", "울진군", "울릉군"],
    "경남": ["창원시", "진주시", "통영시", "사천시", "김해시", "밀양시", "거제시", "양산시", "의령군", "함안군", "창녕군", "고성군", "남해군", "하동군", "산청군", "함양군", "거창군", "합천군"],
    "부산": ["중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"],
    "대구": ["중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군"],
    "울산": ["중구", "남구", "동구", "북구", "울주군"],
    "대전": ["중구", "동구", "서구", "유성구", "대덕구"],
    "충북": ["청주시", "충주시", "제천시", "보은군", "옥천군", "영동군", "증평군", "진천군", "괴산군", "음성군", "단양군"],
    "충남": ["천안시", "공주시", "보령시", "아산시", "서산시", "논산시", "계룡시", "당진시", "금산군", "부여군", "서천군", "청양군", "홍성군", "예산군", "태안군"],
    "전북": ["전주시", "군산시", "익산시", "정읍시", "남원시", "김제시", "완주군", "진안군", "무주군", "장수군", "임실군", "순창군", "고창군", "부안군"],
    "전남": ["목포시", "여수시", "순천시", "나주시", "광양시", "담양군", "곡성군", "구례군", "고흥군", "보성군", "화순군", "장흥군", "강진군", "해남군", "영암군", "무안군", "함평군", "영광군", "장성군", "완도군", "진도군", "신안군"],
    "광주": ["동구", "서구", "남구", "북구", "광산구"],
    "제주": ["제주시", "서귀포시"],
    "세종": ["세종특별자치시"]
  };
  
  return regionMap[region] || [];
}
