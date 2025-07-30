// hexToRgba 함수 정의
function hexToRgba(hex, alpha) {
    // hex 값이 없거나 유효하지 않은 경우 기본값 반환
    if (!hex || typeof hex !== 'string') {
        return `rgba(0, 0, 0, ${alpha})`;
    }
    
    // # 제거
    hex = hex.replace('#', '');
    
    // 3자리 hex를 6자리로 변환
    if (hex.length === 3) {
        hex = hex.split('').map(char => char + char).join('');
    }
    
    // 유효한 hex 값인지 확인
    if (!/^[0-9A-F]{6}$/i.test(hex)) {
        return `rgba(0, 0, 0, ${alpha})`;
    }
    
    // RGB 값 추출
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// 드롭다운 옵션을 처리하는 공통 함수
function processDropdownOptions(options, value, cell) {
    // 값이 숫자인 경우 ID로 처리, 그렇지 않으면 텍스트로 처리
    let option = null;
    let displayValue = value;
    
    if (value && !isNaN(value)) {
        // 숫자인 경우 ID로 찾기
        option = options.find(opt => opt.id == value);
        if (option) {
            displayValue = option.option;
        }
    } else {
        // 텍스트인 경우 이름으로 찾기
        option = options.find(opt => opt.option === value);
        if (option) {
            displayValue = option.option;
        }
    }
    
    if (option) {
        const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
        cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${displayValue}</div>`;
        cell.setAttribute('data-value', option.id);
    } else {
        // 옵션을 찾지 못한 경우에도 pill 형태로 표시
        cell.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${displayValue}</div>`;
        cell.setAttribute('data-value', value);
    }
}

  // Sticky 헤더 기능 초기화
  function initializeStickyHeader() {
      
      const tableView = document.getElementById('tableView');
      const table = document.getElementById('entryTable');
      
      if (!tableView || !table) {
          console.error('테이블 요소를 찾을 수 없습니다.');
          return;
      }
      
      // 기존 스크롤 이벤트 리스너 제거
      const newTableView = tableView.cloneNode(true);
      tableView.parentNode.replaceChild(newTableView, tableView);
      
      // 새로운 tableView 참조 가져오기
      const updatedTableView = document.getElementById('tableView');
      const updatedTable = document.getElementById('entryTable');
      
      if (!updatedTableView || !updatedTable) {
          console.error('업데이트된 테이블 요소를 찾을 수 없습니다.');
          return;
      }
      
      // 현재 스크롤 위치 확인 및 sticky 클래스 강제 적용
      const thead = updatedTable.querySelector('thead');
      if (thead) {
          const scrollTop = updatedTableView.scrollTop;
          
          // 스크롤이 있을 때 sticky 클래스 강제 적용
          if (scrollTop > 0) {
              thead.classList.add('sticky');
              thead.classList.remove('out-of-view');
          } else {
              thead.classList.remove('sticky');
              thead.classList.remove('out-of-view');
          }
      }
      
      // 테이블 컨테이너에 스크롤 이벤트 리스너 추가
      updatedTableView.addEventListener('scroll', function() {
          const thead = updatedTable.querySelector('thead');
          if (!thead) {
              console.log('thead 요소를 찾을 수 없습니다.');
              return;
          }
          
          const scrollTop = updatedTableView.scrollTop;
          
          // 스크롤이 있을 때 sticky 적용
          if (scrollTop > 0) {
              thead.classList.add('sticky');
              thead.classList.remove('out-of-view');
          } else {
              // 스크롤이 없을 때는 기본 상태로 복원
              thead.classList.remove('sticky');
              thead.classList.remove('out-of-view');
          }
      });
      
      // 윈도우 스크롤 이벤트도 추가하여 테이블이 뷰포트를 벗어날 때 처리
      window.addEventListener('scroll', function() {
          const thead = updatedTable.querySelector('thead');
          if (!thead) return;
          
          const tableViewRect = updatedTableView.getBoundingClientRect();
          
          // 테이블이 뷰포트를 벗어났는지 확인
          const isTableOutOfView = (
              tableViewRect.bottom < 0 ||
              tableViewRect.top > window.innerHeight
          );
          
          // 테이블이 뷰포트를 벗어났을 때 sticky 제거
          if (isTableOutOfView) {
              thead.classList.remove('sticky');
              thead.classList.add('out-of-view');
          } else {
              thead.classList.remove('out-of-view');
          }
      });
      
      // 윈도우 리사이즈 시 헤더 위치 재조정
      window.addEventListener('resize', function() {
          const thead = updatedTable.querySelector('thead');
          if (thead && thead.classList.contains('sticky')) {
              // sticky 상태 유지하되 위치 재조정
              const tableViewRect = updatedTableView.getBoundingClientRect();
              
              const isTableOutOfView = (
                  tableViewRect.bottom < 0 ||
                  tableViewRect.top > window.innerHeight
              );
              
              if (isTableOutOfView) {
                  thead.classList.remove('sticky');
                  thead.classList.add('out-of-view');
              } else {
                  thead.classList.remove('out-of-view');
              }
          }
      });
      
      console.log('Sticky 헤더 초기화 완료');
  }
  
  function bindTableCellEvents() {
      console.log('bindTableCellEvents 시작 - 셀 개수:', document.querySelectorAll('td[data-field]').length);
      
      document.querySelectorAll('td[data-field]').forEach(function(td) {
          const type = td.getAttribute('data-field');
          const dataType = td.getAttribute('data-type');
          
          // 기존 이벤트 리스너 제거 (중복 방지)
          td.removeEventListener('click', td._clickHandler);
          
          if (dataType === 'datetime') {
              const input = td.querySelector('input[type="date"]');
              if (input) {
                  input.onchange = function() {
                      const id = td.parentElement.getAttribute('data-id');
                      const newValue = input.value;
                      
                      // 새 행인 경우
                      if (id && id.startsWith('temp_')) {
                          saveNewRowField(td.parentElement, type, newValue);
                      } else {
                          // 기존 행인 경우
                          console.log('update_row_field, 테이블3')
                          fetch('/sales/update_row_field/', {
                              method: 'POST',
                              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                              body: 'id=' + id + '&field=' + encodeURIComponent(type) + '&value=' + encodeURIComponent(newValue)
                          }).then(function(response) {
                              return response.json();
                          }).then(function(data) {
                              if (!data.success) {
                                  alert('수정 실패: ' + data.error);
                                  return;
                              }
                              
                              // 현재 셀 즉시 업데이트
                              updateTableCell(id, type, newValue);
                              
                              // 종속된 행들 찾아서 업데이트
                              updateDependentRows(id, type, newValue);
                              
                              // datetime 필드인 경우 캘린더 리렌더링
                              if (dataType === 'datetime' && window.calendar) {
                                  window.calendar.refetchEvents();
                              }
                              
                              // 필요시 테이블/보드 갱신
                              refreshCalendarSettings();
                          }).catch(function(error) {
                              console.error('업데이트 중 오류:', error);
                              alert('업데이트 중 오류가 발생했습니다.');
                          });
                      }
                  };
              } else {
                  // input이 없는 경우 클릭 시 생성
                  const clickHandler = function() {
                      if (td.querySelector('input')) return;
                      
                      // 테이블 편집 상태 설정
                      setTableEditingState(true);
                      
                      td.style.width = td.offsetWidth + 'px';
                      
                      const oldValue = td.innerText.trim();
                      const id = td.parentElement.getAttribute('data-id');
                      
                      const input = document.createElement('input');
                      input.type = 'date';
                      input.value = oldValue ? oldValue.slice(0,10) : '';
                      input.className = 'table-edit-input';
                      input.style.position = 'absolute';
                      input.style.left = '0';
                      input.style.top = '0';
                      input.style.width = 'max-content';
                      input.style.minWidth = '100%';
                      input.style.background = '#fffbe6';
                      input.style.zIndex = '10';
                      input.style.border = 'none';
                      input.style.fontSize = 'inherit';
                      input.style.fontFamily = 'inherit';
                      input.style.lineHeight = 'inherit';
                      input.style.padding = '0';
                      input.style.margin = '0';
                      
                      td.appendChild(input);
                      input.focus();
                      
                      input.onblur = function() {
                          const newValue = input.value;
                          td.innerText = newValue;
                          td.style.width = '';
                          
                          // 테이블 편집 상태 해제
                          setTableEditingState(false);
                          
                          // 새 행인 경우
                          if (id && id.startsWith('temp_')) {
                              saveNewRowField(td.parentElement, type, newValue);
                          } else {
                              // 기존 행인 경우
                              console.log('update_row_field, 테이블4')
                              fetch('/sales/update_row_field/', {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                              }).then(function(response) {
                                  return response.json();
                              }).then(function(data) {
                                  if (!data.success) {
                                      alert('수정 실패: ' + (data.error || ''));
                                      return;
                                  }
                                  
                                  // 현재 셀 즉시 업데이트
                                  updateTableCell(id, type, newValue);
                                  
                                  // 종속된 행들 찾아서 업데이트
                                  updateDependentRows(id, type, newValue);
                                  
                                  // datetime 필드인 경우 캘린더 리렌더링
                                  if (dataType === 'datetime' && window.calendar) {
                                      window.calendar.refetchEvents();
                                  }
                                  
                                  // 필요시 테이블/보드 갱신
                                  refreshCalendarSettings();
                              }).catch(function(error) {
                                  console.error('업데이트 중 오류:', error);
                                  alert('업데이트 중 오류가 발생했습니다.');
                              });
                          }
                      };
                      
                      input.onkeydown = function(e) {
                          if (e.key === 'Enter') {
                              input.blur();
                          } else if (e.key === 'Escape') {
                              td.innerText = oldValue;
                              td.style.width = '';
                              setTableEditingState(false);
                          }
                      };
                  };
                  
                  td._clickHandler = clickHandler;
                  td.addEventListener('click', clickHandler);
              }
          } else if (dataType === 'dropdown' || dataType === 'region' || dataType === 'region_detail') {
              // 드롭다운 필드 클릭 이벤트
              const clickHandler = function() {
                  console.log('드롭다운 필드 클릭됨:', type, dataType);
                  console.log('td 요소:', td);
                  console.log('td의 data-field:', td.getAttribute('data-field'));
                  console.log('td의 data-type:', td.getAttribute('data-type'));
                  
                  if (td.querySelector('.dropdown-edit')) return;
                  
                  // 테이블 편집 상태 설정
                  setTableEditingState(true);
                  
                  const currentValue = td.getAttribute('data-value');
                  const currentSubregion = td.getAttribute('data-subregion');
                  const tr = td.parentElement;
                  
                  console.log('클릭 핸들러 내부 - currentValue:', currentValue, 'currentSubregion:', currentSubregion);
                  
                  if (dataType === 'region') {
                      console.log('지역 드롭다운 처리 (기존 행)');
                      const regionValue = td.parentElement.querySelector('td[data-field="지역"]');
                      const regionText = regionValue ? regionValue.innerText.trim() : '';
                      console.log('지역 텍스트:', regionText);
                      console.log('openDropdown 함수 호출 전');
                      openDropdown(td, 'region', tr.getAttribute('data-id'), regionText, '');
                      console.log('openDropdown 함수 호출 후');
                  } else if (dataType === 'region_detail') {
                      console.log('상세지역 드롭다운 처리 (기존 행)');
                      const regionTd = td.parentElement.querySelector('td[data-field="지역"]');
                      const regionValue = regionTd ? regionTd.innerText.trim() : '';
                      console.log('상세지역 - 지역 값:', regionValue);
                      console.log('openDropdown 함수 호출 전');
                      openDropdown(td, 'region_detail', tr.getAttribute('data-id'), regionValue, currentValue);
                      console.log('openDropdown 함수 호출 후');
                  } else {
                      console.log('일반 드롭다운 처리 (기존 행)');
                      openNewRowAttributeDropdown(td, type, currentValue, currentSubregion, tr);
                  }
              };
              
              td._clickHandler = clickHandler;
              td.addEventListener('click', clickHandler);
          } else if (dataType === 'memo' || (type === '메모' || type.includes('메모'))) {
              console.log('메모 필드 클릭 이벤트')
              // 메모 필드 클릭 이벤트
              const clickHandler = function() {
                  if (td.querySelector('textarea')) return;
                  
                  // 테이블 편집 상태 설정
                  setTableEditingState(true);
                  
                  const oldValue = td.innerText.trim();
                  const id = td.parentElement.getAttribute('data-id');
                  
                  // 메모 필드 편집 시 td의 overflow를 visible로 변경
                  td.style.overflow = 'visible';
                  td.style.textOverflow = 'ellipsis';
                  td.style.whiteSpace = 'nowrap';
                  td.style.wordWrap = 'break-word';
                  td.style.position = 'relative'; // td를 relative로 설정하여 textarea의 absolute 위치 기준점 제공
                  td.innerHTML = "";

                  const textarea = document.createElement('textarea');
                  textarea.value = oldValue;
                  textarea.className = 'table-edit-text-area';
                  textarea.style.position = 'absolute';
                  textarea.style.left = '0';
                  textarea.style.top = '0';
                  textarea.style.width = td.offsetWidth + 'px'; // td 너비로 고정
                  textarea.style.minHeight = '55px';
                  textarea.style.maxHeight = '300px';
                  textarea.style.background = '#fffbe6';
                  textarea.style.zIndex = '10';
                  textarea.style.border = '1px solid #ddd';
                  textarea.style.borderRadius = '4px';
                  textarea.style.fontSize = 'inherit';
                  textarea.style.fontFamily = 'inherit';
                  textarea.style.lineHeight = '1.4';
                  textarea.style.padding = '8px';
                  textarea.style.margin = '0';
                  textarea.style.resize = 'vertical';
                  textarea.style.overflowY = 'auto';
                  textarea.style.wordWrap = 'break-word';
                  textarea.style.whiteSpace = 'pre-wrap';
                  textarea.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                  
                  // textarea를 DOM에 추가하기 전에 높이 계산
                  const tempDiv = document.createElement('div');
                  tempDiv.style.cssText = `
                      position: absolute;
                      visibility: hidden;
                      white-space: pre-wrap;
                      word-wrap: break-word;
                      width: ${td.offsetWidth}px;
                      font-size: inherit;
                      font-family: inherit;
                      line-height: 1.4;
                      padding: 8px;
                      border: 1px solid #ddd;
                      box-sizing: border-box;
                  `;
                  tempDiv.textContent = oldValue;
                  document.body.appendChild(tempDiv);
                  
                  const contentHeight = tempDiv.offsetHeight;
                  document.body.removeChild(tempDiv);
                  
                  const minHeight = 55;
                  const maxHeight = 300;
                  const finalHeight = Math.max(minHeight, Math.min(contentHeight, maxHeight));
                  console.log('finalHeight', finalHeight)
                  
                  // textarea 높이를 명시적으로 설정 (minHeight를 먼저 설정하고 height를 나중에 설정)
                  textarea.style.minHeight = minHeight + 'px';
                  textarea.style.maxHeight = finalHeight + 'px';
                  
                  console.log(`메모 textarea 초기 높이 설정: 텍스트="${oldValue.substring(0, 50)}...", 내용 높이=${contentHeight}px, 최종 높이=${finalHeight}px`);
                  console.log(`textarea 실제 높이 설정: ${textarea.style.height}`);
                  
                  td.appendChild(textarea);
                  textarea.focus();
                  
                  // DOM에 추가된 후 height 설정 (다른 스타일이 덮어쓰지 않도록)
                  setTimeout(() => {
                      textarea.style.height = finalHeight + 'px';
                      console.log(`textarea DOM 추가 후 실제 높이: ${textarea.offsetHeight}px, 설정된 높이: ${textarea.style.height}`);
                  }, 10);
                  
                  // 자동 크기 조정 함수 - scrollHeight를 사용하여 자연스럽게 조정
                  function adjustMemoTextareaSize() {
                      const text = textarea.value;
                      
                      // 텍스트를 임시 div에 넣어서 실제 줄 수 계산
                      const tempDiv = document.createElement('div');
                      tempDiv.style.cssText = `
                          position: absolute;
                          visibility: hidden;
                          white-space: pre-wrap;
                          word-wrap: break-word;
                          width: ${textarea.offsetWidth}px;
                          font-size: ${getComputedStyle(textarea).fontSize};
                          font-family: ${getComputedStyle(textarea).fontFamily};
                          line-height: ${getComputedStyle(textarea).lineHeight};
                          padding: ${getComputedStyle(textarea).padding};
                          border: ${getComputedStyle(textarea).border};
                          box-sizing: border-box;
                      `;
                      tempDiv.textContent = text;
                      document.body.appendChild(tempDiv);
                      
                      const contentHeight = tempDiv.offsetHeight;
                      document.body.removeChild(tempDiv);
                      
                      const minHeight = 60;
                      const maxHeight = 300;
                      const finalHeight = Math.max(minHeight, Math.min(contentHeight, maxHeight));
                      
                      textarea.style.height = finalHeight + 'px';
                      
                      // 줄 수 계산
                      const lineHeight = parseInt(getComputedStyle(textarea).lineHeight) || 20;
                      const estimatedLines = Math.ceil(contentHeight / lineHeight);
                      
                      console.log(`메모 textarea 높이 조정: 텍스트="${text.substring(0, 50)}...", 내용 높이=${contentHeight}px, 최종 높이=${finalHeight}px, 예상 줄 수=${estimatedLines}`);
                  }
                  
                  // 입력 시 크기 조정
                  textarea.addEventListener('input', adjustMemoTextareaSize);
                  textarea.addEventListener('keydown', adjustMemoTextareaSize);
                  textarea.addEventListener('keyup', adjustMemoTextareaSize);
                  textarea.addEventListener('paste', adjustMemoTextareaSize);
                  textarea.addEventListener('cut', adjustMemoTextareaSize);
                  
                  // 편집 완료 시 td 스타일 복원 함수
                  function restoreTdStyle() {
                      td.style.overflow = 'hidden';
                      td.style.textOverflow = 'ellipsis';
                      td.style.whiteSpace = 'nowrap';
                      td.style.position = 'static'; // 원래 위치로 복원
                  }
                  
                  // 임시로 blur 이벤트를 주석 처리하여 textarea가 사라지지 않도록 함
                  textarea.onblur = function() {
                      const newValue = textarea.value;
                      // 줄바꿈을 <br>로 변환하여 표시
                      const displayValue = newValue.replace(/\n/g, '<br>');
                      td.innerHTML = displayValue;
                      
                      // td 스타일 복원
                      restoreTdStyle();
                      
                      // 테이블 편집 상태 해제
                      setTableEditingState(false);
                      
                      // 새 행인 경우
                      if (id && id.startsWith('temp_')) {
                          saveNewRowField(td.parentElement, type, newValue);
                      } else {
                          // 기존 행인 경우
                          console.log('update_row_field, 메모 필드')
                          fetch('/sales/update_row_field/', {
                              method: 'POST',
                              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                              body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                          }).then(function(response) {
                              return response.json();
                          }).then(function(data) {
                              if (!data.success) {
                                  alert('수정 실패: ' + (data.error || ''));
                                  return;
                              }
                              
                              // 현재 셀 즉시 업데이트
                              updateTableCell(id, type, newValue);
                              
                              // 종속된 행들 찾아서 업데이트
                              updateDependentRows(id, type, newValue);
                              
                              // 필요시 테이블/보드 갱신
                              refreshCalendarSettings();
                          }).catch(function(error) {
                              console.error('업데이트 중 오류:', error);
                              alert('업데이트 중 오류가 발생했습니다.');
                          });
                      }
                  };
              };
              
              td._clickHandler = clickHandler;
              td.addEventListener('click', clickHandler);
          } else {
              // 일반 텍스트 필드 클릭 이벤트
              const clickHandler = function(e) {
                  if (td.querySelector('input')) return;
                  
                  // 테이블 편집 상태 설정
                  setTableEditingState(true);
                  
                  if (type === '회사명') {
                      // 회사명 필드 특별 처리
                      if (e.target.classList.contains('more-btn')) return;
                      td.style.width = td.offsetWidth + 'px';
                      const nameDiv = td.querySelector('.name-text');
                      if (!nameDiv) return;
                      const oldValue = nameDiv.innerText;
                      const id = td.parentElement.getAttribute('data-id');
                      const input = document.createElement('input');
                      input.type = 'text';
                      input.value = oldValue;
                      input.className = 'table-edit-input';
                      nameDiv.innerHTML = '';
                      nameDiv.appendChild(input);
                      const moreBtnWrapper = td.querySelector('.more-btn-wrapper');
                      if (moreBtnWrapper) moreBtnWrapper.style.visibility = 'hidden';
                      input.focus();
                      function restoreCell(value) {
                          td.innerHTML = `
                            <div class="name-container">
                              <div class="name-text">${value}</div>
                              <div class="more-btn-wrapper"><div class="more-btn" style="cursor:pointer;">⋯</div></div>
                            </div>
                          `;
                          // ...버튼 이벤트 재바인딩
                          const newMoreBtn = td.querySelector('.more-btn');
                          if (newMoreBtn) {
                              newMoreBtn.onclick = function(e) {
                                  e.stopPropagation();
                                  const tr = td.closest('tr');
                                  const id = tr.getAttribute('data-id');
                                  if (!id) { alert('ID 정보가 없습니다.'); return; }
                                  fetch('/sales/get_row_details/' + id + '/')
                                      .then(r => r.json())
                                      .then(function(data) {
                                          if (data.success) showDetailModal(data.row_data, data.row_id);
                                          else alert('상세정보 불러오기 실패: ' + (data.error || ''));
                                      })
                                      .catch(function(err) {
                                          alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                                          console.error(err);
                                      });
                              };
                          }
                          // td.onclick도 재바인딩 (more-btn 체크)
                          td.onclick = function(e) {
                              if (e.target.classList.contains('more-btn')) return;
                              if (td.querySelector('input')) return;
                              td.style.width = td.offsetWidth + 'px';
                              const nameDiv = td.querySelector('.name-text');
                              if (!nameDiv) return;
                              const oldValue = nameDiv.innerText;
                              const id = td.parentElement.getAttribute('data-id');
                              const input = document.createElement('input');
                              input.type = 'text';
                              input.value = oldValue;
                              input.className = 'table-edit-input';
                              nameDiv.innerHTML = '';
                              nameDiv.appendChild(input);
                              const moreBtnWrapper = td.querySelector('.more-btn-wrapper');
                              if (moreBtnWrapper) moreBtnWrapper.style.visibility = 'hidden';
                              input.focus();
                              input.onblur = function() {
                                  const newValue = input.value;
                                  restoreCell(newValue);
                                  if (id && id.startsWith('temp_')) {
                                      saveNewRowField(td.parentElement, '회사명', newValue);
                                  } else {
                                      fetch('/sales/update_row_field/', {
                                          method: 'POST',
                                          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                          body: 'id=' + id + '&field=회사명&value=' + encodeURIComponent(newValue)
                                      });
                                  }
                              };
                              input.onkeydown = function(e) {
                                  if (e.key === 'Enter') input.blur();
                                  if (e.key === 'Escape') restoreCell(oldValue);
                              };
                          };
                          td.style.width = '';
                      }
                      input.onblur = function() {
                          const newValue = input.value;
                          restoreCell(newValue);
                          if (id && id.startsWith('temp_')) {
                              saveNewRowField(td.parentElement, '회사명', newValue);
                          } else {
                              fetch('/sales/update_row_field/', {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'id=' + id + '&field=회사명&value=' + encodeURIComponent(newValue)
                              });
                          }
                      };
                      input.onkeydown = function(e) {
                          if (e.key === 'Enter') input.blur();
                          if (e.key === 'Escape') restoreCell(oldValue);
                      };
                  } else if (type === '매출' || type.includes('매출')) {
                      // 매출 필드 특별 처리
                      td.style.width = td.offsetWidth + 'px';
                      const oldValue = td.getAttribute('data-raw') || td.innerText.replace(/[^\d]/g, '');
                      const id = td.parentElement.getAttribute('data-id');
                      const input = document.createElement('input');
                      input.type = 'text';
                      input.value = oldValue ? parseInt(oldValue, 10).toLocaleString() : '';
                      input.className = 'table-edit-input';
                      input.style.position = 'absolute';
                      input.style.left = '0';
                      input.style.top = '0';
                      input.style.width = 'max-content';
                      input.style.minWidth = '100%';
                      input.style.background = '#fffbe6';
                      input.style.zIndex = '10';
                      input.style.border = 'none';
                      input.style.fontSize = 'inherit';
                      input.style.fontFamily = 'inherit';
                      input.style.lineHeight = 'inherit';
                      input.style.padding = '0';
                      input.style.margin = '0';
                      input.oninput = function() {
                          let val = this.value.replace(/[^0-9]/g, '');
                          this.value = Number(val).toLocaleString();
                      };
                      input.onblur = function() {
                          const cleanValue = input.value.replace(/[^\d]/g, '');
                          updateCellValue(id, type, cleanValue, td);
                      };
                      input.onkeydown = function(e) {
                          if (e.key === 'Enter') input.blur();
                          if (e.key === 'Escape') td.innerText = oldValue;
                      };
                      td.innerHTML = '';
                      td.appendChild(input);
                      input.focus();
                      input.select();
                  } else {
                      // 일반 텍스트 필드 처리
                      const oldValue = td.innerText.trim();
                      const id = td.parentElement.getAttribute('data-id');
                      
                      const input = document.createElement('input');
                      input.type = 'text';
                      input.value = oldValue;
                      input.className = 'table-edit-input';
                      input.style.position = 'absolute';
                      input.style.left = '0';
                      input.style.top = '0';
                      input.style.width = 'max-content';
                      input.style.minWidth = '100%';
                      input.style.background = '#fffbe6';
                      input.style.zIndex = '10';
                      input.style.border = 'none';
                      input.style.fontSize = 'inherit';
                      input.style.fontFamily = 'inherit';
                      input.style.lineHeight = 'inherit';
                      input.style.padding = '0';
                      input.style.margin = '0';
                      
                      td.appendChild(input);
                      input.focus();
                      
                      input.onblur = function() {
                          const newValue = input.value;
                          td.innerText = newValue;
                          
                          // 테이블 편집 상태 해제
                          setTableEditingState(false);
                          
                          // 새 행인 경우
                          if (id && id.startsWith('temp_')) {
                              saveNewRowField(td.parentElement, type, newValue);
                          } else {
                              // 기존 행인 경우
                              console.log('update_row_field, 테이블6')
                              fetch('/sales/update_row_field/', {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                              }).then(function(response) {
                                  return response.json();
                              }).then(function(data) {
                                  if (!data.success) {
                                      alert('수정 실패: ' + (data.error || ''));
                                      return;
                                  }
                                  
                                  // 현재 셀 즉시 업데이트
                                  updateTableCell(id, type, newValue);
                                  
                                  // 종속된 행들 찾아서 업데이트
                                  updateDependentRows(id, type, newValue);
                                  
                                  // 필요시 테이블/보드 갱신
                                  refreshCalendarSettings();
                              }).catch(function(error) {
                                  console.error('업데이트 중 오류:', error);
                                  alert('업데이트 중 오류가 발생했습니다.');
                              });
                          }
                      };
                      
                      input.onkeydown = function(e) {
                          if (e.key === 'Enter') {
                              input.blur();
                          } else if (e.key === 'Escape') {
                              td.innerText = oldValue;
                              setTableEditingState(false);
                          }
                      };
                  }
              };
              
              td._clickHandler = clickHandler;
              td.addEventListener('click', clickHandler);
              
              // 회사명 필드에 대한 상세보기 버튼 이벤트 바인딩
              if (type === '회사명') {
                  const moreBtn = td.querySelector('.more-btn');
                  if (moreBtn) {
                      moreBtn.onclick = function(e) {
                          e.stopPropagation();
                          const tr = td.closest('tr');
                          const id = tr.getAttribute('data-id');
                          if (!id) { alert('ID 정보가 없습니다.'); return; }
                          fetch('/sales/get_row_details/' + id + '/')
                              .then(r => r.json())
                              .then(function(data) {
                                  if (data.success) showDetailModal(data.row_data, data.row_id);
                                  else alert('상세정보 불러오기 실패: ' + (data.error || ''));
                              })
                              .catch(function(err) {
                                  alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                                  console.error(err);
                              });
                      };
                  }
              }
          }
      });
      
      console.log('bindTableCellEvents 완료');
  }
  
  // 부분 업데이트 함수 - 특정 셀만 업데이트
  function updateTableCell(rowId, field, value) {
      const row = document.querySelector(`tr[data-id="${rowId}"]`);
      if (!row) return;
      
      const cell = row.querySelector(`td[data-field="${field}"]`);
      if (!cell) return;
      
      
      // 셀 내용만 업데이트 (전체 테이블 새로고침 없이)
      if (field === '매출' || field.includes('매출')) {
          cell.textContent = formatToKoreanCurrency(value);
          cell.setAttribute('data-raw', value);
      } else if (field === '개업년월') {
          // 개업년월 특별 처리
          try {
              if (typeof value === 'string' && value.startsWith('{')) {
                  const data = JSON.parse(value);
                  if (data.opening_date) {
                      cell.textContent = data.opening_date;
                  } else if (data.years_ago) {
                      cell.textContent = `${data.years_ago}년전`;
                  } else {
                      cell.textContent = value;
                  }
              } else {
                  cell.textContent = value;
              }
          } catch (e) {
              cell.textContent = value;
          }
      } else if (field === '회사명') {
          // 회사명 필드 특별 처리
          const nameTextDiv = cell.querySelector('.name-text');
          if (nameTextDiv) {
              nameTextDiv.innerText = value;
          } else {
              cell.textContent = value;
          }
      } else {
          // 드롭다운 필드인지 확인
          const dropdownFields = (window.ATTR_FIELDS || [])
              .filter(attr => attr.attributeType_name === 'dropdown')
              .map(attr => attr.name);
          
          if (dropdownFields.includes(field)) {
              // 드롭다운 필드는 서버에서 최신 옵션 정보를 가져와서 업데이트
              
              // 먼저 현재 셀의 내용을 pill 형태로 임시 업데이트 (로딩 상태)
              if (value) {
                  processDropdownOptions(window.DROPDOWN_OPTIONS[field], value, cell);
              }
              
              // 서버에서 옵션 정보를 가져와서 처리
              // window.DROPDOWN_OPTIONS에서 먼저 확인, 없으면 서버에서 가져오기
              let options = null;
              if (window.DROPDOWN_OPTIONS && window.DROPDOWN_OPTIONS[field]) {
                  options = window.DROPDOWN_OPTIONS[field];
              }
              
              if (options) {
                  // 로컬에 있는 옵션 사용
                  processDropdownOptions(options, value, cell);
              } else {
                  // 서버에서 옵션 가져오기 (fallback)
                  fetch('/sales/dropdown_options/?field=' + encodeURIComponent(field))
                      .then(response => {
                          if (!response.ok) {
                              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                          }
                          return response.json();
                      })
                      .then(data => {
                          if (data.options && Array.isArray(data.options)) {
                              processDropdownOptions(data.options, value, cell);
                          } else {
                              // 옵션 데이터가 없는 경우에도 pill 형태로 표시
                              processDropdownOptions(window.DROPDOWN_OPTIONS[field], value, cell);
                          }
                      })
                      .catch(error => {
                          console.error('드롭다운 옵션 업데이트 실패:', error);
                          // 오류 발생 시에도 pill 형태로 표시
                          processDropdownOptions(window.DROPDOWN_OPTIONS[field], value, cell);
                      });
              }
          } else {
              // 일반 필드
              cell.textContent = value;
              cell.setAttribute('data-value', value);
          }
      }
      
      // 실시간 동기화 (캘린더만)
      if (field === 'F/U 일정' && window.calendar) {
          window.calendar.refetchEvents();
      }
      
      // datetime 타입 필드인 경우 캘린더 리렌더링
      if (cell.getAttribute('data-type') === 'datetime' && window.calendar) {
          window.calendar.refetchEvents();
      }
      
      // 모든 datetime 필드 변경 시 캘린더 리렌더링
      if (typeof refreshCalendar === 'function') {
          refreshCalendar();
      }
  }
  
  
  
  // 새 행용 Attribute 시스템 이벤트 바인딩
  function bindNewRowAttributeEvents(tr) {
      tr.querySelectorAll('td[data-field]').forEach(function(td) {
          const field = td.getAttribute('data-field');
          const type = td.getAttribute('data-type');
          
          
          // datetime 타입 필드들
          if (type === 'datetime') {
              const input = td.querySelector('input[type="date"]');
              if (input) {
                  input.onchange = function() {
                      const newValue = input.value;
                      // 새 행 필드 저장
                      saveNewRowField(tr, field, newValue);
                  };
              }
          }
          // dropdown 타입이나 특수 지역 필드들
          else if(type === 'dropdown' || field === '지역' || field === '상세지역') {
              console.log('드롭다운/지역 셀 이벤트 바인딩:', {type, field, dataType});
              td.style.cursor = 'pointer';
              td.onclick = function(e) {
                  e.stopPropagation();
                  console.log('드롭다운/지역 셀 클릭됨:', {type, field, dataType});
                  
                  let dropdownType = '';
                  if(type === 'dropdown') {
                      // 필드명을 그대로 사용 (영어 매핑 제거)
                      dropdownType = field;
                  } else if(field === '지역') {
                      dropdownType = 'region';
                      console.log('지역 드롭다운으로 설정');
                  } else if(field === '상세지역') {
                      dropdownType = 'region_detail';
                      console.log('상세지역 드롭다운으로 설정');
                  }
                  
                  console.log('dropdownType 설정됨:', dropdownType);
                  
                  if(dropdownType === 'region') {
                      // 회사명 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                      const currentValue = (field === '회사명') ? 
                          (td.querySelector('.name-text')?.innerText.trim() || '') : 
                          td.innerText.trim();
                      const regionValue = td.parentElement.querySelector('td[data-field="지역"]');
                      const regionText = regionValue ? 
                          (regionValue.getAttribute('data-field') === '회사명' ? 
                              (regionValue.querySelector('.name-text')?.innerText.trim() || '') : 
                              regionValue.innerText.trim()) : '';
                      console.log('지역 드롭다운 호출:', {currentValue, regionText});
                      openDropdown(td, 'region', id, currentValue, regionText);

                  } else if(dropdownType === 'region_detail') {
                      console.log('상세지역 드롭다운 처리');
                      const regionTd = td.parentElement.querySelector('td[data-field="지역"]');
                      const regionValue = regionTd ? 
                          (regionTd.getAttribute('data-field') === '회사명' ? 
                              (regionTd.querySelector('.name-text')?.innerText.trim() || '') : 
                              regionTd.innerText.trim()) : '';
                      
                      const currentValue = (field === '회사명') ? 
                          (td.querySelector('.name-text')?.innerText.trim() || '') : 
                          td.innerText.trim();
                      console.log('상세지역 드롭다운 호출:', {regionValue, currentValue});
                      openDropdown(td, 'region_detail', id, regionValue, currentValue);

                  } else if(dataType === 'dropdown') {
                      console.log('일반 드롭다운 처리');
                      openDropdown(td, type, id, td.getAttribute('data-value'));
                  }
              };

          } else {
              td.onclick = function() {
                  if (td.querySelector('input')) return;
                  td.style.width = td.offsetWidth + 'px';
                  if(type === '회사명') {
                      // ...버튼 이벤트 항상 바인딩
                      const moreBtn = td.querySelector('.more-btn');
                      if (moreBtn) {
                          moreBtn.onclick = function(e) {
                              e.stopPropagation();
                              const tr = td.closest('tr');
                              const id = tr.getAttribute('data-id');
                              if (!id) { alert('ID 정보가 없습니다.'); return; }
                              fetch('/sales/get_row_details/' + id + '/')
                                  .then(r => r.json())
                                  .then(function(data) {
                                      if (data.success) showDetailModal(data.row_data, data.row_id);
                                      else alert('상세정보 불러오기 실패: ' + (data.error || ''));
                                  })
                                  .catch(function(err) {
                                      alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                                      console.error(err);
                                  });
                          };
                      }
                      td.onclick = function(e) {
                          // more-btn을 클릭한 경우 상세보기 모달로 처리하지 않음
                          if (e.target.classList.contains('more-btn') || e.target.closest('.more-btn')) {
                              return;
                          }
                          
                          // name-text를 클릭한 경우에만 편집 모드로 진입
                          if (!e.target.classList.contains('name-text') && !e.target.closest('.name-text')) {
                              return;
                          }
                          
                          if (td.querySelector('input')) return;
                          td.style.width = td.offsetWidth + 'px';
                          const nameDiv = td.querySelector('.name-text');
                          if (!nameDiv) return;
                          const oldValue = nameDiv.innerText;
                          const id = td.parentElement.getAttribute('data-id');
                          const input = document.createElement('input');
                          input.type = 'text';
                          input.value = oldValue;
                          input.className = 'table-edit-input';
                          nameDiv.innerHTML = '';
                          nameDiv.appendChild(input);
                          const moreBtnWrapper = td.querySelector('.more-btn-wrapper');
                          if (moreBtnWrapper) moreBtnWrapper.style.visibility = 'hidden';
                          input.focus();
                          function restoreCell(value) {
                              td.innerHTML = `
                                <div class="name-container">
                                  <div class="name-text">${value}</div>
                                  <div class="more-btn-wrapper"><div class="more-btn" style="cursor:pointer;">⋯</div></div>
                                </div>
                              `;
                              // ...버튼 이벤트 재바인딩
                              const newMoreBtn = td.querySelector('.more-btn');
                              if (newMoreBtn) {
                                  newMoreBtn.onclick = function(e) {
                                      e.stopPropagation();
                                      const tr = td.closest('tr');
                                      const id = tr.getAttribute('data-id');
                                      if (!id) { alert('ID 정보가 없습니다.'); return; }
                                      fetch('/sales/get_row_details/' + id + '/')
                                          .then(r => r.json())
                                          .then(function(data) {
                                              if (data.success) showDetailModal(data.row_data, data.row_id);
                                              else alert('상세정보 불러오기 실패: ' + (data.error || ''));
                                          })
                                          .catch(function(err) {
                                              alert('상세정보 불러오기 실패: 네트워크 오류\n' + err);
                                              console.error(err);
                                          });
                                  };
                              }
                              // td.onclick도 재바인딩 (more-btn 체크)
                              td.onclick = function(e) {
                                  // more-btn을 클릭한 경우 상세보기 모달로 처리하지 않음
                                  if (e.target.classList.contains('more-btn') || e.target.closest('.more-btn')) {
                                      return;
                                  }
                                  
                                  // name-text를 클릭한 경우에만 편집 모드로 진입
                                  if (!e.target.classList.contains('name-text') && !e.target.closest('.name-text')) {
                                      return;
                                  }
                                  
                                  if (td.querySelector('input')) return;
                                  td.style.width = td.offsetWidth + 'px';
                                  const nameDiv = td.querySelector('.name-text');
                                  if (!nameDiv) return;
                                  const oldValue = nameDiv.innerText;
                                  const id = td.parentElement.getAttribute('data-id');
                                  const input = document.createElement('input');
                                  input.type = 'text';
                                  input.value = oldValue;
                                  input.className = 'table-edit-input';
                                  nameDiv.innerHTML = '';
                                  nameDiv.appendChild(input);
                                  const moreBtnWrapper = td.querySelector('.more-btn-wrapper');
                                  if (moreBtnWrapper) moreBtnWrapper.style.visibility = 'hidden';
                                  input.focus();
                                  input.onblur = function() {
                                      const newValue = input.value;
                                      restoreCell(newValue);
                                      if (id && id.startsWith('temp_')) {
                                          saveNewRowField(td.parentElement, '회사명', newValue);
                                      } else {
                                          fetch('/sales/update_row_field/', {
                                              method: 'POST',
                                              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                              body: 'id=' + id + '&field=회사명&value=' + encodeURIComponent(newValue)
                                          });
                                      }
                                  };
                                  input.onkeydown = function(e) {
                                      if (e.key === 'Enter') input.blur();
                                      if (e.key === 'Escape') restoreCell(oldValue);
                                  };
                              };
                              td.style.width = '';
                          }
                          input.onblur = function() {
                              const newValue = input.value;
                              restoreCell(newValue);
                              if (id && id.startsWith('temp_')) {
                                  saveNewRowField(td.parentElement, '회사명', newValue);
                              } else {
                                  fetch('/sales/update_row_field/', {
                                      method: 'POST',
                                      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                      body: 'id=' + id + '&field=회사명&value=' + encodeURIComponent(newValue)
                                  });
                              }
                          };
                          input.onkeydown = function(e) {
                              if (e.key === 'Enter') input.blur();
                              if (e.key === 'Escape') restoreCell(oldValue);
                          };
                      };
                  } else {
                      // 일반 텍스트 필드들 처리
                      // 회사명 필드인 경우 .name-text에서 값 추출, 다른 필드는 td.innerText 사용
                      const oldValue = (type === '회사명') ? 
                          (td.querySelector('.name-text')?.innerText || '') : 
                          td.innerText;
                      const id = td.parentElement.getAttribute('data-id');
                      
                      let inputType = 'text';
                      // 날짜 필드들은 date input 사용
                      if (["TA","미팅","F/U 일정"].includes(type) || dataType === 'datetime') {
                          inputType = 'date';
                      }
                      
                      const input = document.createElement('input');
                      input.type = inputType;
                      // 매출 필드라면 한글 단위로 표시, 아니면 기존 값
                      if (type === '매출' || type.includes('매출')) {
                          const raw = td.getAttribute('data-raw');
                          let initialValue = '';
                          if (raw && !isNaN(parseInt(raw, 10))) {
                              initialValue = formatNumberWithComma(parseInt(raw, 10));
                          }
                          input.value = initialValue;
                          input.oninput = function(e) {
                              // 숫자만 추출 후 콤마 포맷팅
                              let val = this.value.replace(/[^0-9]/g, '');
                              this.value = formatNumberWithComma(val);
                          };
                          input.onblur = function() {
                              const cleanValue = removeCommaFromNumber(this.value);
                              updateCellValue(id, type, cleanValue, td);
                          };
                      } else {
                          input.value = (inputType==='date' && oldValue) ? oldValue.trim().slice(0,10) : oldValue.trim();
                          input.onblur = function() {
                              const newValue = input.value;
                              if(type === '회사명') {
                                  const nameTextDiv = td.querySelector('.name-text');
                                  if(nameTextDiv) nameTextDiv.innerText = newValue;
                                  if(input.parentNode) input.parentNode.removeChild(input);
                              } else {
                                  td.innerText = newValue;
                              }
                              td.style.width = '';
                              console.log('update_row_field, 테이블7')
                              fetch('/sales/update_row_field/', {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                              }).then(function(response) {
                                  return response.json();
                              }).then(function(data) {
                                  if (!data.success) {
                                      alert('수정 실패: ' + (data.error || ''));
                                      return;
                                  }
                                  
                                  // 현재 셀 즉시 업데이트
                                  updateTableCell(id, type, newValue);
                                  
                                  // 종속된 행들 찾아서 업데이트
                                  updateDependentRows(id, type, newValue);
                                  
                                  // datetime 필드인 경우 캘린더 리렌더링
                                  if (dataType === 'datetime' && window.calendar) {
                                      window.calendar.refetchEvents();
                                  }
                                  
                                  // 필요시 테이블/보드 갱신
                                  refreshCalendarSettings();
                              }).catch(function(error) {
                                  console.error('업데이트 중 오류:', error);
                                  alert('업데이트 중 오류가 발생했습니다.');
                              });
                          };
                      }
                      input.className = 'table-edit-input';
                      
                      // 메모 필드인 경우 특별한 스타일 적용
                      console.log('필드 타입 확인:', type, 'data-type:', dataType);
                      if (type === '메모' || type.includes('메모') || dataType === 'memo') {
                          console.log('메모 필드 특별 스타일 적용 - 타입:', type, '데이터타입:', dataType);
                          
                          // input을 textarea로 변경
                          const textarea = document.createElement('textarea');
                          textarea.value = input.value;
                          textarea.className = 'table-edit-input';
                          
                          // 메모 필드 편집 시 td의 overflow를 visible로 변경
                          td.style.overflow = 'visible';
                          td.style.textOverflow = 'clip';
                          td.style.whiteSpace = 'normal';
                          td.style.position = 'relative'; // td를 relative로 설정하여 textarea의 absolute 위치 기준점 제공
                          td.style.width = td.offsetWidth + 'px'; // td 너비 고정
                          td.style.height = td.offsetHeight + 'px';
                          
                          textarea.style.cssText = `
                              position: absolute;
                              left: 0;
                              top: 0;
                              width: ${td.offsetWidth}px;
                              min-height: 60px;
                              max-height: 300px;
                              background: #fffbe6;
                              z-index: 10;
                              border: 1px solid #ddd;
                              border-radius: 4px;
                              font-size: inherit;
                              font-family: inherit;
                              line-height: 1.4;
                              padding: 8px;
                              margin: 0;
                              resize: vertical;
                              overflow-y: auto;
                              word-wrap: break-word;
                              white-space: pre-wrap;
                              box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                          `;
                          
                          // 메모 필드의 경우 자동 크기 조정 함수 - scrollHeight를 사용하여 자연스럽게 조정
                          function adjustMemoTextareaSize() {
                              const text = textarea.value;
                              
                              // 텍스트를 임시 div에 넣어서 실제 줄 수 계산
                              const tempDiv = document.createElement('div');
                              tempDiv.style.cssText = `
                                  position: absolute;
                                  visibility: hidden;
                                  white-space: pre-wrap;
                                  word-wrap: break-word;
                                  width: ${textarea.offsetWidth}px;
                                  font-size: ${getComputedStyle(textarea).fontSize};
                                  font-family: ${getComputedStyle(textarea).fontFamily};
                                  line-height: ${getComputedStyle(textarea).lineHeight};
                                  padding: ${getComputedStyle(textarea).padding};
                                  border: ${getComputedStyle(textarea).border};
                                  box-sizing: border-box;
                              `;
                              tempDiv.textContent = text;
                              document.body.appendChild(tempDiv);
                              
                              const contentHeight = tempDiv.offsetHeight;
                              document.body.removeChild(tempDiv);
                              
                              const minHeight = 60;
                              const maxHeight = 300;
                              const finalHeight = Math.max(minHeight, Math.min(contentHeight, maxHeight));
                              
                              textarea.style.height = finalHeight + 'px';
                              
                              // 줄 수 계산
                              const lineHeight = parseInt(getComputedStyle(textarea).lineHeight) || 20;
                              const estimatedLines = Math.ceil(contentHeight / lineHeight);
                              
                              console.log(`메모 textarea 높이 조정: 텍스트="${text.substring(0, 50)}...", 내용 높이=${contentHeight}px, 최종 높이=${finalHeight}px, 예상 줄 수=${estimatedLines}`);
                          }
                          
                          // input을 textarea로 교체
                          td.innerHTML = '';
                          td.appendChild(textarea);
                          textarea.focus();
                          
                          // 초기 크기 조정 - textarea가 DOM에 추가된 후 실행
                          setTimeout(adjustMemoTextareaSize, 10);
                          
                          // 입력 시 크기 조정
                          textarea.addEventListener('input', adjustMemoTextareaSize);
                          textarea.addEventListener('keydown', adjustMemoTextareaSize);
                          textarea.addEventListener('keyup', adjustMemoTextareaSize);
                          textarea.addEventListener('paste', adjustMemoTextareaSize);
                          textarea.addEventListener('cut', adjustMemoTextareaSize);
                          
                          // 편집 완료 시 td 스타일 복원 함수
                          function restoreTdStyle() {
                              td.style.overflow = 'hidden';
                              td.style.textOverflow = 'ellipsis';
                              td.style.whiteSpace = 'nowrap';
                              td.style.position = 'static'; // 원래 위치로 복원
                          }
                          
                          // 기존 onblur 이벤트를 textarea용으로 수정
                          textarea.onblur = function() {
                              const newValue = textarea.value;
                              // 줄바꿈을 <br>로 변환하여 표시
                              const displayValue = newValue.replace(/\n/g, '<br>');
                              td.innerHTML = displayValue;
                              td.style.width = '';
                              
                              // td 스타일 복원
                              restoreTdStyle();
                              
                              console.log('update_row_field, 새 행 메모 필드')
                              fetch('/sales/update_row_field/', {
                                  method: 'POST',
                                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                  body: 'id='+id+'&field='+encodeURIComponent(type)+'&value='+encodeURIComponent(newValue)
                              }).then(function(response) {
                                  return response.json();
                              }).then(function(data) {
                                  if (!data.success) {
                                      alert('수정 실패: ' + (data.error || ''));
                                      return;
                                  }
                                  
                                  // 현재 셀 즉시 업데이트
                                  updateTableCell(id, type, newValue);
                                  
                                  // 종속된 행들 찾아서 업데이트
                                  updateDependentRows(id, type, newValue);
                                  
                                  // 필요시 테이블/보드 갱신
                                  refreshCalendarSettings();
                              }).catch(function(error) {
                                  console.error('업데이트 중 오류:', error);
                                  alert('업데이트 중 오류가 발생했습니다.');
                              });
                          };
                          
                          // ESC 키 처리
                          textarea.onkeydown = function(e) {
                              if (e.key === 'Enter' && !e.shiftKey) {
                                  textarea.blur();
                              } else if (e.key === 'Escape') {
                                  td.innerHTML = oldValue.replace(/\n/g, '<br>');
                                  restoreTdStyle();
                                  setTableEditingState(false);
                              }
                          };
                      } else {
                          console.log('일반 필드 스타일 적용 - 타입:', type);
                          // 일반 필드의 경우 기존 스타일 유지
                          input.style.position = 'absolute';
                          input.style.left = '0';
                          input.style.top = '0';
                          input.style.width = 'max-content';
                          input.style.minWidth = '100%';
                          input.style.background = '#fffbe6';
                          input.style.zIndex = '10';
                          input.style.border = 'none';
                          input.style.fontSize = 'inherit';
                          input.style.fontFamily = 'inherit';
                          input.style.lineHeight = 'inherit';
                          input.style.padding = '0';
                          input.style.margin = '0';
                      }
                      
                      td.innerHTML = '';
                      td.appendChild(input);
                      input.focus();
                      if(inputType === 'text') input.select();
                      
                      // input 높이 자동 조정 함수 (메모 필드가 아닌 경우)
                      function adjustInputHeight() {
                          if (inputType === 'text' && !(type === '매출' || type.includes('매출')) && !(type === '메모' || type.includes('메모'))) {
                              // 텍스트 길이에 따라 높이 조정
                              const textLength = input.value.length;
                              if (textLength > 50) {
                                  const lines = Math.ceil(textLength / 50);
                                  const newHeight = Math.min(36 + (lines - 1) * 20, 200);
                                  input.style.height = newHeight + 'px';
                              } else {
                                  input.style.height = '36px';
                              }
                          }
                      }
                      
                      // 초기 높이 조정
                      adjustInputHeight();
                      
                      // 입력 시 높이 조정
                      if (inputType === 'text' && !(type === '매출' || type.includes('매출')) && !(type === '메모' || type.includes('메모'))) {
                          input.addEventListener('input', adjustInputHeight);
                      }
                      
                      input.onkeydown = function(e) {
                          if (e.key === 'Enter') input.blur();
                          if (e.key === 'Escape') {
                              if(type === '회사명') {
                                  const nameTextDiv = td.querySelector('.name-text');
                                  if(nameTextDiv) nameTextDiv.innerText = oldValue;
                                  if(input.parentNode) input.parentNode.removeChild(input);
                              } else {
                                  td.innerText = oldValue;
                              }
                              td.style.width = '';
                          }
                      };
                  }
              };
          }
      });
  }
  
  // 새 행 필드 값 저장 함수 (수정됨)
  function saveNewRowField(tr, field, value) {
      const currentId = tr.getAttribute('data-id');
      
      // 매출 필드인 경우 한국어 단위를 숫자로 변환
      let processedValue = value;
      if (field === '매출' || field.includes('매출')) {
          processedValue = parseKoreanCurrency(value).toString();
      }
      
      // 임시 ID인 경우 (새 행 생성)
      if (currentId && currentId.startsWith('temp_')) {
          console.log('새 행 생성 중...');
          fetch('/sales/create_new_row/', {
              method: 'POST',
              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
              body: 'field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(processedValue)
          }).then(function(response) {
              return response.json();
          }).then(function(data) {
              if (data.success && data.id) {
                  // 임시 ID를 실제 ID로 변경
                  tr.setAttribute('data-id', data.id);
                  tr.removeAttribute('data-is-new');
                  
                  // 실시간 동기화
                  syncTableAndKanban(field);
                  
                  // 종속된 행들 업데이트
                  if (typeof updateDependentRows === 'function') {
                      updateDependentRows(data.id, field, processedValue);
                  }
                  
                  // F/U 일정 필드인 경우 캘린더 새로고침
                  if (field === 'F/U 일정' && window.calendar) {
                      window.calendar.refetchEvents();
                  }
                  
                  // datetime 타입 필드인 경우 캘린더 리렌더링
                  const fieldElement = tr.querySelector(`td[data-field="${field}"]`);
                  if (fieldElement && fieldElement.getAttribute('data-type') === 'datetime' && window.calendar) {
                      window.calendar.refetchEvents();
                  }
              }
          }).catch(function(error) {
              console.error(`새 행 생성 중 오류:`, error);
              alert('새 행 생성 중 오류 발생: ' + error.message);
          });
      }
      // 실제 ID가 있는 경우 (기존 행 업데이트)
      else if (currentId && !currentId.startsWith('temp_')) {
          console.log('기존 행 업데이트 중...');
          fetch('/sales/update_row_field/', {
              method: 'POST',
              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
              body: 'id=' + encodeURIComponent(currentId) + '&field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(processedValue)
          }).then(function(response) {
              return response.json();
          }).then(function(data) {
              if (data.success) {
                  // 실시간 동기화
                  syncTableAndKanban(field);
                  
                  // 종속된 행들 업데이트
                  if (typeof updateDependentRows === 'function') {
                      updateDependentRows(currentId, field, processedValue);
                  }
                  
                  // F/U 일정 필드인 경우 캘린더 새로고침
                  if (field === 'F/U 일정' && window.calendar) {
                      window.calendar.refetchEvents();
                  }
                  
                  // datetime 타입 필드인 경우 캘린더 리렌더링
                  const fieldElement = tr.querySelector(`td[data-field="${field}"]`);
                  if (fieldElement && fieldElement.getAttribute('data-type') === 'datetime' && window.calendar) {
                      window.calendar.refetchEvents();
                  }
              } else {
                  console.error(`${field} 필드 업데이트 실패:`, data.error);
                  alert('업데이트 실패: ' + (data.error || ''));
              }
          }).catch(function(error) {
              console.error(`${field} 필드 업데이트 중 오류:`, error);
              alert('업데이트 중 오류 발생: ' + error.message);
          });
      } else {
          console.error('유효하지 않은 행 ID:', currentId);
      }
  }
  
  // 새 행용 드롭다운 함수 (Attribute 시스템)
  function openNewRowAttributeDropdown(td, type, currentValue, currentSubregion, tr) {
      console.log('openNewRowAttributeDropdown 호출:', type, currentValue);
      
      // 기존 dropdown_manager.js의 openDropdown 함수 사용
      if (typeof openDropdown === 'function') {
          const rowId = tr.getAttribute('data-id');
          openDropdown(td, type, rowId, currentValue, currentSubregion);
      } else {
          console.error('openDropdown 함수를 찾을 수 없습니다. dropdown_manager.js가 로드되었는지 확인해주세요.');
      }
  }
  
  // 새 행 드롭다운 항목에 이벤트 바인딩하는 함수
  function bindNewRowDropdownItemEvents(li, type, tr) {
      // 컬러피커 이벤트
      const colorInput = li.querySelector('input[data-color-edit]');
      if(colorInput) {
          // 색상 변경 이벤트 (색상 선택 완료 시)
          colorInput.onchange = function(e){
              e.stopPropagation();
              e.preventDefault();
              
              fetch('/sales/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + colorInput.getAttribute('data-color-edit') + '&color=' + encodeURIComponent(colorInput.value), {
                  method: 'PUT'
              }).then(r => r.json()).then(data => {
                  if(data.success) {
                      // 색상 변경 즉시 반영
                      const span = li.querySelector('span[data-option-id]');
                      span.style.background = hexToRgba(colorInput.value, 0.18);
                      
                      // 실시간 동기화 - 드롭다운 옵션 색상 변경도 테이블과 칸반보드에 반영
                      syncTableAndKanban(type);
                      
                      // 색상 변경 후 추가 동기화 처리
                      setTimeout(() => {
                          // 테이블 셀들의 색상 정보를 다시 업데이트
                          const cells = document.querySelectorAll(`td[data-field="${type}"]`);
                          cells.forEach(cell => {
                              const currentValue = cell.getAttribute('data-value');
                              if (currentValue) {
                                  // 해당 셀의 색상 정보를 즉시 업데이트
                                  const pill = cell.querySelector('.dropdown-pill');
                                  if (pill) {
                                      pill.style.background = hexToRgba(colorInput.value, 0.18);
                                  }
                              }
                          });
                      }, 100);
                  }
              }).catch(error => {
                  console.error('색상 변경 실패:', error);
              });
          };
          
          // 실시간 색상 변경 이벤트 (색상 선택 중)
          colorInput.addEventListener('input', function(e) {
              e.stopPropagation();
              const optionId = this.getAttribute('data-color-edit');
              const newColor = this.value;
              
              // 드롭다운 내부 색상 실시간 업데이트
              const span = li.querySelector('span[data-option-id]');
              if (span) {
                  span.style.background = hexToRgba(newColor, 0.18);
              }
              
              // 테이블 셀들의 색상 정보를 실시간으로 업데이트
              const cells = document.querySelectorAll(`td[data-field="${type}"]`);
              cells.forEach(cell => {
                  const currentValue = cell.getAttribute('data-value');
                  if (currentValue) {
                      try {
                          // JSON 형태로 저장된 다중선택 값인지 확인
                          const parsed = JSON.parse(currentValue);
                          if (Array.isArray(parsed) && parsed.length > 0) {
                              // 다중선택 값 처리 - 해당 옵션 ID가 포함된 경우 색상 업데이트
                              if (parsed.includes(Number(optionId))) {
                                  const pill = cell.querySelector('.dropdown-pill');
                                  if (pill) {
                                      pill.style.background = hexToRgba(newColor, 0.18);
                                  }
                              }
                          } else {
                              // 단일 선택 값 처리
                              if (Number(currentValue) === Number(optionId)) {
                                  const pill = cell.querySelector('.dropdown-pill');
                                  if (pill) {
                                      pill.style.background = hexToRgba(newColor, 0.18);
                                  }
                              }
                          }
                      } catch (e) {
                          // JSON 파싱 실패 시 단일 값으로 처리
                          if (Number(currentValue) === Number(optionId)) {
                              const pill = cell.querySelector('.dropdown-pill');
                              if (pill) {
                                  pill.style.background = hexToRgba(newColor, 0.18);
                              }
                          }
                      }
                  }
              });
          });
          
          // 컬러피커 클릭 시 드롭다운이 닫히지 않도록 추가 이벤트 처리
          colorInput.addEventListener('click', function(e) {
              e.stopPropagation();
          });
          
          colorInput.addEventListener('mousedown', function(e) {
              e.stopPropagation();
          });
      }
      
      // 삭제 버튼 이벤트
      const delBtn = li.querySelector('button[data-del]');
      if(delBtn) {
          delBtn.onclick = function(e){
              e.stopPropagation();
              if(confirm('삭제할까요?')) {
                  fetch('/sales/dropdown_options/?field=' + encodeURIComponent(type) + '&id=' + delBtn.getAttribute('data-del'), {
                      method: 'DELETE'
                  }).then(r => r.json()).then(data => {
                      if(data.success) {
                          li.remove();
                          
                          // 실시간 동기화 - 드롭다운 옵션 삭제도 테이블과 칸반보드에 반영
                          syncTableAndKanban(type);
                      }
                  }).catch(error => {
                      console.error('삭제 실패:', error);
                      alert('삭제에 실패했습니다.');
                  });
              }
          };
      }
      
      // 수정 버튼 이벤트
      const editBtn = li.querySelector('button[data-edit]');
      if(editBtn) {
          editBtn.addEventListener('click', function(e) {
              e.stopPropagation();
              const optionId = this.getAttribute('data-edit');
              const optionContainer = this.closest('.dropdown-option-container');
              const optionText = optionContainer.querySelector('span');
              const oldText = optionText.textContent;
              
              // 입력 필드 생성
              const input = document.createElement('input');
              input.type = 'text';
              input.value = oldText;
              input.className = 'table-edit-input';
              input.style.cssText = `
                  flex: 1;
                  padding: 4px 8px;
                  border: 1px solid #007bff;
                  border-radius: 3px;
                  font-size: 12px;
                  margin-right: 4px;
                  background: white;
                  outline: none;
              `;
              
              // 기존 텍스트를 입력 필드로 교체
              optionText.style.display = 'none';
              optionText.parentNode.insertBefore(input, optionText);
              
              // 포커스와 선택을 지연시켜 DOM 업데이트 완료 후 실행
              setTimeout(() => {
                  input.focus();
                  input.select();
              }, 10);
              
              // 수정 완료 처리 함수
              function saveEdit() {
                  const newText = input.value.trim();
                  if (!newText) {
                      alert('옵션명을 입력해주세요.');
                      return;
                  }
                  
                  fetch(`/sales/dropdown_options/?field=${encodeURIComponent(type)}&id=${optionId}&name=${encodeURIComponent(newText)}`, {
                      method: 'PUT',
                      headers: {
                          'X-CSRFToken': getCsrfToken()
                      }
                  })
                  .then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          optionText.textContent = newText;
                          optionText.style.display = '';
                          input.remove();
                          
                          // 실시간 동기화
                          syncTableAndKanban(type);
                          // 상태 속성인 경우 상태 탭 새로고침
                          if (window.statusAttributeName && type === window.statusAttributeName && typeof window.refreshStatusTabs === 'function') {
                              setTimeout(() => { window.refreshStatusTabs(); }, 100);
                          }
                      } else {
                          alert('옵션 수정 실패: ' + (data.error || ''));
                          optionText.style.display = '';
                          input.remove();
                      }
                  })
                  .catch(error => {
                      alert('옵션 수정 중 오류가 발생했습니다: ' + error.message);
                      optionText.style.display = '';
                      input.remove();
                  });
              }
              
              // 취소 처리 함수
              function cancelEdit() {
                  optionText.style.display = '';
                  input.remove();
              }
              
              input.onblur = function() {
                  setTimeout(() => {
                      if (input.parentNode) {
                          saveEdit();
                      }
                  }, 100);
              };
              
              input.onkeydown = function(e) {
                  if (e.key === 'Enter') {
                      saveEdit();
                  } else if (e.key === 'Escape') {
                      cancelEdit();
                  }
              };
          });
      }
  }
  
  // 테이블 초기화 시 외부 클릭 이벤트 리스너 추가
  document.addEventListener('click', function(event) {
      // 드롭다운이 열려있고, 클릭한 위치가 드롭다운 외부인 경우에만 닫기
      if (window.dropdown && !window.dropdown.contains(event.target)) {
          // 지역/상세지역 드롭다운인 경우 보호
          const isRegionDropdown = window.dropdown && window.dropdown.getAttribute('data-region-type');
          
          // 드롭다운을 여는 버튼을 클릭한 경우는 제외
          const clickedElement = event.target;
          const isDropdownButton = clickedElement.classList.contains('add-btn') || 
                                   clickedElement.onclick && clickedElement.onclick.toString().includes('openDropdown');
          
          if (!isDropdownButton) {
              // 지역/상세지역 드롭다운인 경우 완전히 보호
              if (isRegionDropdown) {
                  console.log('diary_table.js: 지역 드롭다운 감지, 전역 클릭 이벤트 무시');
                  return; // 지역 드롭다운인 경우 아무것도 하지 않음
              } else {
                  closeDropdown();
              }
          }
      }
  });
  
  // ESC 키로 드롭다운 닫기
  document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape' && window.dropdown) {
          closeDropdown();
      }
  });
  
  // 숫자 필드 업데이트 시 콤마 포맷팅 적용
  function updateCellValue(id, fieldName, value, element) {
      
      // 새 행인 경우
      if (id && id.startsWith('temp_')) {
          saveNewRowField(element.parentElement, fieldName, value);
          return;
      }
      
      // 기존 행인 경우
      console.log('update_row_field, 테이블2')
      fetch('/sales/update_row_field/', {
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: 'id=' + id + '&field=' + encodeURIComponent(fieldName) + '&value=' + encodeURIComponent(value)
      })
      .then(function(response) {
          return response.json();
      })
      .then(function(data) {
          if (!data.success) {
              alert('수정 실패: ' + (data.error || ''));
              return;
          }
          
          // 모든 필드에 대해 현재 셀만 업데이트 (드롭다운 포함)
          updateTableCell(id, fieldName, value);
          
          // 종속된 행들 찾아서 업데이트
          updateDependentRows(id, fieldName, value);
          
          // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우에만 즉시 필터 적용
          if (window.currentStatusTab !== null && fieldName === window.statusAttributeName) {
              // 해당 행의 상태 셀 업데이트
              const row = document.querySelector(`tr[data-id="${id}"]`);
              if (row) {
                  const statusCell = row.querySelector(`td[data-field="${fieldName}"]`);
                  if (statusCell) {
                      // 새로운 값으로 data-value 업데이트
                      statusCell.setAttribute('data-value', value);
                      
                      // 상태 필터 즉시 재적용
                      setTimeout(() => {
                          if (typeof applyStatusFilter === 'function') {
                              applyStatusFilter();
                          }
                      }, 50);
                  }
              }
          }
          
          // datetime 필드인 경우 캘린더 리렌더링
          const fieldElement = document.querySelector(`td[data-field="${fieldName}"]`);
          if (fieldElement && fieldElement.getAttribute('data-type') === 'datetime' && window.calendar) {
              window.calendar.refetchEvents();
          }
          
          // 필요시 테이블/보드 갱신
          refreshCalendarSettings();
      })
      .catch(function(error) {
          console.error('업데이트 중 오류:', error);
          alert('업데이트 중 오류가 발생했습니다.');
      });
  }
  
  // 종속된 행들을 찾아서 업데이트하는 함수
  function updateDependentRows(updatedRowId, fieldName, value) {
      
      // 모든 필드에 대해 종속된 행들 찾기 (매출 관련 필드 제한 제거)
      // 서버에서 종속된 행들 정보 가져오기
      fetch('/sales/get_dependent_rows/', {
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: 'row_id=' + encodeURIComponent(updatedRowId) + '&field=' + encodeURIComponent(fieldName)
      })
      .then(response => response.json())
      .then(data => {
          if (data.success && data.dependent_rows) {
              
              // 드롭다운 필드인지 확인
              const dropdownFields = (window.ATTR_FIELDS || [])
                  .filter(attr => attr.attributeType_name === 'dropdown')
                  .map(attr => attr.name);
              
              const isDropdownField = dropdownFields.includes(fieldName);
              
              // 각 종속된 행의 셀 업데이트
              data.dependent_rows.forEach(depRow => {
                  if (depRow.row_id && depRow.field && depRow.value !== undefined) {
                      
                      // 드롭다운 필드인 경우 옵션 정보를 가져와서 처리
                      let displayValue = depRow.value;
                      if (isDropdownField && depRow.value) {
                          // 값이 숫자인 경우에만 ID를 이름으로 변환
                          if (!isNaN(depRow.value)) {
                              // 드롭다운 옵션 정보 가져와서 ID를 이름으로 변환
                              fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName))
                                  .then(response => {
                                      if (!response.ok) {
                                          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                                      }
                                      return response.json();
                                  })
                                  .then(optionData => {
                                      if (optionData.options && Array.isArray(optionData.options)) {
                                          const option = optionData.options.find(opt => opt.id == depRow.value);
                                          if (option) {
                                              displayValue = option.option;
                                          } else {
                                              // 옵션을 찾지 못한 경우 원래 값 사용
                                              displayValue = depRow.value;
                                          }
                                      } else {
                                          // 옵션 데이터가 없는 경우 원래 값 사용
                                          displayValue = depRow.value;
                                      }
                                      
                                      // 약간의 지연을 두고 업데이트 (DOM 업데이트 보장)
                                      setTimeout(() => {
                                          updateTableCell(depRow.row_id, depRow.field, displayValue);
                                      }, 10);
                                  })
                                  .catch(error => {
                                      console.error('드롭다운 옵션 정보 가져오기 실패:', error);
                                      // 실패 시 원래 값으로 업데이트 (updateTableCell에서 pill 형태로 처리됨)
                                      setTimeout(() => {
                                          updateTableCell(depRow.row_id, depRow.field, depRow.value);
                                      }, 10);
                                  });
                          } else {
                              // 값이 이미 텍스트인 경우 그대로 사용
                              setTimeout(() => {
                                  updateTableCell(depRow.row_id, depRow.field, displayValue);
                              }, 10);
                          }
                      } else {
                          // 일반 필드인 경우 그대로 사용
                          setTimeout(() => {
                              updateTableCell(depRow.row_id, depRow.field, displayValue);
                          }, 10);
                      }
                  }
              });
          } else {
              console.log('종속된 행이 없거나 오류 발생:', data);
          }
      })
      .catch(error => {
          console.error('종속된 행들 업데이트 실패:', error);
      });
      
      // 드롭다운 필드인 경우 관련 셀들 동기화
      if (dropdownFields.includes(fieldName)) {
          // 드롭다운 옵션 동기화는 기존 syncTableAndKanban 함수에서 처리
          if (typeof syncTableAndKanban === 'function') {
              syncTableAndKanban(fieldName);
          }
      }
  }
  
  // 테이블과 칸반보드 실시간 동기화 함수 (개선된 버전)
  function syncTableAndKanban(fieldName) {
      // 테이블 업데이트 (즉시 실행)
      updateTableDropdownOptions(fieldName);
      
      // 테이블 편집 중이 아닐 때만 칸반보드 업데이트
      if (!isTableEditing) {
          debounceKanbanUpdate(fieldName);
      } else {
          // 편집 중이면 대기열에 추가
          pendingKanbanUpdates.add(fieldName);
      }
  }
  
  // 테이블 드롭다운 옵션 업데이트 함수 (분리)
  function updateTableDropdownOptions(fieldName) {
      if (isTableUpdating) return;
      isTableUpdating = true;
      
      // 드롭다운 옵션이 수정된 경우 모든 관련 셀 즉시 업데이트
      const dropdownFields = (window.ATTR_FIELDS || [])
          .filter(attr => attr.attributeType_name === 'dropdown')
          .map(attr => attr.name);
      
      if (fieldName && dropdownFields.includes(fieldName)) {
          // 서버에서 최신 옵션 정보 가져와서 모든 관련 셀 업데이트
          fetch('/sales/dropdown_options/?field=' + encodeURIComponent(fieldName))
              .then(response => response.json())
              .then(data => {
                  if (data.options) {
                      // 해당 필드를 사용하는 모든 셀 찾기
                      const cells = document.querySelectorAll(`td[data-field="${fieldName}"]`);
                      
                      cells.forEach(cell => {
                          const currentValue = cell.getAttribute('data-value');
                          const currentText = cell.textContent.trim();
                          
                          if (currentValue) {
                              try {
                                  // JSON 형태로 저장된 다중선택 값인지 확인
                                  const parsed = JSON.parse(currentValue);
                                  if (Array.isArray(parsed) && parsed.length > 0) {
                                      // 다중선택 값 처리 - 숫자 비교로 수정
                                      const selectedOptions = data.options.filter(opt => parsed.includes(Number(opt.id)));
                                      let htmlContent = '';
                                      selectedOptions.forEach((opt, index) => {
                                          const color = opt.color ? hexToRgba(opt.color, 0.18) : '#eee';
                                          htmlContent += `<div class="dropdown-pill" style="background:${color}; color:#333; display:block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; margin-bottom:2px;">${opt.option}</div>`;
                                      });
                                      
                                      if (htmlContent) {
                                          cell.innerHTML = htmlContent;
                                          cell.setAttribute('data-value', JSON.stringify(parsed));
                                      } else {
                                          cell.innerHTML = '<div class="dropdown-pill" style="background:#eee; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">선택 없음</div>';
                                          cell.setAttribute('data-value', '');
                                      }
                                  } else if (Array.isArray(parsed) && parsed.length === 0) {
                                      // 빈 배열인 경우
                                      cell.innerHTML = '<div class="dropdown-pill" style="background:#eee; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">선택 없음</div>';
                                      cell.setAttribute('data-value', '');
                                  } else {
                                      // 단일 선택 값 처리 (기존 로직)
                                      const option = data.options.find(opt => opt.id == currentValue);
                                      if (option) {
                                          const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                                          cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                                          cell.setAttribute('data-value', option.id);
                                      } else {
                                          // data-value가 일치하지 않으면 텍스트로 찾기
                                          const textOption = data.options.find(opt => opt.option === currentText);
                                          if (textOption) {
                                              const color = textOption.color ? hexToRgba(textOption.color, 0.18) : '#eee';
                                              cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${textOption.option}</div>`;
                                              cell.setAttribute('data-value', textOption.id);
                                          } else {
                                              // 옵션을 찾지 못한 경우에도 pill 형태로 표시
                                              console.log(`옵션을 찾지 못함, pill 형태로 표시: ${currentValue}`);
                                              cell.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${currentValue}</div>`;
                                              cell.setAttribute('data-value', currentValue);
                                          }
                                      }
                                  }
                              } catch (e) {
                                  // JSON 파싱 실패 시 단일 값으로 처리
                                  const option = data.options.find(opt => opt.id == currentValue);
                                  if (option) {
                                      const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                                      cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                                      cell.setAttribute('data-value', option.id);
                                  } else {
                                      // 옵션을 찾지 못한 경우에도 pill 형태로 표시
                                      console.log(`JSON 파싱 실패 후 옵션을 찾지 못함, pill 형태로 표시: ${currentValue}`);
                                      cell.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${currentValue}</div>`;
                                      cell.setAttribute('data-value', currentValue);
                                  }
                              }
                          }
                      });
                      
                      console.log('드롭다운 옵션 동기화 완료');
                  }
              })
              .catch(error => {
                  console.error('드롭다운 옵션 업데이트 실패:', error);
              })
              .finally(() => {
                  isTableUpdating = false;
              });
      } else {
          isTableUpdating = false;
      }
  }
  
  // 칸반보드 업데이트 디바운싱 함수 (개선된 버전)
  function debounceKanbanUpdate(fieldName) {
      // 테이블 편집 중이면 대기열에만 추가하고 실행하지 않음
      if (isTableEditing) {
          pendingKanbanUpdates.add(fieldName);
          return;
      }
      
      // 대기 중인 업데이트에 추가
      pendingKanbanUpdates.add(fieldName);
      
      // 기존 타이머가 있으면 취소
      if (kanbanUpdateTimer) {
          clearTimeout(kanbanUpdateTimer);
      }
      
      // 800ms 후에 칸반보드 업데이트 실행 (더 긴 지연시간으로 변경)
      kanbanUpdateTimer = setTimeout(() => {
          // 모든 대기 중인 업데이트를 한 번에 처리
          const updatesToProcess = Array.from(pendingKanbanUpdates);
          pendingKanbanUpdates.clear();
          
          // 가장 최근의 업데이트만 처리 (중복 제거)
          const latestUpdate = updatesToProcess[updatesToProcess.length - 1];
          if (latestUpdate) {
              updateKanbanIfNeeded(latestUpdate);
          }
      }, 800);
  }
  
  // 칸반보드 업데이트 필요 여부 확인 및 실행 (개선된 버전)
  function updateKanbanIfNeeded(fieldName) {
      // 테이블 편집 중이면 업데이트를 건너뜀
      if (isTableEditing) {
          console.log('테이블 편집 중이므로 칸반보드 업데이트를 건너뜁니다.');
          return;
      }
      
      if (isKanbanUpdating) {
          console.log('칸반보드 업데이트가 이미 진행 중입니다. 대기열에 추가합니다.');
          pendingKanbanUpdates.add(fieldName);
          return;
      }
      
      // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우 새로고침
      const currentKanbanAttr = document.getElementById('kanbanAttributeSelect') ? 
          document.getElementById('kanbanAttributeSelect').value : 
          window.SELECTED_KANBAN_ATTR;
      
      if (currentKanbanAttr && fieldName === currentKanbanAttr) {
          console.log('칸반보드 속성이 변경되어 새로고침합니다:', fieldName);
          if (typeof refreshKanban === 'function') {
              isKanbanUpdating = true;
              refreshKanban();
              // 칸반보드 업데이트 완료 후 플래그 리셋
              setTimeout(() => {
                  isKanbanUpdating = false;
                  // 대기 중인 업데이트가 있으면 처리
                  if (pendingKanbanUpdates.size > 0) {
                      const nextUpdate = Array.from(pendingKanbanUpdates)[0];
                      pendingKanbanUpdates.delete(nextUpdate);
                      updateKanbanIfNeeded(nextUpdate);
                  }
              }, 1500); // 1.5초 후 플래그 리셋
          }
      }
  }
  
  // CSRF 토큰 가져오기 함수
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
  
  // 행 삭제 함수
  function deleteRow(rowId) {
      if (!confirm('이 행을 삭제하시겠습니까?\n\n삭제된 데이터는 복구할 수 없습니다.')) {
          return;
      }
      
      fetch('/sales/delete_row/', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({
              row_id: rowId
          })
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              // 테이블에서 행 제거
              const row = document.querySelector(`tr[data-id="${rowId}"]`);
              if (row) {
                  row.remove();
              }
              
              // 칸반 보드와 캘린더 동기화
              syncTableAndKanban();
              
              // 항상 칸반보드와 캘린더 리렌더링
              if (typeof refreshKanban === 'function') {
                  refreshKanban();
              }
              if (typeof refreshCalendar === 'function') {
                  refreshCalendar();
              }
              
              alert('행이 성공적으로 삭제되었습니다.');
          } else {
              alert('오류: ' + data.error);
          }
      })
      .catch(error => {
          console.error('Error:', error);
          alert('행 삭제 중 오류가 발생했습니다.');
      });
  }
  
  // 매출 필드 실시간 변환 함수 (테이블용)
  function formatSalesInputRealtimeTable(input) {
      const value = input.value.replace(/[^\d]/g, '');
      const numericValue = parseInt(value) || 0;
      
      if (numericValue >= 1000000) {
          const convertedValue = Math.floor(numericValue / 10000);
          if (convertedValue >= 1) {
              input.value = convertedValue;
          } else {
              input.value = numericValue.toLocaleString();
          }
      } else if (numericValue > 0) {
          input.value = numericValue.toLocaleString();
      }
  }

  // 새로 만들기 버튼 이벤트 바인딩
  window.addNewRow = function() {
      console.log('=== addNewRow 함수 호출 시작 ===');
      
      // 중복 클릭 방지를 위한 전역 변수
      if (window.isAddingNewRow) {
          console.log('이미 새 행을 추가 중입니다. 중복 클릭 방지.');
          return;
      }
      window.isAddingNewRow = true;

              // 현재 선택된 상태 탭 확인
              let statusField = null;
              let statusValue = null;
              
              // 방법 1: 전역 변수에서 가져오기
              if (window.currentStatusTab !== null && window.statusAttributeName) {
                  statusField = window.statusAttributeName;
                  statusValue = window.currentStatusTab;
                  console.log(`전역 변수에서 상태 필드 설정: ${statusField} = ${statusValue}`);
              } else {
                  // 방법 2: 활성화된 탭에서 직접 가져오기
                  const activeTab = document.querySelector('.status-tab.active');
                  if (activeTab) {
                      const statusId = activeTab.getAttribute('data-status-id');
                      if (statusId && statusId !== 'all') {
                          // 상태 속성명을 찾기 위해 서버에 요청
                          fetch('/sales/get_status_tabs/')
                              .then(response => response.json())
                              .then(data => {
                                  if (data.success && data.attribute_name) {
                                      statusField = data.attribute_name;
                                      statusValue = statusId;
                                      console.log(`탭에서 상태 필드 설정: ${statusField} = ${statusValue}`);
                                      
                                      // 상태 정보를 찾은 후 새 행 생성 요청
                                      createNewRowWithStatus(statusField, statusValue);
                                  } else {
                                      console.log('상태 정보를 찾을 수 없음, 기본값으로 새 행 생성');
                                      createNewRowWithStatus(null, null);
                                  }
                              })
                              .catch(error => {
                                  console.error('상태 정보 조회 오류:', error);
                                  createNewRowWithStatus(null, null);
                              });
                          return; // 비동기 처리이므로 여기서 종료
                      }
                  }
                  console.log('상태 탭이 없거나 전체 탭이 활성화됨');
                  createNewRowWithStatus(null, null);
                  return;
              }

              // 동기적으로 처리할 수 있는 경우
              createNewRowWithStatus(statusField, statusValue);
              
              function createNewRowWithStatus(statusField, statusValue) {
                  // 서버에 새 행 생성 요청
                  let requestBody = 'field=' + encodeURIComponent('회사명') + '&value=' + encodeURIComponent('새 항목');
                  
                  // 상태 필드가 있으면 추가
                  if (statusField && statusValue) {
                      requestBody += '&status_field=' + encodeURIComponent(statusField) + '&status_value=' + encodeURIComponent(statusValue);
                  }

                  console.log('서버 요청 데이터:', requestBody);

                  // --- SCROLL FLAG SET HERE ---
                  window.scrollTableToBottomAfterRefresh = true;

                  fetch('/sales/create_new_row/', {
                      method: 'POST',
                      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                      body: requestBody
                  })
                  .then(function(response) { 
                      console.log('서버 응답 상태:', response.status);
                      if (!response.ok) {
                          throw new Error('Network response was not ok: ' + response.status);
                      }
                      return response.json(); 
                  })
                  .then(function(data) {
                      console.log('서버 응답 데이터:', data);
                      if (data.success) {
                          console.log('새 행 생성 성공! 새 행 ID:', data.id);
                          
                          // diary_list.html의 refreshTable 함수 호출
                          console.log('refreshTable 함수 호출 시도...');
                          console.log('typeof refreshTable:', typeof refreshTable);
                          console.log('typeof window.refreshTable:', typeof window.refreshTable);
                          
                          let refreshFunction = null;
                          if (typeof refreshTable === 'function') {
                              refreshFunction = refreshTable;
                              console.log('refreshTable 함수를 직접 사용');
                          } else if (typeof window.refreshTable === 'function') {
                              refreshFunction = window.refreshTable;
                              console.log('window.refreshTable 함수를 사용');
                          }
                          
                          if (refreshFunction) {
                              console.log('refreshTable 함수 호출 시작...');
                              try {
                                  refreshFunction();
                                  console.log('refreshTable 함수 호출 완료');
                              } catch (error) {
                                  console.error('refreshTable 함수 실행 중 오류:', error);
                                  console.log('오류로 인해 location.reload() 호출');
                                  location.reload();
                              }
                          } else {
                              console.error('refreshTable 함수가 정의되지 않음');
                              console.log('location.reload() 호출');
                              location.reload();
                          }
                      } else {
                          console.error('새 행 생성 실패:', data.error);
                          alert('새 행 생성 실패: ' + (data.error || ''));
                      }
                  })
                  .catch(function(error) {
                      console.error('새 행 생성 중 오류:', error);
                      alert('새 행 생성 중 오류: ' + error.message);
                  })
                  .finally(function() {
                      window.isAddingNewRow = false;
                      console.log('=== addNewRow 함수 완료 ===');
                  });
              }
      }

  // === dropdown 속성명 동적 추출 함수 ===
  function getDropdownFields() {
      return (window.ATTR_FIELDS || [])
          .filter(attr => attr.attributeType_name === 'dropdown')
          .map(attr => attr.name);
  }

  // 기존 데이터 정리 함수
  function cleanupExistingData() {
      console.log('기존 데이터 정리 시작');
      // 모든 드롭다운 필드의 data-value를 확인하고 정리
      const dropdownFields = getDropdownFields();
      dropdownFields.forEach(field => {
          const cells = document.querySelectorAll(`td[data-field="${field}"]`);
          cells.forEach(cell => {
              const currentValue = cell.getAttribute('data-value');
              if (currentValue) {
                  try {
                      // JSON 형태인지 확인
                      const parsed = JSON.parse(currentValue);
                      if (Array.isArray(parsed) && parsed.length > 0) {
                          // 배열인 경우 첫 번째 값만 사용
                          cell.setAttribute('data-value', parsed[0]);
                          // UI도 업데이트
                          const optionId = parsed[0];
                          // 서버에서 옵션 정보 가져와서 UI 업데이트
                          fetch('/sales/dropdown_options/?field=' + encodeURIComponent(field))
                              .then(response => response.json())
                              .then(data => {
                                  if (data.options) {
                                      const option = data.options.find(opt => opt.id == optionId);
                                      if (option) {
                                          const color = option.color ? hexToRgba(option.color, 0.18) : '#eee';
                                          cell.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${option.option}</div>`;
                                      }
                                  }
                              })
                              .catch(error => {
                                  console.error('옵션 정보 가져오기 실패:', error);
                              });
                      }
                  } catch (e) {
                      // JSON이 아닌 경우 그대로 유지
                      console.log(`${field} 필드 유지: ${currentValue}`);
                  }
              }
          });
      });
      console.log('기존 데이터 정리 완료');
  }

  // 페이지 로드 시 데이터 정리
  document.addEventListener('DOMContentLoaded', function() {
      // 기존 데이터 정리 함수 제거 - 다중선택 값들이 단일 값으로 변환되는 것을 방지
      // setTimeout(() => {
      //     cleanupExistingData();
      // }, 1000);
  });

  // === 다중선택 드롭다운 셀을 옵션명 pill로 변환하는 함수 ===
  function renderDropdownPills() {
      console.log('renderDropdownPills 함수 시작');
      
      // 다중선택 드롭다운 필드 목록 동적 추출
      const dropdownFields = getDropdownFields();
      
      dropdownFields.forEach(field => {
          const cells = document.querySelectorAll(`td[data-field="${field}"]`);
          
          cells.forEach(cell => {
              const currentValue = cell.getAttribute('data-value');
              
              if (!currentValue) {
                  cell.innerHTML = '<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">선택 없음</div>';
                  return;
              }
              
              let parsed = null;
              try {
                  parsed = JSON.parse(currentValue);
              } catch (e) {
                  parsed = currentValue;
              }
              
              // 서버에서 옵션 정보를 가져와서 처리
              // window.DROPDOWN_OPTIONS에서 먼저 확인, 없으면 서버에서 가져오기
              let options = null;
              if (window.DROPDOWN_OPTIONS && window.DROPDOWN_OPTIONS[field]) {
                  options = window.DROPDOWN_OPTIONS[field];
              }
              
              if (options) {
                  // 로컬에 있는 옵션 사용
                  processDropdownPillsWithOptions(options, parsed, cell, currentValue);
              } else {
                  // 서버에서 옵션 가져오기 (fallback)
                  fetch('/sales/dropdown_options/?field=' + encodeURIComponent(field))
                      .then(response => {
                          if (!response.ok) {
                              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                          }
                          return response.json();
                      })
                      .then(data => {
                          console.log(`필드 "${field}" 옵션 데이터:`, data);
                          
                          if (!data.options) {
                              console.log(`필드 "${field}" 옵션 데이터가 없음`);
                              cell.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${parsed}</div>`;
                              return;
                          }
                          
                          processDropdownPillsWithOptions(data.options, parsed, cell, currentValue);
                          console.log(`셀 ${field} 업데이트 완료`);
                      })
                      .catch(error => {
                          console.error(`드롭다운 옵션 로드 실패 (${field}):`, error);
                          // 오류 발생 시에도 pill 형태로 표시
                          cell.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${currentValue}</div>`;
                      });
              }
          });
      });
      
      console.log('renderDropdownPills 함수 완료');
  }

  
  
  // 행 드래그앤드롭 재초기화 함수
  function reinitializeRowDragDrop() {
      console.log('행 드래그앤드롭 재초기화 시작');
      
      // 기존 Sortable 인스턴스 제거
      if (window.rowSortable) {
          window.rowSortable.destroy();
          window.rowSortable = null;
      }
      
      // 약간의 지연 후 새로운 Sortable 인스턴스 생성
      setTimeout(() => {
          try {
              const tbody = document.getElementById('entryTbody');
              if (tbody && typeof Sortable !== 'undefined') {
                  window.rowSortable = new Sortable(tbody, {
                      handle: '.drag-handle',
                      animation: 150,
                      onEnd: function (evt) {
                          // 순서 변경 시 서버에 반영
                          const ids = Array.from(document.querySelectorAll('#entryTbody tr[data-id]')).map(tr => tr.getAttribute('data-id'));
                          fetch('/sales/reorder/', {
                              method: 'POST',
                              headers: {'Content-Type': 'application/json'},
                              body: JSON.stringify({order: ids})
                          }).then(res => res.json()).then(data => {
                              if(!data.success) alert('순서 저장 실패: '+data.error);
                          }).catch(() => alert('순서 저장 중 오류 발생'));
                      }
                  });
                  console.log('행 드래그앤드롭 재초기화 완료');
              } else {
                  console.log('tbody 또는 Sortable을 찾을 수 없음');
              }
          } catch (error) {
              console.error('행 드래그앤드롭 재초기화 오류:', error);
          }
      }, 200);
}
  
// 테이블 로딩 표시
function showTableLoading() {
    const tableView = document.getElementById('tableView');
    if (tableView) {
        tableView.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #6c757d;">
                <div style="margin-bottom: 10px;">데이터를 불러오는 중...</div>
                <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto;"></div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
    }
}

// 속성 삭제 함수
function deleteAttribute(attrName) {
    if (!confirm(`"${attrName}" 속성을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없으며, 해당 속성과 관련된 모든 데이터가 삭제됩니다.`)) {
        return;
    }
    
    fetch('/sales/delete_attribute/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `name=${encodeURIComponent(attrName)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // 페이지 새로고침으로 변경사항 반영
            location.reload();
            
            // 칸반보드 필터 업데이트
            refreshKanbanFilter();
            
            // 캘린더 설정 업데이트
            refreshCalendarSettings();
        } else {
            alert('오류: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('속성 삭제 중 오류가 발생했습니다.');
    });
}

// 속성 관리 모달 닫기
function closeAttributeVisibilityModal() {
    console.log('속성 관리 모달 닫기');
    const modal = document.getElementById('attributeVisibilityModal');
    modal.style.display = 'none';
}

// 다중 선택 관련 함수들
function toggleSelectAll(checkbox) {
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    rowCheckboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBulkDeleteButton();
}

function updateBulkDeleteButton() {
    const selectedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const selectedCountSpan = document.getElementById('selectedCount');
    
    if (selectedCheckboxes.length > 0) {
        bulkDeleteBtn.style.display = 'inline-block';
        selectedCountSpan.textContent = selectedCheckboxes.length;
    } else {
        bulkDeleteBtn.style.display = 'none';
        selectedCountSpan.textContent = '0';
    }
}

function bulkDeleteRows() {
    const selectedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
    
    if (selectedCheckboxes.length === 0) {
        alert('삭제할 행을 선택해주세요.');
        return;
    }
    
    const selectedRowIds = Array.from(selectedCheckboxes).map(cb => cb.getAttribute('data-row-id'));
    
    if (!confirm(`선택된 ${selectedRowIds.length}개 행을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
        return;
    }
    
    // 로딩 표시
    const loadingNotification = document.createElement('div');
    loadingNotification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #007bff;
        color: white;
        padding: 15px;
        border-radius: 6px;
        z-index: 1000;
        font-size: 14px;
    `;
    loadingNotification.textContent = `${selectedRowIds.length}개 행을 삭제하는 중...`;
    document.body.appendChild(loadingNotification);
    
    // 선택된 행들을 순차적으로 삭제
    let deletedCount = 0;
    let failedCount = 0;
    
    function deleteNextRow(index) {
        if (index >= selectedRowIds.length) {
            // 모든 삭제 완료
            loadingNotification.remove();
            
            // 결과 알림
            const resultMessage = `삭제 완료: ${deletedCount}개 성공, ${failedCount}개 실패`;
            const resultNotification = document.createElement('div');
            resultNotification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${failedCount === 0 ? '#28a745' : '#dc3545'};
                color: white;
                padding: 15px 20px;
                border-radius: 6px;
                z-index: 1000;
                font-size: 14px;
            `;
            resultNotification.textContent = resultMessage;
            document.body.appendChild(resultNotification);
            
            setTimeout(() => resultNotification.remove(), 3000);
            
            // 즉시 체크박스 상태 초기화 및 삭제 버튼 숨기기
            resetCheckboxes();
            
            // 테이블 새로고침
            refreshTable();
            
            // 칸반보드 새로고침
            if (window.kanbanAttribute) {
                refreshKanban();
            }
            
            // 캘린더 업데이트
            refreshCalendar();
            
            return;
        }
        
        const rowId = selectedRowIds[index];
        
        // deleteRow 함수를 직접 호출하지 않고 서버에 삭제 요청
        fetch('/sales/delete_row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                row_id: rowId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                deletedCount++;
            } else {
                failedCount++;
                console.error(`행 ${rowId} 삭제 실패:`, data.error);
            }
            
            // 다음 행 삭제
            deleteNextRow(index + 1);
        })
        .catch(error => {
            console.error(`행 ${rowId} 삭제 중 오류:`, error);
            failedCount++;
            deleteNextRow(index + 1);
        });
    }
    
    // 첫 번째 행부터 삭제 시작
    deleteNextRow(0);
}

// 테이블 새로고침 시 체크박스 상태 초기화
function resetCheckboxes() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
    }
    
    rowCheckboxes.forEach(cb => {
        cb.checked = false;
    });
    
    updateBulkDeleteButton();
}


// 컬럼 리사이즈 이벤트 감지 및 제목 자동 조정
function initializeColumnResizeListener() {
    document.addEventListener('columnResized', function(e) {
        const column = e.target;
        const width = e.detail.width;
        
        // 해당 컬럼의 제목 요소들 찾기
        const headerContent = column.querySelector('.header-content');
        if (headerContent) {
            // 제목 텍스트 요소들 조정
            const titleElements = headerContent.querySelectorAll('.attribute-name-text, span');
            titleElements.forEach(element => {
                // 최대 너비를 컬럼 너비에 맞게 조정 (패딩과 버튼 공간 고려)
                const maxTitleWidth = Math.max(width - 60, 20); // 최소 20px 보장
                element.style.maxWidth = maxTitleWidth + 'px';
            });
        }
    });
}

// 페이지 로드 시 컬럼 리사이즈 리스너 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeColumnResizeListener();
});

// Helper: Ensure kanbanSettings is loaded before using
async function ensureKanbanSettingsLoaded() {
    if (!window.kanbanSettings || !window.kanbanSettings.filters) {
        try {
            const resp = await fetch('/sales/get_kanban_settings/');
            const data = await resp.json();
            if (data.success && data.settings) {
                window.kanbanSettings = data.settings;
            }
        } catch (e) { /* ignore */ }
    }
}

// ... existing code ...
          // 칸반보드: 어떤 드롭다운 속성이든 변경 시 항상 새로고침 (최적화: 중복 호출 방지)
          if (typeof refreshKanban === 'function') {
              if (!window._kanbanRefreshTimeout) {
                  window._kanbanRefreshTimeout = null;
              }
              if (window._kanbanRefreshTimeout) {
                  clearTimeout(window._kanbanRefreshTimeout);
              }
              // debounce: 100ms 내 중복 호출 방지
              window._kanbanRefreshTimeout = setTimeout(() => {
                  window._kanbanRefreshTimeout = null;
                  if (!window._kanbanRefreshing) {
                      window._kanbanRefreshing = true;
                      refreshKanban();
                      setTimeout(() => { window._kanbanRefreshing = false; }, 500);
                  }
              }, 80);
          }
// ... existing code ...

// At the end of the main refreshTable (the one that updates the DOM and re-binds events):
// After all DOM updates and event bindings, add:
// ... existing code ...
                  // 현재 필터 상태 재적용
                  if (window.filters && Object.keys(window.filters).length > 0) {
                      Object.entries(window.filters).forEach(([column, filterValue]) => {
                          // 필터 입력창에 값 복원
                          const filterInput = document.querySelector(`input[data-column="${column}"]`);
                          if (filterInput) {
                              filterInput.value = filterValue;
                          }
                          // 필터 재적용
                          if (window.originalRows) {
                              window.originalRows.forEach(row => {
                                  let shouldShow = true;
                                  for (const [filterColumn, filterVal] of Object.entries(window.filters)) {
                                      const cellValue = getCellValue(row, filterColumn).toLowerCase();
                                      if (!cellValue.includes(filterVal)) {
                                          shouldShow = false;
                                          break;
                                      }
                                  }
                                  // ... existing code ...
                              });
                          }
                      });
                  }
                  // --- SCROLL TO BOTTOM IF FLAG IS SET ---
                  if (window.scrollTableToBottomAfterRefresh) {
                      const tableView = document.getElementById('tableView');
                      if (tableView) {
                          tableView.scrollTop = tableView.scrollHeight;
                      }
                      window.scrollTableToBottomAfterRefresh = false;
                  }
// ... existing code ...

// 새 행을 위한 드롭다운 옵션을 처리하는 함수
function processDropdownOptionsForNewRow(options, type, td, tr) {
    console.log('processDropdownOptionsForNewRow 시작:', type, options.length);
    
    const currentValue = td.getAttribute('data-value') || '';
    
    // 모달과 동일한 깔끔한 구조로 변경
    let html = `<div style="padding: 8px; border-bottom: 1px solid #eee;"><b>${type} 선택</b></div>`;
    
    // 옵션 목록 컨테이너
    html += '<div style="max-height: 150px; overflow-y: auto;">';
    
    options.forEach(function(opt) {
        // 단일선택 값 처리
        let isSelected = false;
        if (currentValue) {
            try {
                const parsed = JSON.parse(currentValue);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    isSelected = Number(opt.id) === Number(parsed[0]);
                } else {
                    isSelected = Number(opt.id) === Number(parsed);
                }
            } catch (e) {
                isSelected = Number(opt.id) === Number(currentValue);
            }
        }
        const backgroundColor = opt.color ? hexToRgba(opt.color, 0.18) : 'white';
        html += `
          <div class="dropdown-option-container" style="padding: 6px 10px; border-bottom: 1px solid #f0f0f0;">
            <div class="dropdown-item" data-option-id="${opt.id}" 
                 style="cursor: pointer; 
                        background: ${backgroundColor}; 
                        border-radius: 4px; 
                        padding: 6px 8px; 
                        margin-bottom: 4px;
                        ${isSelected ? 'border: 2px solid #007bff; font-weight: bold;' : 'border: 1px solid #ddd;'}
                        transition: all 0.2s;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        position: relative;">
              <div style="display: flex; align-items: center; flex: 1; min-width: 0;">
                <span style="flex: 1; word-wrap: break-word; word-break: break-all; color: #333; font-size: 14px; line-height: 1.4; padding: 2px 0;">${opt.option}</span>
              </div>
              <div class="option-controls" style="display: flex; gap: 4px; align-items: center; margin-left: 8px;">
                <input type="color" value="${opt.color||'#eeeeee'}" data-color-edit="${opt.id}" 
                       style="padding: 0; width: 20px; height: 20px; border: none; cursor: pointer; border-radius: 2px; background: transparent; position: relative;" title="색상 변경">
                <button data-edit="${opt.id}" 
                        style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px; color: #666; transition: color 0.2s;" 
                        title="수정"
                        onmouseover="this.style.color='#007bff'"
                        onmouseout="this.style.color='#666'">✏️</button>
                <button data-del="${opt.id}" 
                        style="background: none; border: none; cursor: pointer; font-size: 12px; padding: 2px; color: #666; transition: color 0.2s;" 
                        title="삭제"
                        onmouseover="this.style.color='#dc3545'"
                        onmouseout="this.style.color='#666'">🗑️</button>
              </div>
            </div>
          </div>
        `;
    });
    
    // "선택 없음" 옵션 추가
    html += `
      <div class="dropdown-option-container" style="padding: 6px 10px; border-bottom: 1px solid #f0f0f0;">
        <div class="dropdown-item" data-option-id="none" 
             style="cursor: pointer; 
                    background: #f8f9fa; 
                    border-radius: 4px; 
                    padding: 6px 8px; 
                    margin-bottom: 4px;
                    border: 1px solid #ddd;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    position: relative;">
          <div style="display: flex; align-items: center; flex: 1; min-width: 0;">
            <span style="flex: 1; word-wrap: break-word; word-break: break-all; color: #999; font-style: italic; font-size: 14px; line-height: 1.4; padding: 2px 0;">선택 없음</span>
          </div>
        </div>
      </div>
    `;
    
    html += '</div>';
    // 새 옵션 추가 영역은 그대로 유지
    html += `<div style="border-top: 1px solid #eee; padding: 8px; background: #f8f9fa;">
      <div style="display: flex; gap: 4px; align-items: center;">
        <input type="text" placeholder="새 옵션 추가" 
               style="flex: 1; padding: 4px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
        <button class="add-btn" 
                style="padding: 4px 12px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px; transition: background-color 0.2s;"
                onmouseover="this.style.background='#0056b3'"
                onmouseout="this.style.background='#007bff'">추가</button>
      </div>
    </div>`;
    
    console.log('드롭다운 HTML 생성 완료, window.dropdown 상태:', window.dropdown);
    
    if (window.dropdown) {
        window.dropdown.innerHTML = html;
        document.body.appendChild(window.dropdown);
        console.log('드롭다운 DOM에 추가 완료');
        
        // === 드롭다운 모달 이벤트 바인딩 추가 ===
        if (typeof bindDropdownModalEvents === 'function') {
            bindDropdownModalEvents(window.dropdown, type, options);
        }
        
        // 단일선택: 옵션 클릭 시 바로 선택
        window.dropdown.querySelectorAll('.dropdown-item[data-option-id]').forEach(function(item) {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                const optionId = this.getAttribute('data-option-id');
                
                // "선택 없음" 옵션 처리
                if (optionId === 'none') {
                    // UI 업데이트
                    td.innerHTML = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">선택 없음</div>`;
                    td.setAttribute('data-value', '');
                    
                    // 커스텀 이벤트 발생
                    const rowId = tr.getAttribute('data-id');
                    document.dispatchEvent(new CustomEvent('dropdownOptionChanged', {
                        detail: {
                            fieldName: type,
                            newValue: '',
                            rowId: rowId
                        }
                    }));
                    
                    // 서버에서 해당 속성 값 삭제
                    if (rowId && rowId.startsWith('temp_')) {
                        // 새 행인 경우 로컬에서만 처리
                        console.log('새 행에서 선택 없음 처리');
                    } else {
                        // 기존 행인 경우 서버에서 삭제
                        fetch('/sales/delete_attribute_value/', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                            body: 'id=' + rowId + '&field=' + encodeURIComponent(type)
                        }).then(function(response) {
                            return response.json();
                        }).then(function(data) {
                            if (!data.success) {
                                alert('삭제 실패: ' + (data.error || ''));
                                return;
                            }
                            
                            // 현재 셀 즉시 업데이트
                            updateTableCell(rowId, type, '');
                            
                            // 종속된 행들 찾아서 업데이트
                            updateDependentRows(rowId, type, '');
                            
                            // 칸반보드 동기화
                            syncTableAndKanban(type);
                        }).catch(function(error) {
                            console.error('삭제 중 오류:', error);
                            alert('삭제 중 오류가 발생했습니다.');
                        });
                    }
                    
                    closeDropdown();
                    return;
                }
                
                // 일반 옵션 선택 처리
                const selectedOption = options.find(opt => opt.id == optionId);
                if (selectedOption) {
                    const color = selectedOption.color ? hexToRgba(selectedOption.color, 0.18) : '#eee';
                    td.innerHTML = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${selectedOption.option}</div>`;
                    td.setAttribute('data-value', selectedOption.id);
                    
                    // 커스텀 이벤트 발생
                    const rowId = tr.getAttribute('data-id');
                    document.dispatchEvent(new CustomEvent('dropdownOptionChanged', {
                        detail: {
                            fieldName: type,
                            newValue: selectedOption.id,
                            rowId: rowId
                        }
                    }));
                    
                    // 새 행인 경우
                    if (rowId && rowId.startsWith('temp_')) {
                        saveNewRowField(tr, type, selectedOption.id);
                    } else {
                        // 기존 행인 경우 - 서버 업데이트는 커스텀 이벤트 핸들러에서 처리
                        console.log('드롭다운 옵션 선택:', type, selectedOption.id);
                        
                        // 서버 업데이트는 handleDropdownOptionChange에서 처리하므로 여기서는 생략
                        // 실제 서버 업데이트는 커스텀 이벤트 핸들러에서 처리됨
                    }
                    
                    closeDropdown();
                }
            });
        });
        
        console.log('드롭다운 이벤트 바인딩 완료');
    } else {
        console.error('window.dropdown이 undefined입니다!');
    }
}

// renderDropdownPills를 위한 드롭다운 옵션 처리 함수
function processDropdownPillsWithOptions(options, parsed, cell, currentValue) {
    let htmlContent = '';
    if (Array.isArray(parsed)) {
        // 다중선택 값 처리
        const selectedOptions = options.filter(opt => parsed.includes(Number(opt.id)));
        
        selectedOptions.forEach(opt => {
            const color = opt.color ? hexToRgba(opt.color, 0.18) : '#eee';
            htmlContent += `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; margin-bottom:2px;">${opt.option}</div>`;
        });
    } else {
        // 단일 선택 값 처리
        const opt = options.find(opt => opt.id == parsed);
        
        if (opt) {
            const color = opt.color ? hexToRgba(opt.color, 0.18) : '#eee';
            htmlContent = `<div class="dropdown-pill" style="background:${color}; color:#333; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center;">${opt.option}</div>`;
        } else {
            // 옵션을 찾지 못한 경우에도 pill 형태로 표시
            console.log(`옵션을 찾지 못함, pill 형태로 표시: ${parsed}`);
            htmlContent = `<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">${parsed}</div>`;
        }
    }
    
    cell.innerHTML = htmlContent || '<div class="dropdown-pill" style="background:#f8f9fa; color:#6c757d; display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; border:1px solid #dee2e6;">선택 없음</div>';
}

// ... existing code ...


// 드롭다운 옵션 변경 이벤트 리스너 설정
function setupDropdownUpdateListeners() {
    // 기존 이벤트 리스너 제거
    document.removeEventListener('dropdownOptionChanged', handleDropdownOptionChange);
    
    // 새로운 이벤트 리스너 추가
    document.addEventListener('dropdownOptionChanged', handleDropdownOptionChange);
    
    console.log('드롭다운 업데이트 리스너 설정 완료');
}

// 드롭다운 옵션 변경 처리 함수
function handleDropdownOptionChange(event) {
    const { fieldName, newValue, rowId } = event.detail;
    
    console.log('드롭다운 옵션 변경 감지:', { fieldName, newValue, rowId });
    
    // 빈 값인 경우 삭제 요청
    // if (newValue === '') {
    //     fetch('/sales/delete_attribute_value/', {
    //         method: 'POST',
    //         headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    //         body: 'id=' + encodeURIComponent(rowId) + '&field=' + encodeURIComponent(fieldName)
    //     })
    //     .then(r => r.json())
    //     .then(function(data) {
    //         if (data.success) {
    //             console.log('드롭다운 옵션 삭제 성공');
                
    //             // 해당 셀을 "선택 없음"으로 업데이트
    //             const row = document.querySelector(`tr[data-id="${rowId}"]`);
    //             if (row) {
    //                 const cell = row.querySelector(`td[data-field="${fieldName}"]`);
    //                 if (cell) {
    //                     cell.innerHTML = '<div style="display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; color:#999;">선택 없음</div>';
    //                     cell.setAttribute('data-value', '');
    //                 }
    //             }
                
    //             // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우에만 즉시 필터 적용
    //             if (window.currentStatusTab !== null && fieldName === window.statusAttributeName) {
    //                 setTimeout(() => {
    //                     if (typeof applyStatusFilter === 'function') {
    //                         applyStatusFilter();
    //                     }
    //                 }, 50);
    //             }
    //         } else {
    //             console.error('드롭다운 옵션 삭제 실패:', data.error);
    //         }
    //     })
    //     .catch(function(error) {
    //         console.error('드롭다운 옵션 삭제 중 오류:', error);
    //     });
    //     return;
    // }
    
    // // 서버에 업데이트 요청
    // console.log('드롭다운 옵션 업데이트 요청123:');
    // fetch('/sales/update_row_field/', {
    //     method: 'POST',
    //     headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    //     body: 'id=' + encodeURIComponent(rowId) + '&field=' + encodeURIComponent(fieldName) + '&value=' + encodeURIComponent(newValue)
    // })
    // .then(r => r.json())
    // .then(function(data) {
    //     if (data.success) {
    //         console.log('드롭다운 옵션 업데이트 성공');
            
    //         // 상태 필터가 활성화되어 있고, 변경된 필드가 상태 속성인 경우에만 즉시 필터 적용
    //         if (window.currentStatusTab !== null && fieldName === window.statusAttributeName) {
    //             // 해당 행의 상태 셀 업데이트
    //             const row = document.querySelector(`tr[data-id="${rowId}"]`);
    //             if (row) {
    //                 const statusCell = row.querySelector(`td[data-field="${fieldName}"]`);
    //                 if (statusCell) {
    //                     // 새로운 값으로 data-value 업데이트
    //                     statusCell.setAttribute('data-value', newValue);
                        
    //                     // 상태 필터 즉시 재적용
    //                     setTimeout(() => {
    //                         if (typeof applyStatusFilter === 'function') {
    //                             applyStatusFilter();
    //                         }
    //                     }, 50);
    //                 }
    //             }
    //         }
            
    //         // 종속된 행들 찾아서 업데이트
    //         if (typeof updateDependentRows === 'function') {
    //             updateDependentRows(rowId, fieldName, newValue);
    //         }
            
    //         // datetime 필드인 경우 캘린더 리렌더링
    //         const fieldElement = document.querySelector(`td[data-field="${fieldName}"]`);
    //         if (fieldElement && fieldElement.getAttribute('data-type') === 'datetime' && window.calendar) {
    //             window.calendar.refetchEvents();
    //         }
            
    //         // 필요시 테이블/보드 갱신
    //         if (typeof refreshCalendarSettings === 'function') {
    //             refreshCalendarSettings();
    //         }
    //     } else {
    //         console.error('드롭다운 옵션 업데이트 실패:', data.error);
    //     }
    // })
    // .catch(function(error) {
    //     console.error('드롭다운 옵션 업데이트 중 오류:', error);
    // });
}

// ... existing code ...

// 디바운싱을 위한 타이머 변수들
let tableUpdateTimer = null;
let kanbanUpdateTimer = null;
let isTableUpdating = false;
let isKanbanUpdating = false;
let pendingKanbanUpdates = new Set(); // 대기 중인 칸반보드 업데이트 추적
let isTableEditing = false; // 테이블 편집 중 상태

// 테이블 편집 상태 관리 함수들
function setTableEditingState(editing) {
    isTableEditing = editing;
    if (editing) {
        console.log('테이블 편집 모드 활성화 - 칸반보드 업데이트 일시 중지');
    } else {
        console.log('테이블 편집 모드 비활성화 - 칸반보드 업데이트 재개');
        // 편집이 끝나면 대기 중인 칸반보드 업데이트 처리
        if (pendingKanbanUpdates.size > 0) {
            const nextUpdate = Array.from(pendingKanbanUpdates)[0];
            pendingKanbanUpdates.delete(nextUpdate);
            setTimeout(() => updateKanbanIfNeeded(nextUpdate), 100);
        }
    }
}

// 전역 이벤트 리스너로 테이블 편집 상태 감지
document.addEventListener('DOMContentLoaded', function() {
    // 테이블 편집 시작 감지
    document.addEventListener('focusin', function(e) {
        if (e.target.classList.contains('table-edit-input') || 
            e.target.classList.contains('dropdown-edit') ||
            e.target.closest('.table-edit-input') ||
            e.target.closest('.dropdown-edit')) {
            setTableEditingState(true);
        }
    });
    
    // 테이블 편집 종료 감지
    document.addEventListener('focusout', function(e) {
        if (e.target.classList.contains('table-edit-input') || 
            e.target.classList.contains('dropdown-edit') ||
            e.target.closest('.table-edit-input') ||
            e.target.closest('.dropdown-edit')) {
            // 약간의 지연을 두어 다른 입력 필드로 포커스가 이동하는 경우를 처리
            setTimeout(() => {
                const activeElement = document.activeElement;
                if (!activeElement || 
                    (!activeElement.classList.contains('table-edit-input') && 
                     !activeElement.classList.contains('dropdown-edit') &&
                     !activeElement.closest('.table-edit-input') &&
                     !activeElement.closest('.dropdown-edit'))) {
                    setTableEditingState(false);
                }
            }, 100);
        }
    });
    
    // ESC 키로 편집 취소 시 상태 해제
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isTableEditing) {
            setTableEditingState(false);
        }
    });
    
    // 드롭다운 옵션 변경 감지 리스너 초기 설정
    setupDropdownUpdateListeners();
});