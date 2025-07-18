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
    
    // 로컬 dropdown 변수 정리
    if (dropdown && dropdown.parentNode) {
        console.log('로컬 dropdown 제거');
        dropdown.parentNode.removeChild(dropdown);
        dropdown = null;
    }
    
    // 전역 window.dropdown 변수 정리
    if (window.dropdown && window.dropdown.parentNode) {
        console.log('전역 dropdown 제거');
        window.dropdown.parentNode.removeChild(window.dropdown);
        window.dropdown = null;
    }
    
    // 모든 dropdown-edit 클래스 요소들 제거 (혹시 남아있는 것들)
    const remainingDropdowns = document.querySelectorAll('.dropdown-edit');
    if (remainingDropdowns.length > 0) {
        console.log('남아있는 드롭다운 요소들 제거:', remainingDropdowns.length);
        remainingDropdowns.forEach(function(element) {
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

// 한국어 단위로 변환하는 함수
function formatToKoreanCurrency(amount) {
    console.log(123)
  if (!amount || amount === 0) return '0원';
  
  const numAmount = typeof amount === 'string' ? parseInt(amount.replace(/[^\d]/g, '')) : amount;
  if (isNaN(numAmount) || numAmount === 0) return '0원';
  
  let result = '';
  let remaining = numAmount;
  
  // 억 단위 처리
  if (remaining >= 100000000) {
      const eok = Math.floor(remaining / 100000000);
      result += eok + '억';
      remaining = remaining % 100000000;
  }
  
  // 천만 단위 처리 (천으로 표시)
  if (remaining >= 10000000) {
      const cheon = Math.floor(remaining / 10000000);
      if (result) result += ' ';
      result += cheon + '천';
      remaining = remaining % 10000000;
  }
  
  // 백만 단위 처리
  if (remaining >= 1000000) {
      const baek = Math.floor(remaining / 1000000);
      if (result) result += ' ';
      result += baek + '백';
      remaining = remaining % 1000000;
  }
  
  // 만 단위가 남아있으면 추가
  if (remaining >= 10000) {
      if (result) result += '만';
      else result = Math.floor(remaining / 10000) + '만';
  } else if (result) {
      result += '만';
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

// 알림 표시 함수 (기존에 없다면 추가)
function showNotification(message, type = 'info') {
  // 기존 알림 제거
  const existingNotifications = document.querySelectorAll('.notification');
  existingNotifications.forEach(notification => notification.remove());
  
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 6px;
      color: white;
      font-weight: bold;
      z-index: 10000;
      max-width: 300px;
      word-wrap: break-word;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      animation: slideIn 0.3s ease;
  `;
  
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
  
  notification.textContent = message;
  document.body.appendChild(notification);
  
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
  
  // CSS 애니메이션 추가
  if (!document.getElementById('notification-styles')) {
      const style = document.createElement('style');
      style.id = 'notification-styles';
      style.textContent = `
          @keyframes slideIn {
              from { transform: translateX(100%); opacity: 0; }
              to { transform: translateX(0); opacity: 1; }
          }
          @keyframes slideOut {
              from { transform: translateX(0); opacity: 1; }
              to { transform: translateX(100%); opacity: 0; }
          }
      `;
      document.head.appendChild(style);
  }
}

// 지역별 상세지역 매핑 함수
function getSubregions(region) {
  const regionMap = {
    '서울': ['관악구','금천구','강남구','강서구','강동구','강북구','광진구','구로구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'],
    '경기': ['수원시','고양시','성남시','용인시','부천시','안산시','안양시','남양주시','화성시','평택시','의정부시','시흥시','파주시','광명시','김포시','군포시','광주시','오산시','이천시','안성시','의왕시','하남시','여주시','양평군','동두천시','과천시','가평군','연천군'],
    '인천': ['계양구', '남동구', '동구', '미추홀구', '부평구', '서구', '연수구', '중구', '강화군', '옹진군'],
    '경북': ['경주시', '포항시', '김천시', '안동시', '구미시', '영주시', '영천시', '상주시', '문경시', '경산시', '군위군', '의성군', '청송군', '영양군', '영덕군', '청도군', '고령군', '성주군', '칠곡군', '예천군', '봉화군', '울진군', '울릉군'],
    '경남': ['창원시','진주시','통영시','사천시','김해시','밀양시','거제시','양산시','의령군','함안군','창녕군','고성군','남해군','하동군','산청군','함양군','거창군','합천군'],
    '대구': ['중구','동구','서구','남구','북구','수성구','달서구','달성군'],
    '부산': ['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'],
    '광주': ['동구','서구','남구','북구','광산구'],
    '대전': ['동구','중구','서구','유성구','대덕구'],
    '울산': ['중구','남구','동구','북구','울주군'],
    '세종': ['세종특별자치시'],
    '강원': ['춘천시','원주시','강릉시','동해시','태백시','속초시','삼척시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','고성군','양양군'],
    '충북': ['청주시','충주시','제천시','보은군','옥천군','영동군','증평군','진천군','괴산군','음성군','단양군'],
    '충남': ['천안시','공주시','보령시','아산시','서산시','논산시','계룡시','당진시','금산군','부여군','서천군','청양군','홍성군','예산군','태안군'],
    '전북': ['전주시','군산시','익산시','정읍시','남원시','김제시','완주군','진안군','무주군','장수군','임실군','순창군','고창군','부안군'],
    '전남': ['목포시','여수시','순천시','나주시','광양시','담양군','곡성군','구례군','고흥군','보성군','화순군','장흥군','강진군','해남군','영암군','무안군','함평군','영광군','장성군','완도군','진도군','신안군'],
  };
  
  return regionMap[region] || [];
}
