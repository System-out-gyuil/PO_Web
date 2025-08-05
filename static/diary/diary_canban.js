// 모바일 기기 감지 함수
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
           (window.innerWidth <= 768);
}

function bindKanbanSortable() {
  document.querySelectorAll('.board-cards').forEach(function(col){
      const sortableOptions = {
          group: 'kanban',
          animation: 150,
          onStart: function(evt) {
              // 드래그 시작 시 시각적 피드백
              evt.item.style.opacity = '0.6';
          },
          onEnd: function(evt) {
              // 드래그 종료 시 원래 상태로 복원
              evt.item.style.opacity = '1';
          },
          onAdd: function(evt){
              const entryId = evt.item.getAttribute('data-entry-id');
              const newStatusId = col.parentElement.getAttribute('data-status-id');
              const currentKanbanAttr = col.parentElement.getAttribute('data-attr-name') || window.SELECTED_KANBAN_ATTR;
              
              console.log(`칸반보드 드래그앤드롭: 항목 ${entryId}을 ${currentKanbanAttr} = ${newStatusId}로 변경`);
              
              // 로딩 상태 표시
              evt.item.style.border = '2px solid #007bff';
              evt.item.style.background = '#f8f9fa';
              
              fetch('/sales/update_row_field/', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'X-CSRFToken': getCsrfToken()
                  },
                  body: 'id='+entryId+'&field='+encodeURIComponent(currentKanbanAttr)+'&value='+encodeURIComponent(newStatusId)
              })
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                  }
                  return response.json();
              })
              .then(data => {
                  if (data.success) {
                      console.log('칸반보드 드래그앤드롭 업데이트 성공');
                      
                      // 성공 상태 표시
                      evt.item.style.border = '2px solid #28a745';
                      evt.item.style.background = '#d4edda';
                      
                      // 실시간으로 테이블 새로고침
                      if (typeof refreshTable === 'function') {
                          refreshTable();
                      }
                      
                      // 열린 상세보기 모달이 있다면 해당 행의 드롭다운 값도 업데이트
                      const detailModal = document.getElementById('detailModal');
                      if (detailModal && detailModal.style.display !== 'none' && window.currentDetailRowId == entryId) {
                          console.log('열린 모달의 드롭다운 값을 업데이트합니다');
                          // 모달의 해당 필드 버튼 텍스트 업데이트
                          updateModalDropdownValue(currentKanbanAttr, newStatusId);
                      }
                      
                      // F/U 일정 관련 칸반보드인 경우 캘린더도 새로고침
                      if (currentKanbanAttr === 'F/U 일정' && window.calendar) {
                          window.calendar.refetchEvents();
                      }
                      
                      // datetime 타입 필드인 경우 캘린더 리렌더링
                      const fieldElement = document.querySelector(`td[data-field="${currentKanbanAttr}"]`);
                      if (fieldElement && fieldElement.getAttribute('data-type') === 'datetime' && window.calendar) {
                          window.calendar.refetchEvents();
                      }
                      
                      // 모든 datetime 필드 변경 시 캘린더 리렌더링
                      if (typeof refreshCalendar === 'function') {
                          refreshCalendar();
                      }
                      
                      // 1초 후 원래 스타일로 복원
                      setTimeout(() => {
                          evt.item.style.border = '';
                          evt.item.style.background = '';
                      }, 1000);
                      
                  } else {
                      throw new Error(data.error || '업데이트 실패');
                  }
              })
              .catch(error => {
                  console.error('칸반보드 드래그앤드롭 오류:', error);
                  
                  // 오류 상태 표시
                  evt.item.style.border = '2px solid #dc3545';
                  evt.item.style.background = '#f8d7da';
                  
                  // 오류 알림
                  if (typeof showNotification === 'function') {
                      showNotification('드래그앤드롭 업데이트에 실패했습니다: ' + error.message, 'error');
                  } else {
                      alert('드래그앤드롭 업데이트에 실패했습니다: ' + error.message);
                  }
                  
                  // 2초 후 원래 스타일로 복원
                  setTimeout(() => {
                      evt.item.style.border = '';
                      evt.item.style.background = '';
                  }, 2000);
              });
          }
      };
      
      // 모바일 기기인 경우 1초 지연 설정
      if (isMobileDevice()) {
          sortableOptions.delay = 1000;
          console.log('모바일 기기 감지: 칸반보드 드래그앤드롭에 1초 지연 설정');
      }
      
      new Sortable(col, sortableOptions);
  });
  
  // 칸반 카드 클릭 시 상세 모달
  document.querySelectorAll('.board-card').forEach(function(card){
      card.onclick = function(e) {
          const entryId = card.getAttribute('data-entry-id');
          if(entryId) {
              // 새로운 Row 시스템의 get_row_details 엔드포인트 사용
              fetch('/sales/get_row_details/'+entryId+'/')
                .then(r=>r.json())
                .then(function(data){
                    if(data.success) showDetailModal(data.row_data, data.row_id);
                    else alert('상세정보 불러오기 실패: '+(data.error||''));
                });
          }
      };
  });
  
  // 새 카드 추가 버튼 이벤트
  document.querySelectorAll('.add-card-btn').forEach(function(btn){
      btn.onclick = function() {
          const statusId = btn.closest('.board-col').getAttribute('data-status-id');
          const currentKanbanAttr = btn.closest('.board-col').getAttribute('data-attr-name') || window.SELECTED_KANBAN_ATTR;
          
          // 새 행 생성 - 선택된 칸반 속성 필드를 해당 컬럼의 상태로 설정
          fetch('/sales/create_new_row/', {
              method: 'POST',
              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
              body: 'field='+encodeURIComponent(currentKanbanAttr)+'&value='+encodeURIComponent(statusId)
          }).then(function(response) {
              return response.json();
          }).then(function(data) {
              if (data.success && data.id) {
                  // 칸반보드와 테이블 새로고침
                  refreshKanban();
                  refreshTable();
              } else {
                  alert('새 카드 생성 실패: ' + (data.error || ''));
              }
          }).catch(function(error) {
              console.error('새 카드 생성 중 오류:', error);
              alert('새 카드 생성 중 오류 발생: ' + error.message);
          });
      };
  });
}

