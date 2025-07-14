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

// 숫자에 콤마 추가하는 함수
function formatNumberWithComma(value) {
    console.log('formatNumberWithComma 호출됨:', value);
    if (!value && value !== 0) return '';
    const num = typeof value === 'string' ? parseInt(value.replace(/[^\d]/g, '')) : value;
    if (isNaN(num)) return '';
    return num.toLocaleString();
}

// 한국어 단위로 변환하는 함수
function formatToKoreanCurrency(amount) {
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

// 드롭다운 외부 클릭 이벤트 설정 함수
function setupDropdownCloseHandler(dropdownElement) {
    closeDropdown(); // 기존 드롭다운 먼저 닫기
    
    dropdownCloseHandler = function(e) {
        if (dropdownElement && !dropdownElement.contains(e.target)) {
            closeDropdown();
        }
    };
    
    // click과 mousedown 모두 처리
    setTimeout(() => {
        document.addEventListener('click', dropdownCloseHandler);
        document.addEventListener('mousedown', dropdownCloseHandler);
    }, 100);
}

function refreshKanban() {
    fetch('/').then(r=>r.text()).then(html=>{
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const newBoard = temp.querySelector('#boardView');
        if (newBoard) {
            document.getElementById('boardView').innerHTML = newBoard.innerHTML;
            bindKanbanSortable(); // 드래그 기능 복구
        }
    });
}

function hexToRgba(hex, alpha) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(x => x + x).join('');
  const r = parseInt(hex.substring(0,2), 16);
  const g = parseInt(hex.substring(2,4), 16);
  const b = parseInt(hex.substring(4,6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}


function updateEntryField(id, field, value) {
  fetch('/600/update/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'id='+encodeURIComponent(id)+'&field='+encodeURIComponent(field)+'&value='+encodeURIComponent(value)
  })
  .then(r=>r.json())
  .then(function(data){
      if(!data.success) {
          alert('수정 실패: '+(data.error||''));
          return;
      }
      // 항상 최신 entry로 모달/테이블/보드 동기화
      return fetch('/600/update/?id='+id);
  })
  .then(r => r ? r.json() : null)
  .then(function(data){
      if(data && data.success && data.entry) {
          showDetailModal(data.entry);
          updateTableRow(data.entry);
          // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
          if (window.kanbanAttribute && field === window.kanbanAttribute) {
              refreshKanban();
          }
          if(field === 'fu_date' && window.calendar) window.calendar.refetchEvents();
      }
  })
  .catch(function(err){
      alert('수정 실패: 네트워크 오류');
      console.error(err);
  });
}

// 드롭다운 가시성 테스트 함수
function testDropdownVisibility() {
    console.log('=== 기본 DOM 테스트 시작 ===');
    
    // 1. 기본 DOM 조작 테스트
    try {
        const testDiv = document.createElement('div');
        testDiv.innerHTML = 'DOM 조작 테스트';
        console.log('DOM 요소 생성 성공:', testDiv);
    } catch (error) {
        console.error('DOM 요소 생성 실패:', error);
        return false;
    }
    
    // 2. body 접근 테스트
    try {
        console.log('document.body 존재:', !!document.body);
        console.log('document.body.appendChild 함수 존재:', typeof document.body.appendChild);
    } catch (error) {
        console.error('document.body 접근 실패:', error);
        return false;
    }
    
    // 3. 매우 간단한 alert 스타일 테스트
    const simpleTest = document.createElement('div');
    simpleTest.id = 'simple-test-' + Date.now();
    simpleTest.innerHTML = '🔴 테스트 메시지 - 이것이 보이나요?';
    
    // 가장 기본적인 스타일만 적용
    simpleTest.style.position = 'fixed';
    simpleTest.style.top = '20px';
    simpleTest.style.right = '20px';
    simpleTest.style.background = 'red';
    simpleTest.style.color = 'white';
    simpleTest.style.padding = '20px';
    simpleTest.style.zIndex = '999999';
    simpleTest.style.fontSize = '16px';
    simpleTest.style.fontWeight = 'bold';
    simpleTest.style.border = '3px solid yellow';
    simpleTest.style.borderRadius = '10px';
    
    console.log('간단한 테스트 요소 생성:', simpleTest);
    
    try {
        document.body.appendChild(simpleTest);
        console.log('테스트 요소 DOM에 추가 성공');
        
        // 추가 후 상태 확인
        setTimeout(() => {
            const addedElement = document.getElementById(simpleTest.id);
            console.log('추가된 요소 확인:', {
                found: !!addedElement,
                offsetWidth: addedElement ? addedElement.offsetWidth : 'N/A',
                offsetHeight: addedElement ? addedElement.offsetHeight : 'N/A',
                computedDisplay: addedElement ? window.getComputedStyle(addedElement).display : 'N/A',
                boundingRect: addedElement ? addedElement.getBoundingClientRect() : 'N/A'
            });
            
            // 5초 후 제거
            setTimeout(() => {
                if (addedElement) {
                    addedElement.remove();
                    console.log('테스트 요소 제거됨');
                }
            }, 5000);
        }, 100);
        
    } catch (error) {
        console.error('테스트 요소 DOM 추가 실패:', error);
        return false;
    }
    
    // 4. 더 복잡한 드롭다운 스타일 테스트
    setTimeout(() => {
        console.log('=== 복잡한 드롭다운 테스트 시작 ===');
        
        const complexTest = document.createElement('div');
        complexTest.id = 'complex-test-' + Date.now();
        complexTest.innerHTML = `
            <div style="background: white; padding: 15px; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #007bff;">드롭다운 테스트</h3>
                <ul style="list-style: none; margin: 0; padding: 0;">
                    <li style="padding: 8px; background: #f8f9fa; margin-bottom: 2px; cursor: pointer;" 
                        onclick="alert('항목 1 클릭됨')">항목 1</li>
                    <li style="padding: 8px; background: #f8f9fa; margin-bottom: 2px; cursor: pointer;"
                        onclick="alert('항목 2 클릭됨')">항목 2</li>
                    <li style="padding: 8px; background: #f8f9fa; margin-bottom: 2px; cursor: pointer;"
                        onclick="alert('항목 3 클릭됨')">항목 3</li>
                </ul>
                <button onclick="document.getElementById('${complexTest.id}').remove()" 
                        style="margin-top: 10px; padding: 5px 10px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    닫기
                </button>
            </div>
        `;
        
        // 중앙 배치
        complexTest.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8);
            padding: 20px;
            z-index: 999999;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        `;
        
        try {
            document.body.appendChild(complexTest);
            console.log('복잡한 테스트 요소 추가 성공');
            
            // 10초 후 자동 제거
            setTimeout(() => {
                const element = document.getElementById(complexTest.id);
                if (element) {
                    element.remove();
                    console.log('복잡한 테스트 요소 자동 제거됨');
                }
            }, 10000);
            
        } catch (error) {
            console.error('복잡한 테스트 요소 추가 실패:', error);
        }
    }, 2000);
    
    return true;
}

// 간단한 alert 테스트 함수
function simpleTest() {
    alert('JavaScript가 정상 작동합니다!');
    
    // 간단한 빨간 박스 생성
    const redBox = document.createElement('div');
    redBox.innerHTML = 'RED BOX TEST';
    redBox.style.cssText = 'position:fixed; top:10px; left:10px; background:red; color:white; padding:10px; z-index:99999; font-size:20px; font-weight:bold;';
    document.body.appendChild(redBox);
    
    setTimeout(() => {
        redBox.remove();
    }, 3000);
    
    console.log('simpleTest 완료');
}

// 최종 디버깅 함수 - 가장 기본적인 드롭다운 테스트
function ultimateDropdownTest() {
    console.log('=== 최종 드롭다운 디버깅 시작 ===');
    
    // 모든 기존 테스트 요소 제거
    document.querySelectorAll('[id^="test-"], [id^="simple-test-"], [id^="complex-test-"], .dropdown-edit').forEach(el => {
        el.remove();
    });
    
    // 1단계: 가장 기본적인 div 테스트
    console.log('1단계: 기본 div 생성 테스트');
    const basicDiv = document.createElement('div');
    basicDiv.id = 'basic-test';
    basicDiv.innerHTML = '⚠️ 기본 DIV 테스트';
    basicDiv.style.cssText = `
        position: fixed !important;
        top: 50px !important;
        left: 50px !important;
        width: 200px !important;
        height: 100px !important;
        background: yellow !important;
        color: black !important;
        border: 5px solid red !important;
        z-index: 999999 !important;
        font-size: 20px !important;
        font-weight: bold !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        padding: 20px !important;
    `;
    
    document.body.appendChild(basicDiv);
    console.log('기본 div 추가됨:', basicDiv);
    
    // 2단계: 실제 드롭다운과 동일한 구조 테스트
    setTimeout(() => {
        console.log('2단계: 실제 드롭다운 구조 테스트');
        
        const dropdownTest = document.createElement('div');
        dropdownTest.className = 'dropdown-edit';
        dropdownTest.id = 'dropdown-structure-test';
        
        // 실제 드롭다운과 동일한 스타일 적용
        dropdownTest.style.cssText = `
            position: fixed !important;
            background: white !important;
            border: 2px solid #007bff !important;
            border-radius: 8px !important;
            padding: 12px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
            z-index: 99999 !important;
            min-width: 200px !important;
            max-height: 300px !important;
            overflow-y: auto !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            font-size: 14px !important;
            font-family: Arial, sans-serif !important;
            top: 150px !important;
            left: 50px !important;
        `;
        
        // 실제 지역 드롭다운과 동일한 HTML 구조
        dropdownTest.innerHTML = `
            <div>
                <b style="color: #007bff; font-size: 16px;">지역 선택 테스트</b>
                <ul style="margin:8px 0 12px 0;max-height:120px;overflow-y:auto;list-style:none;padding:0;">
                    <li style="margin-bottom:2px;">
                        <span data-region="서울" style="cursor:pointer;padding:8px 12px;border-radius:4px;display:block;transition:all 0.2s;color:#333;border:1px solid transparent;">
                            서울
                        </span>
                    </li>
                    <li style="margin-bottom:2px;">
                        <span data-region="경기" style="cursor:pointer;padding:8px 12px;border-radius:4px;display:block;transition:all 0.2s;color:#333;border:1px solid transparent;">
                            경기
                        </span>
                    </li>
                    <li style="margin-bottom:2px;">
                        <span data-region="인천" style="cursor:pointer;padding:8px 12px;border-radius:4px;display:block;transition:all 0.2s;color:#333;border:1px solid transparent;">
                            인천
                        </span>
                    </li>
                </ul>
                <button onclick="document.getElementById('dropdown-structure-test').remove()" 
                        style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                    닫기
                </button>
            </div>
        `;
        
        document.body.appendChild(dropdownTest);
        console.log('드롭다운 구조 테스트 추가됨:', dropdownTest);
        
        // 상태 확인
        setTimeout(() => {
            const addedDropdown = document.getElementById('dropdown-structure-test');
            console.log('드롭다운 상태 확인:', {
                found: !!addedDropdown,
                offsetWidth: addedDropdown?.offsetWidth,
                offsetHeight: addedDropdown?.offsetHeight,
                clientWidth: addedDropdown?.clientWidth,
                clientHeight: addedDropdown?.clientHeight,
                scrollWidth: addedDropdown?.scrollWidth,
                scrollHeight: addedDropdown?.scrollHeight,
                boundingRect: addedDropdown?.getBoundingClientRect(),
                computedStyle: addedDropdown ? {
                    display: window.getComputedStyle(addedDropdown).display,
                    visibility: window.getComputedStyle(addedDropdown).visibility,
                    opacity: window.getComputedStyle(addedDropdown).opacity,
                    position: window.getComputedStyle(addedDropdown).position,
                    zIndex: window.getComputedStyle(addedDropdown).zIndex,
                    top: window.getComputedStyle(addedDropdown).top,
                    left: window.getComputedStyle(addedDropdown).left,
                    width: window.getComputedStyle(addedDropdown).width,
                    height: window.getComputedStyle(addedDropdown).height
                } : null
            });
            
            // 이벤트 바인딩 테스트
            if (addedDropdown) {
                const spans = addedDropdown.querySelectorAll('span[data-region]');
                spans.forEach(span => {
                    span.onclick = function() {
                        alert('지역 선택됨: ' + this.getAttribute('data-region'));
                        addedDropdown.remove();
                    };
                });
                console.log('이벤트 바인딩 완료, span 개수:', spans.length);
            }
        }, 500);
        
    }, 2000);
    
    // 3단계: CSS 충돌 검사
    setTimeout(() => {
        console.log('3단계: CSS 충돌 검사');
        
        // 현재 페이지의 모든 CSS 규칙 검사
        const allStyleSheets = Array.from(document.styleSheets);
        console.log('현재 페이지의 스타일시트 개수:', allStyleSheets.length);
        
        // dropdown-edit 클래스에 영향을 줄 수 있는 CSS 규칙 찾기
        let conflictingRules = [];
        allStyleSheets.forEach((sheet, index) => {
            try {
                const rules = Array.from(sheet.cssRules || sheet.rules || []);
                rules.forEach(rule => {
                    if (rule.selectorText && (
                        rule.selectorText.includes('.dropdown-edit') ||
                        rule.selectorText.includes('div') ||
                        rule.selectorText.includes('*')
                    )) {
                        conflictingRules.push({
                            sheet: index,
                            selector: rule.selectorText,
                            cssText: rule.cssText
                        });
                    }
                });
            } catch (e) {
                console.log(`스타일시트 ${index} 접근 불가:`, e.message);
            }
        });
        
        console.log('잠재적 충돌 CSS 규칙들:', conflictingRules);
        
    }, 4000);
    
    // 모든 테스트 요소 자동 정리 (15초 후)
    setTimeout(() => {
        document.querySelectorAll('[id^="basic-test"], [id^="dropdown-structure-test"]').forEach(el => {
            el.remove();
        });
        console.log('=== 최종 드롭다운 디버깅 완료 ===');
    }, 15000);
}

function showFilePreviewModal(fileInfo) {
    console.log('=== showFilePreviewModal 시작 ===');
    console.log('전체 fileInfo:', fileInfo);
    if (!fileInfo) {
        console.error('fileInfo가 없습니다.');
        return;
    }
    // 파일 확장자 추출
    const originalFilename = fileInfo.original_filename || fileInfo.filename || fileInfo.stored_filename || '';
    const ext = originalFilename.split('.').pop()?.toLowerCase() || '';
    // 파일 ID 추출
    let fileId = fileInfo.id || fileInfo.stored_filename || fileInfo.filename || '';
    // 현재 행 ID
    const currentRowId = window.currentDetailRowId;
    // 필드명 추출(영업노트 등 단일 파일 필드)
    const fieldName = fileInfo.field_name || fileInfo.attribute_name || fileInfo.attr_name || '';

    console.log('currentRowId:', currentRowId);
    console.log('fieldName:', fieldName);
    // 로딩 모달 생성
    const loadingModal = document.createElement('div');
    loadingModal.style.cssText = `position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;`;
    loadingModal.innerHTML = `<div style="background: #fff; border-radius: 8px; padding: 30px; text-align: center;"><div style="font-size: 48px; margin-bottom: 20px;">⏳</div><div style="font-size: 16px; color: #666;">파일을 로딩 중...</div></div>`;
    document.body.appendChild(loadingModal);
    // 서버에서 서명된 URL 가져오기
    const fetchSignedUrl = () => {
        if (!currentRowId) {
            showFilePreviewWithUrl(fileInfo, fileInfo.preview_url || fileInfo.download_url || fileInfo.public_url);
            loadingModal.remove();
            return;
        }
        // 영업노트(단일 파일 필드) 방식: fieldName이 있으면 해당 API 사용
        if (fieldName) {
            fetch(`/600/get_file_preview_url/${currentRowId}/${fieldName}/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                }
            })
            .then(response => response.json())
            .then(data => {
                loadingModal.remove();
                if (data.success && data.preview_url) {
                    showFilePreviewWithUrl(fileInfo, data.preview_url);
                } else {
                    showFilePreviewWithUrl(fileInfo, fileInfo.preview_url || fileInfo.download_url || fileInfo.public_url);
                }
            })
            .catch(error => {
                console.error('서명된 URL 가져오기 실패:', error);
                loadingModal.remove();
                showFilePreviewWithUrl(fileInfo, fileInfo.preview_url || fileInfo.download_url || fileInfo.public_url);
            });
            return;
        }
        // fallback: 기존 URL 사용
        showFilePreviewWithUrl(fileInfo, fileInfo.preview_url || fileInfo.download_url || fileInfo.public_url);
        loadingModal.remove();
    };
    // URL로 파일 미리보기 표시
    const showFilePreviewWithUrl = (fileInfo, previewUrl) => {
        console.log('선택된 previewUrl:', previewUrl);
        console.log('파일 확장자:', ext);
        console.log('content_type:', fileInfo.content_type);
        console.log('파일 타입:', fileInfo.type);

        // 파일 타입 우선 확인 (type 필드가 있으면 사용)
        const fileType = fileInfo.type || '';
        
        let viewerHtml = '';
        let isPreviewable = true;
        
        if (fileType === 'img' || fileInfo.content_type?.startsWith('image/')) {
            viewerHtml = `<img src="${previewUrl}" style="max-width:100%; max-height:80vh; display:block; margin:auto;" />`;
            console.log('이미지 파일 처리');
        } else if (fileType === 'pdf' || ext === 'pdf' || fileInfo.content_type === 'application/pdf') {
            viewerHtml = `<iframe src="${previewUrl}" style="width:100%; height:80vh;" frameborder="0"></iframe>`;
            console.log('PDF 파일 처리');
        } else if (fileType === 'audio' || fileInfo.content_type?.startsWith('audio/')) {
            viewerHtml = `<audio controls src="${previewUrl}" style="width:100%; max-height:80vh;"></audio>`;
            console.log('오디오 파일 처리');
        } else if (fileType === 'video' || fileInfo.content_type?.startsWith('video/')) {
            viewerHtml = `<video controls src="${previewUrl}" style="max-width:100%; max-height:80vh;"></video>`;
            console.log('비디오 파일 처리');
        } else if (
            ['xlsx', 'xls'].includes(ext) ||
            (fileInfo.content_type && fileInfo.content_type.includes('spreadsheetml'))
        ) {
            viewerHtml = `
                <div style="text-align:center; color:#888; padding:40px;">
                    이 파일 형식은 미리보기를 지원하지 않습니다.<br>
                    아래 버튼을 눌러 파일을 다운로드하세요.<br><br>
                    <button onclick="window.open('${fileInfo.download_url || previewUrl}', '_blank')"
                            style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        파일 다운로드
                    </button>
                </div>
            `;
            console.log('엑셀 파일 미리보기 미지원 안내');
        } else if (
            ['docx', 'pptx', 'ppt', 'doc'].includes(ext) ||
            (fileInfo.content_type && (
                fileInfo.content_type.includes('wordprocessingml') ||
                fileInfo.content_type.includes('presentationml') ||
                fileInfo.content_type.includes('msword')
            ))
        ) {
            // Google Docs Viewer 사용 - 서명된 URL 사용
            const url = encodeURIComponent(previewUrl);
            viewerHtml = `
                <iframe src="https://docs.google.com/viewer?url=${url}&embedded=true"
                        style="width:100%; height:75vh;" frameborder="0"></iframe>
                <div style="text-align: center; margin-top: 15px;">
                    <button onclick="window.open('${fileInfo.download_url || previewUrl}', '_blank')"
                            style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        파일 다운로드
                    </button>
                </div>
            `;
            console.log('문서/파워포인트 파일 처리 (Google Docs Viewer)');
        } else if (ext === 'hwp' || fileInfo.content_type === 'application/x-hwp') {
            if (fileInfo.converted_pdf_url) {
                viewerHtml = `<iframe src="${fileInfo.converted_pdf_url}" style="width:100%; height:80vh;" frameborder="0"></iframe>`;
                console.log('HWP 파일 처리 (변환된 PDF)');
            } else {
                isPreviewable = false;
                viewerHtml = `<div style="text-align:center; color:#888; padding:40px;">HWP 파일은 웹 미리보기를 지원하지 않습니다.<br>PDF로 변환 후 미리보기가 가능합니다.</div>`;
                console.log('HWP 파일 처리 (미지원)');
            }
        } else if (fileType === 'file' || fileType === '') {
            // 일반 파일인 경우 확장자 기반으로 처리
            if (['txt', 'md', 'json', 'xml', 'html', 'css', 'js'].includes(ext)) {
                // 텍스트 파일은 iframe으로 표시
                viewerHtml = `<iframe src="${previewUrl}" style="width:100%; height:80vh;" frameborder="0"></iframe>`;
                console.log('텍스트 파일 처리');
            } else {
                isPreviewable = false;
                viewerHtml = `
                    <div style="text-align:center; color:#888; padding:40px;">
                        이 파일 형식은 미리보기를 지원하지 않습니다.<br>
                        아래 버튼을 눌러 파일을 다운로드하세요.<br><br>
                        <button onclick="window.open('${fileInfo.download_url || previewUrl}', '_blank')"
                                style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            파일 다운로드
                        </button>
                    </div>
                `;
                console.log('지원하지 않는 파일 형식');
            }
        } else {
            isPreviewable = false;
            viewerHtml = `<div style="text-align:center; color:#888; padding:40px;">이 파일 형식은 미리보기를 지원하지 않습니다.</div>`;
            console.log('지원하지 않는 파일 형식');
        }

        console.log('생성된 viewerHtml:', viewerHtml);

        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;
        `;
        modal.innerHTML = `
            <div style="background: #fff; border-radius: 8px; max-width: 90vw; max-height: 90vh; width: 1000px; height: 1000px; position: relative; box-shadow: 0 4px 32px rgba(0,0,0,0.2);">
                <div style="padding: 16px 24px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight:bold;">미리보기: ${fileInfo.original_filename}</span>
                    <button onclick="this.closest('.file-preview-modal').remove()" style="background: #dc3545; color: #fff; border: none; border-radius: 50%; width: 32px; height: 32px; font-size: 18px; cursor: pointer;">×</button>
                </div>
                <div style="padding: 24px; overflow:auto; max-height: 75vh;">
                    ${viewerHtml}
                </div>
            </div>
        `;
        modal.className = 'file-preview-modal';
        modal.onclick = function(e) {
            if (e.target === modal) modal.remove();
        };
        document.body.appendChild(modal);
        console.log('=== showFilePreviewModal 완료 ===');
    };
    
    // 서명된 URL 가져오기 시작
    fetchSignedUrl();
}

// 전역 함수로 노출
window.showFilePreviewModal = showFilePreviewModal;