// 칸반보드 필터 기능 추가
// 칸반보드 업데이트 상태 관리
let kanbanUpdateInProgress = false;
let lastKanbanData = null;

function updateKanbanBoard(attrName) {
  if (!attrName || attrName === 'undefined') {
      alert('칸반보드 기준 속성을 먼저 설정하세요.');
      return;
  }
  
  // 이미 업데이트 중이면 중복 실행 방지
  if (kanbanUpdateInProgress) {
      console.log('칸반보드 업데이트가 이미 진행 중입니다.');
      return;
  }
  
  kanbanUpdateInProgress = true;
  const loadingIndicator = document.getElementById('kanbanLoadingIndicator');
  const boardView = document.getElementById('boardView');
  
  // 로딩 표시
  if (loadingIndicator) {
      loadingIndicator.style.display = 'block';
  }
  
  fetch('/sales/get_kanban_data/?attr_name=' + encodeURIComponent(attrName))
      .then(response => response.json())
      .then(data => {
          if (loadingIndicator) {
              loadingIndicator.style.display = 'none';
          }
          
          if (data.success) {
              // 데이터가 변경되었는지 확인
              const dataChanged = !lastKanbanData || 
                  JSON.stringify(lastKanbanData) !== JSON.stringify(data);
              
              if (dataChanged) {
                  // 칸반보드 HTML 생성
                  let boardHTML = '<div class="board-container">';
                  
                  data.board.forEach(function(col) {
                      let colStyle = '';
                      if (col.status.color) {
                          colStyle = `background:${hexToRgba(col.status.color, 0.10)};`;
                      }
                      
                      let titleStyle = '';
                      if (col.status.color) {
                          titleStyle = `background:${hexToRgba(col.status.color, 0.18)};border-left:6px solid ${col.status.color};padding-left:10px;`;
                      } else {
                          titleStyle = 'border-left:6px solid #007bff;padding-left:10px;';
                      }
                      
                      boardHTML += `
                          <div class="board-col" data-status-id="${col.status.id}" data-attr-name="${attrName}" style="${colStyle}">
                              <div class="board-col-title" style="${titleStyle}">${col.status.name}</div>
                              <div class="board-cards">
                      `;
                      
                      col.entries.forEach(function(entry) {
                          const entryName = entry.name || '(이름 없음)';
                          const entryAmount = entry.amount;
                          const entryProgress = entry.progress || entry.now || '';
                          
                          // 진행사항 옵션에서 텍스트 찾기
                          let progressText = '';
                          if (entryProgress && data.progress_options) {
                              const progressOption = data.progress_options.find(option => option.id == entryProgress);
                              if (progressOption) {
                                  progressText = progressOption.option;
                              }
                          }
                          
                          boardHTML += `
                              <div class="board-card" data-entry-id="${entry.id}">
                                <div class="board-card-title">${entryName || '(회사명 없음)'}</div>
                                ${progressText ? `<div class="board-card-progress" style="font-size:11px;color:#666;margin-top:2px;">${progressText}</div>` : ''}
                              </div>
                          `;
                      });
                      
                      boardHTML += `
                              </div>
                              <button class="add-card-btn" style="display:none;"></button>
                          </div>
                      `;
                  });
                  
                  boardHTML += '</div>';
                  
                  // 기존 보드 교체
                  boardView.innerHTML = boardHTML;
                  
                  // 이벤트 바인딩 재설정
                  bindKanbanSortable();
                  
                  // 전역 변수 업데이트
                  window.SELECTED_KANBAN_ATTR = attrName;
                  
                  // 마지막 데이터 저장
                  lastKanbanData = data;
                  
                  console.log('칸반보드 업데이트 완료');
              } else {
                  console.log('칸반보드 데이터가 변경되지 않아 업데이트를 건너뜁니다.');
              }
          } else {
              alert('칸반보드 데이터를 불러오는데 실패했습니다: ' + (data.error || ''));
          }
      })
      .catch(error => {
          if (loadingIndicator) {
              loadingIndicator.style.display = 'none';
          }
          console.error('칸반보드 업데이트 오류:', error);
          alert('칸반보드 업데이트 중 오류가 발생했습니다: ' + error.message);
      })
      .finally(() => {
          kanbanUpdateInProgress = false;
      });
}

// 칸반보드 설정 버튼 추가 함수
function addKanbanSettingsButton() {
    const kanbanSection = document.querySelector('#boardView');
    if (!kanbanSection) return;
    
    // 이미 설정 버튼이 있는지 확인
    if (document.getElementById('kanbanSettingsBtn')) return;
    
    // 설정 버튼 생성
    const settingsBtn = document.createElement('button');
    settingsBtn.id = 'kanbanSettingsBtn';
    settingsBtn.innerHTML = '⚙️ 칸반보드 설정';
    settingsBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        padding: 8px 16px;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        z-index: 100;
    `;
    settingsBtn.onclick = function() {
        if (typeof showKanbanSettingsModal === 'function') {
            showKanbanSettingsModal();
        } else {
            console.error('showKanbanSettingsModal 함수를 찾을 수 없습니다.');
        }
    };
    
    // 부모 요소에 상대 위치 설정
    const parentElement = kanbanSection.parentElement;
    if (parentElement) {
        parentElement.style.position = 'relative';
        parentElement.appendChild(settingsBtn);
    }
}

// 칸반보드 새로고침 (현재 선택된 속성으로)
function refreshKanban() {
  let currentAttr = document.getElementById('kanbanAttributeSelect')?.value;
  if (!currentAttr) {
      currentAttr = window.kanbanSettings?.main_attr;
  }
  // 기준 속성이 없으면 아무것도 하지 않음 (모달/alert도 X)
  if (!currentAttr || currentAttr === 'undefined') {
      return;
  }
  updateKanbanBoard(currentAttr);
}

// 모달의 드롭다운 값을 업데이트하는 헬퍼 함수
function updateModalDropdownValue(fieldName, newValue) {
    // 드롭다운 옵션 목록을 가져와서 새 값에 해당하는 텍스트 찾기
    fetch('/sales/dropdown_options/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'field=' + encodeURIComponent(fieldName)
    })
    .then(r => r.json())
    .then(function(data) {
        if (data.success && data.options) {
            const option = data.options.find(opt => opt.id == newValue);
            if (option) {
                // 모달 내의 해당 필드 버튼 찾기
                const modal = document.getElementById('detailModal');
                if (modal) {
                    const buttons = modal.querySelectorAll('button.add-btn');
                    buttons.forEach(button => {
                        const onclickAttr = button.getAttribute('onclick');
                        if (onclickAttr && onclickAttr.includes(`'${fieldName}'`)) {
                            button.textContent = option.name;
                            console.log(`모달 드롭다운 업데이트: ${fieldName} = ${option.name}`);
                        }
                    });
                }
            }
        }
    })
    .catch(error => {
        console.error('드롭다운 옵션 조회 오류:', error);
    });
}

// 한국 통화 형식으로 변환하는 함수 (백만 단위 기준)
function formatKoreanCurrency(value) {
    if (!value) return '0원';
    
    try {
        // 문자열인 경우 숫자만 추출
        let num;
        if (typeof value === 'string') {
            num = parseInt(value.replace(/\D/g, ''));
        } else {
            num = parseInt(value);
        }
        
        if (isNaN(num) || num === 0) {
            return '0원';
        }
        
        let result = '';
        let remaining = num;
        
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
            if (result) {
                result += ' ';
            }
            result += cheon + '천';
            remaining = remaining % 10000000;
        }
        
        // 백만 단위 처리
        if (remaining >= 1000000) {
            const baek = Math.floor(remaining / 1000000);
            if (result) {
                result += ' ';
            }
            result += baek + '백';
            remaining = remaining % 1000000;
        }
        
        // 백만 단위 이상이면 여기서 끝
        if (isOverBaekman) {
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
        
    } catch (error) {
        return String(value);
    }
}

// 칸반보드 컬럼 드래그앤드롭(순서변경) 기능
function enableKanbanColumnDragDrop() {
    const boardContainer = document.querySelector('.board-container');
    if (!boardContainer || typeof Sortable === 'undefined') return;

    // 이미 초기화된 경우 중복 방지
    if (window.kanbanColSortable) {
        window.kanbanColSortable.destroy();
    }

    window.kanbanColSortable = new Sortable(boardContainer, {
        animation: 180,
        handle: '.board-col-title',
        draggable: '.board-col',
        onEnd: function (evt) {
            // 순서 변경 후 서버에 저장
            const attrName = window.SELECTED_KANBAN_ATTR;
            const optionOrders = Array.from(boardContainer.querySelectorAll('.board-col')).map((col, idx) => ({
                id: col.getAttribute('data-status-id'),
                order: idx
            }));

            fetch('/sales/update_kanban_option_order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken ? getCsrfToken() : ''
                },
                body: JSON.stringify({
                    attr_name: attrName,
                    option_orders: optionOrders
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showNotification('칸반보드 옵션 순서가 저장되었습니다.', 'success');
                    // 칸반보드 새로고침
                    updateKanbanBoard(attrName);
                } else {
                    showNotification('순서 저장 실패: ' + (data.error || '알 수 없는 오류'), 'error');
                }
            })
            .catch(err => {
                showNotification('순서 저장 중 오류가 발생했습니다.', 'error');
            });
        }
    });
}

// 칸반보드 렌더 후 호출 및 select change 이벤트 바인딩
// 중복 정의 방지, DOMContentLoaded에서 한 번만 바인딩

document.addEventListener('DOMContentLoaded', function() {
    // select 태그에서 옵션 변경 시 칸반보드 갱신
    const kanbanSelect = document.getElementById('kanbanAttributeSelect');
    if (kanbanSelect) {
        kanbanSelect.addEventListener('change', function() {
            updateKanbanBoard(this.value);
        });
    }
    enableKanbanColumnDragDrop();
    addKanbanSettingsButton(); // 칸반보드 설정 버튼 추가
    initializeKanbanBoard();
});

function initializeKanbanBoard() {
    fetch('/sales/get_kanban_settings/')
        .then(r => r.json())
        .then(data => {
            if (data.success && data.settings && data.settings.main_attr) {
                window.kanbanSettings = data.settings;
                updateKanbanBoard(data.settings.main_attr);
            } else {
                // 설정이 없을 때: ATTR_FIELDS에서 '상태' 속성명을 찾아 디폴트로 사용
                if (window.ATTR_FIELDS) {
                    const statusAttr = window.ATTR_FIELDS.find(attr => attr.name === '상태');
                    if (statusAttr) {
                        updateKanbanBoard('상태');
                    }
                }
            }
            // 설정이 없을 때는 아무것도 하지 않음 (모달 자동 표시 제거)
        });
}

// 칸반보드 필터 기능 추가 및 컬럼 드래그앤드롭 재바인딩
function updateKanbanBoard(attrName) {
    if (!attrName || attrName === 'undefined') {
        // 기준 속성이 없으면 아무것도 하지 않음 (모달/alert도 X)
        return;
    }
    
    // 로그아웃 중이면 요청 중단
    if (window.isLoggingOut) {
        return;
    }
    
    const loadingIndicator = document.getElementById('kanbanLoadingIndicator');
    const boardView = document.getElementById('boardView');
    
    // 로딩 표시
    loadingIndicator.style.display = 'block';
    
    fetch('/sales/get_kanban_data/?attr_name=' + encodeURIComponent(attrName))
        .then(response => {
            // 로그아웃 중이면 요청 중단
            if (window.isLoggingOut) {
                throw new Error('로그아웃 중');
            }
            return response.json();
        })
        .then(data => {
            loadingIndicator.style.display = 'none';
            
            // 로그아웃 중이면 처리 중단
            if (window.isLoggingOut) {
                return;
            }
            
            if (data.success) {
                // 칸반보드 HTML 생성
                let boardHTML = '<div class="board-container">';
                
                data.board.forEach(function(col) {
                    boardHTML += '<div class="board-col" data-status-id="' + col.status.id + '" data-attr-name="' + attrName + '" style="background:' + (col.status.color ? hexToRgba(col.status.color, 0.10) : '') + ';">';
                    boardHTML += '<div class="board-col-title" style="background:' + (col.status.color ? hexToRgba(col.status.color, 0.18) : '') + ';border-left:6px solid ' + (col.status.color || '#007bff') + ';padding-left:10px;">' + col.status.name + '</div>';
                    boardHTML += '<div class="board-cards">';
                    
                    col.entries.forEach(function(entry) {
                        const entryName = entry.name || '(회사명 없음)';
                        const entryProgress = entry.progress || entry.now || '';
                        
                        // 진행사항 옵션에서 텍스트 찾기
                        let progressText = '';
                        if (entryProgress && data.progress_options) {
                            const progressOption = data.progress_options.find(option => option.id == entryProgress);
                            if (progressOption) {
                                progressText = progressOption.option;
                            }
                        }
                        
                        boardHTML += '<div class="board-card" data-entry-id="' + entry.id + '">';
                        boardHTML += '<div class="board-card-title">' + entryName + '</div>';
                        if (progressText) {
                            boardHTML += '<div class="board-card-progress" style="font-size:11px;color:#666;margin-top:2px;">' + progressText + '</div>';
                        }
                        boardHTML += '</div>';
                    });
                    
                    boardHTML += '</div>';
                    boardHTML += '<button class="add-card-btn" style="display:none;"></button>';
                    boardHTML += '</div>';
                });
                
                boardHTML += '</div>';
                boardView.innerHTML = boardHTML;
                
                // 칸반보드 드래그앤드롭 재바인딩
                bindKanbanSortable();
                
                // 전역 변수 업데이트
                window.SELECTED_KANBAN_ATTR = attrName;
                window.currentKanbanAttribute = attrName;
                
            } else {
                // 로그아웃 중이 아닐 때만 오류 메시지 표시
                if (!window.isLoggingOut) {
                    alert('칸반보드 데이터를 불러오는데 실패했습니다: ' + (data.error || ''));
                }
            }
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            console.error('칸반보드 업데이트 오류:', error);
            
            // 로그아웃 중이 아닐 때만 오류 메시지 표시
            if (!window.isLoggingOut && error.message !== '로그아웃 중') {
                alert('칸반보드 업데이트 중 오류가 발생했습니다: ' + error.message);
            }
        });
}