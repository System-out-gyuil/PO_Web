// 탭 초기화 함수
function initializeStatusTabs() {
  
  // 기존 속성 설정 백업
  const existingAttributeSettings = {};
  if (window.allAttributes) {
      window.allAttributes.forEach(attr => {
          if (attr.view_select) {
              existingAttributeSettings[attr.id] = { ...attr.view_select };
          }
      });
  }
  
  fetch('/sales/get_status_tabs/')
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              window.statusAttributeName = data.attribute_name;
              
              // 기존 속성 설정 복원
              if (data.attributes && Object.keys(existingAttributeSettings).length > 0) {
                  data.attributes.forEach(attr => {
                      if (existingAttributeSettings[attr.id]) {
                          attr.view_select = { ...existingAttributeSettings[attr.id] };
                      }
                  });
              }
              
              createStatusTabs(data.options);
          } else {
              console.error('탭 데이터 로드 실패:', data.error);
          }
      })
      .catch(error => {
          console.error('탭 초기화 오류:', error);
      });
}

// 상태 탭 생성 함수
function createStatusTabs(options) {
  const tabContainer = document.getElementById('tabContainer');
  if (!tabContainer) return;
  
  // 상태 옵션 저장
  window.statusOptions = options;
  
  // 전체 탭 추가
  const allTab = document.createElement('button');
  allTab.className = 'status-tab active';
  allTab.textContent = '전체';
  allTab.setAttribute('data-status-id', 'all');
  allTab.onclick = () => selectStatusTab(null);
  tabContainer.appendChild(allTab);
  
  // 각 상태별 탭 추가
  options.forEach(option => {
      const tab = document.createElement('button');
      tab.className = 'status-tab';
      tab.textContent = option.name;
      tab.setAttribute('data-status-id', option.id);
      tab.style.backgroundColor = option.color ? hexToRgba(option.color, 0.18) : '#f8f9fa';
      tab.style.color = '#333';
      tab.onclick = () => selectStatusTab(option.id);
      tabContainer.appendChild(tab);
  });
}

// 탭 선택 함수
function selectStatusTab(statusId) {
  // 기존 활성 탭 비활성화
  document.querySelectorAll('.status-tab').forEach(tab => {
      tab.classList.remove('active');
  });
  
  // 클릭된 탭 활성화
  event.target.classList.add('active');
  
  // 상태 필터 적용
  window.currentStatusTab = statusId;
  
  // 로딩 표시
  showTableLoading();
  
  // 서버에 요청하여 필터링된 데이터 가져오기
  loadFilteredData(statusId);
  
  // URL을 기본 URL로 변경 (쿼리스트링 제거)
  const baseUrl = window.location.origin + '/sales/';
  window.history.pushState({}, '', baseUrl);
}



// 필터링된 데이터 로드
function loadFilteredData(statusId) {
    console.log('loadFilteredData 함수 호출됨');
  const url = new URL('/sales/entry_table_partial/', window.location.origin);
  if (statusId !== null) {
      url.searchParams.set('status_id', statusId);
  }

  fetch(url)
      .then(response => {
          if (!response.ok) throw new Error('Network response was not ok');
          return response.text();
      })
      .then(html => {
          // 그냥 tableView에 바로 innerHTML로 table만 넣는다!
          const currentTable = document.querySelector('#tableView');
          if (currentTable) {
              currentTable.innerHTML = html;

              // 테이블 이벤트 재바인딩
              if (typeof bindTableCellEvents === 'function') {
                  bindTableCellEvents();
              }
              
              // 드래그앤드롭 재초기화 추가
              if (typeof reinitializeDragDrop === 'function') {
                  reinitializeDragDrop();
              }
              
              // 행 드래그앤드롭 재초기화 추가
              if (typeof reinitializeRowDragDrop === 'function') {
                  reinitializeRowDragDrop();
              }

              // 컬럼 리사이저 재초기화
              if (typeof reinitializeColumnResizer === 'function') {
                  reinitializeColumnResizer();
              }
              
              updateFilterStatus();
              initializeTableData();
          }
      })
      .catch(error => {
          console.error('데이터 로드 오류:', error);
          // 오류 시 기본 테이블 표시
          const tableView = document.getElementById('tableView');
          if (tableView) {
              tableView.innerHTML = `
                  <div style="text-align: center; padding: 40px; color: #dc3545;">
                      데이터를 불러오는 중 오류가 발생했습니다.<br>
                      <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                          페이지 새로고침
                      </button>
                  </div>
              `;
          }
      });
}

// 상태 필터 적용 함수
function applyStatusFilter() {
  if (!window.statusAttributeName) return;
  
  const tbody = document.getElementById('entryTbody');
  if (!tbody) return;
  
  const rows = tbody.querySelectorAll('tr[data-id]');
  let statusTab = window.currentStatusTab;
  if (
    statusTab === undefined ||
    statusTab === null ||
    statusTab === 'undefined' ||
    statusTab === 'null' ||
    statusTab === ''
  ) {
    statusTab = 'all';
  }
  
  console.log('상태 필터 적용 시작:', {
      statusAttributeName: window.statusAttributeName,
      currentStatusTab: statusTab,
      totalRows: rows.length,
      timestamp: new Date().toISOString()
  });
  
  let visibleRows = 0;
  let hiddenRows = 0;
  
  rows.forEach((row, index) => {
      const statusCell = row.querySelector(`td[data-field="${window.statusAttributeName}"]`);
      if (!statusCell) {
          console.log(`행 ${index}: 상태 셀을 찾을 수 없음 - 숨김 처리`, row);
          row.style.display = 'none';
          hiddenRows++;
          return;
      }
      
      const statusValue = statusCell.getAttribute('data-value');
      const rowId = row.getAttribute('data-id');
      
      console.log(`행 ${index} (ID: ${rowId}) 상태 값:`, {
          statusValue: statusValue,
          expectedValue: window.currentStatusTab,
          cellText: statusCell.textContent.trim()
      });
      
      if (window.currentStatusTab === null || window.currentStatusTab === 'all') {
          // 전체 탭 선택 시 모든 행 표시
          row.style.display = '';
          visibleRows++;
          console.log(`행 ${index}: 전체 탭 - 표시됨`);
      } else {
          // 특정 상태 탭 선택 시 해당 상태의 행만 표시
          let shouldShow = false;
          
          if (statusValue) {
              try {
                  // JSON 배열 형태인지 확인
                  const parsedValue = JSON.parse(statusValue);
                  if (Array.isArray(parsedValue)) {
                      // 배열인 경우 해당 값이 포함되어 있는지 확인
                      shouldShow = parsedValue.some(val => String(val) === String(window.currentStatusTab));
                      console.log(`행 ${index}: 배열 값 ${JSON.stringify(parsedValue)} - ${shouldShow ? '포함됨' : '포함되지 않음'}`);
                  } else {
                      // 단일 값인 경우 문자열로 변환하여 비교
                      shouldShow = String(parsedValue) === String(window.currentStatusTab);
                      console.log(`행 ${index}: 단일 값 ${parsedValue} === ${window.currentStatusTab} = ${shouldShow}`);
                  }
              } catch (e) {
                  // JSON이 아닌 경우 문자열로 변환하여 비교
                  shouldShow = String(statusValue) === String(window.currentStatusTab);
                  console.log(`행 ${index}: 문자열 비교 ${statusValue} === ${window.currentStatusTab} = ${shouldShow}`);
              }
          } else {
              console.log(`행 ${index}: statusValue가 없음 - 숨김 처리`);
          }
          
          row.style.display = shouldShow ? '' : 'none';
          if (shouldShow) {
              visibleRows++;
              console.log(`행 ${index}: 표시됨`);
          } else {
              hiddenRows++;
              console.log(`행 ${index}: 숨김 처리됨`);
          }
      }
  });
  
  console.log('상태 필터 적용 완료:', {
      totalRows: rows.length,
      visibleRows: visibleRows,
      hiddenRows: hiddenRows,
      timestamp: new Date().toISOString()
  });
  
  // 필터 상태 업데이트
  updateFilterStatus();
}

// 모달용 상태 탭 로드
function loadStatusTabsForModal() {
  console.log('모달용 상태 탭 로드 시작 - 캐시 초기화');
  
  // 기존 캐시된 데이터 초기화
  window.statusOptions = null;
  window.allAttributes = null;
  window.currentModalStatusId = 'all';
  
  fetch('/sales/get_status_tabs/')
      .then(response => response.json())
      .then(data => {
          console.log('상태 탭 데이터 응답:', data);
          if (data.success) {
              window.statusOptions = data.options;
              createStatusTabsForModal(data.options);
              loadAttributesForModal();
          } else {
              console.error('상태 탭 데이터 로드 실패:', data.error);
          }
      })
      .catch(error => {
          console.error('상태 탭 로드 오류:', error);
      });
}

// 모달용 상태 탭 생성
function createStatusTabsForModal(options) {
  console.log('모달용 상태 탭 생성:', options);
  const container = document.getElementById('statusTabsContainer');
  if (!container) {
      console.error('statusTabsContainer를 찾을 수 없습니다.');
      return;
  }
  
  container.innerHTML = '';
  
  // 전체 탭 추가
  const allTab = document.createElement('button');
  allTab.className = 'modal-status-tab active';
  allTab.textContent = '전체';
  allTab.onclick = () => selectModalStatusTab('all');
  container.appendChild(allTab);
  
  // 각 상태별 탭 추가
  options.forEach(option => {
      const tab = document.createElement('button');
      tab.className = 'modal-status-tab';
      tab.textContent = option.name;
      tab.style.backgroundColor = option.color ? hexToRgba(option.color, 0.18) : '#f8f9fa';
      tab.style.color = '#333';
      tab.onclick = () => selectModalStatusTab(option.id);
      container.appendChild(tab);
  });
}

// 모달에서 상태 탭 선택
function selectModalStatusTab(statusId) {
  console.log('모달에서 상태 탭 선택:', statusId);
  // 기존 활성 탭 비활성화
  document.querySelectorAll('.modal-status-tab').forEach(tab => {
      tab.classList.remove('active');
  });
  
  // 클릭된 탭 활성화
  event.target.classList.add('active');
  
  // 현재 상태 ID 업데이트
  window.currentModalStatusId = statusId;
  
  console.log('현재 모달 상태 ID 업데이트:', window.currentModalStatusId);
  
  // 속성 데이터 서버에서 새로 받아와서 최신 상태 반영
  console.log('탭 전환으로 인한 속성 데이터 새로고침');
  loadAttributesForModal();
}

// 모달용 속성 데이터 로드
function loadAttributesForModal() {
  console.log('모달용 속성 데이터 로드 시작 - 최신 데이터 받아오기');
  
  fetch('/sales/get_all_attributes/')
      .then(response => response.json())
      .then(data => {
          console.log('속성 데이터 응답:', data);
          if (data.success) {
              window.allAttributes = data.attributes;
              updateAttributesListForModal();
          } else {
              console.error('속성 데이터 로드 실패:', data.error);
          }
      })
      .catch(error => {
          console.error('속성 로드 오류:', error);
      });
}

// 모달용 속성 목록 업데이트
function updateAttributesListForModal() {
  console.log('모달용 속성 목록 업데이트 시작');
  const container = document.getElementById('attributesListContainer');
  if (!container) {
      console.error('attributesListContainer를 찾을 수 없습니다.');
      return;
  }
  
  console.log('현재 속성들:', window.allAttributes);
  console.log('현재 상태 ID:', window.currentModalStatusId);
  
  container.innerHTML = '';
  
  if (!window.allAttributes || window.allAttributes.length === 0) {
      container.innerHTML = '<div style="text-align:center;color:#6c757d;padding:20px;">속성을 불러오는 중...</div>';
      return;
  }
  
  window.allAttributes.forEach(attr => {
      const attrDiv = document.createElement('div');
      attrDiv.style.cssText = 'display:flex;align-items:center;padding:10px;border-bottom:1px solid #eee;';
      
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.id = `attr_${attr.id}_${window.currentModalStatusId}`; // 상태별로 고유한 ID
      checkbox.className = 'attribute-visibility-checkbox';
      
      // 현재 상태에서의 표시 여부 설정 (서버에서 받은 최신 데이터 기준)
      let isChecked = false;
      if (window.currentModalStatusId === 'all') {
          // 전체 탭은 "0" 키로 관리되는 독립적인 상태
          isChecked = attr.view_select && attr.view_select['0'] === true;
      } else {
          // 특정 상태 탭에서는 해당 상태만 확인
          isChecked = attr.view_select && attr.view_select[window.currentModalStatusId] === true;
      }
      checkbox.checked = isChecked;
      
      // 체크박스 변경 이벤트 추가
      checkbox.addEventListener('change', function() {
          console.log(`속성 ${attr.name} (${attr.id}) 체크 상태 변경: ${this.checked} (상태 ID: ${window.currentModalStatusId})`);
          saveSingleAttributeSetting(attr.id, window.currentModalStatusId, this.checked);
      });
      
      console.log(`속성 ${attr.name} (ID: ${attr.id}): view_select=${JSON.stringify(attr.view_select)}, 현재 상태=${window.currentModalStatusId}, checked=${isChecked}`);
      
      const label = document.createElement('label');
      label.htmlFor = `attr_${attr.id}_${window.currentModalStatusId}`;
      label.textContent = attr.name;
      label.style.flex = '1';
      
      attrDiv.appendChild(checkbox);
      attrDiv.appendChild(label);
      container.appendChild(attrDiv);
  });
  
  console.log('모달용 속성 목록 업데이트 완료');
}

// 단일 속성 설정 저장
function saveSingleAttributeSetting(attrId, statusId, isVisible) {
  console.log(`단일 속성 설정 저장: 속성 ID=${attrId}, 상태 ID=${statusId}, 표시=${isVisible}`);
  
  // 해당 속성 찾기
  const attr = window.allAttributes.find(a => a.id === attrId);
  if (!attr) {
      console.error('속성을 찾을 수 없습니다:', attrId);
      return;
  }
  
  const settings = {};
  settings[attrId] = { ...attr.view_select };
  
  if (statusId === 'all') {
      settings[attrId]['0'] = isVisible;
  } else {
      settings[attrId][statusId] = isVisible;
  }
  
  console.log('저장할 설정:', settings);
  
  // 서버에 저장
  fetch('/sales/update_attribute_visibility/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify({ settings: settings })
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          console.log(`속성 설정 저장 성공: ${attr.name} (${statusId})`);
          
          // 속성 데이터 업데이트
          if (attr.view_select) {
              if (statusId === 'all') {
                  attr.view_select['0'] = isVisible;
              } else {
                  attr.view_select[statusId] = isVisible;
              }
          } else {
              attr.view_select = {};
              if (statusId === 'all') {
                  attr.view_select['0'] = isVisible;
              } else {
                  attr.view_select[statusId] = isVisible;
              }
          }
          
          // 테이블 즉시 새로고침
          refreshTableWithStatusFilter();
          
      } else {
          console.error('설정 저장 실패:', data.error);
          alert('설정 저장 실패: ' + data.error);
          
          // 실패 시 체크박스 상태 되돌리기
          const checkbox = document.getElementById(`attr_${attrId}_${statusId}`);
          if (checkbox) {
              checkbox.checked = !isVisible;
          }
      }
  })
  .catch(error => {
      console.error('Error:', error);
      alert('설정 저장 중 오류가 발생했습니다.');
      
      // 실패 시 체크박스 상태 되돌리기
      const checkbox = document.getElementById(`attr_${attrId}_${statusId}`);
      if (checkbox) {
          checkbox.checked = !isVisible;
      }
  });
}

// 상태 필터를 고려한 테이블 새로고침
function refreshTableWithStatusFilter() {
  console.log('refreshTableWithStatusFilter 함수 호출됨');
  // 현재 속성 설정 백업
  const currentAttributeSettings = {};
  if (window.allAttributes) {
      window.allAttributes.forEach(attr => {
          if (attr.view_select) {
              currentAttributeSettings[attr.id] = { ...attr.view_select };
          }
      });
  }
  
  // 현재 상태 ID를 URL 파라미터로 전달
  const url = new URL('/sales/entry_table_partial/', window.location.origin);
  let statusTab = window.currentStatusTab;
  if (
    statusTab === undefined ||
    statusTab === null ||
    statusTab === 'undefined' ||
    statusTab === 'null' ||
    statusTab === ''
  ) {
    statusTab = 'all';
  }
  if (statusTab !== null) {
      url.searchParams.set('status_id', statusTab);
  }
  
  fetch(url)
      .then(response => response.text())
      .then(html => {
          document.getElementById('tableView').innerHTML = html;
          
          // 속성 설정 복원
          if (window.allAttributes && Object.keys(currentAttributeSettings).length > 0) {
              window.allAttributes.forEach(attr => {
                  if (currentAttributeSettings[attr.id]) {
                      attr.view_select = { ...currentAttributeSettings[attr.id] };
                  }
              });
          }
          
          // 필요시 테이블 관련 이벤트 재바인딩
          if (typeof bindTableCellEvents === 'function') bindTableCellEvents();
          
          // 드래그앤드롭 재초기화 추가
          if (typeof reinitializeDragDrop === 'function') {
              reinitializeDragDrop();
          }
          
          // 행 드래그앤드롭 재초기화 추가
          if (typeof reinitializeRowDragDrop === 'function') {
              reinitializeRowDragDrop();
          }
          
          // 상태 필터가 활성화되어 있으면 즉시 적용
          if (statusTab !== null) {
              setTimeout(() => {
                  applyStatusFilter();
              }, 100);
          }
          
          // 필터 상태 업데이트
          updateFilterStatus();
      })
      .catch(error => {
          console.error('테이블 새로고침 오류:', error);
      });
}

// 탭 전환 함수
function switchTab(tabName) {
  // 모든 탭 콘텐츠 숨기기
  document.getElementById('visibilityTabContent').style.display = 'none';
  document.getElementById('cascadeTabContent').style.display = 'none';
  
  // 모든 탭 버튼 비활성화
  document.getElementById('visibilityTab').style.background = '#6c757d';
  document.getElementById('cascadeTab').style.background = '#6c757d';
  
  // 선택된 탭 콘텐츠 표시
  document.getElementById(tabName + 'TabContent').style.display = 'block';
  document.getElementById(tabName + 'Tab').style.background = '#007bff';
  
  // 상태별 표시 관리 탭이 선택된 경우 초기화
  if (tabName === 'visibility') {
      loadStatusTabsForModal();
  }
}

// 상태 탭 새로고침 함수
function refreshStatusTabs() {
  console.log('상태 탭 새로고침 시작');
  
  // 현재 활성 탭 상태 저장
  const activeTab = document.querySelector('.status-tab.active');
  const currentStatusId = activeTab ? activeTab.getAttribute('data-status-id') : null;
  
  // 현재 속성 설정 상태 백업
  const currentAttributeSettings = {};
  if (window.allAttributes) {
      window.allAttributes.forEach(attr => {
          if (attr.view_select) {
              currentAttributeSettings[attr.id] = { ...attr.view_select };
          }
      });
  }
  
  // 탭 컨테이너 초기화
  const tabContainer = document.getElementById('tabContainer');
  if (tabContainer) {
      tabContainer.innerHTML = '';
  }
  
  // 상태 탭 재초기화 - 서버 재요청 없이 기존 데이터 사용
  if (window.statusAttributeName) {
      // 기존 상태 옵션 데이터가 있다면 사용, 없다면 서버에서 가져오기
      if (window.statusOptions) {
          createStatusTabs(window.statusOptions);
        } else {
            // 서버에서 상태 옵션만 가져오기 (속성 설정은 유지)
            fetch('/sales/get_status_tabs/')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.statusOptions = data.options;
                        createStatusTabs(data.options);
                        
                        // 속성 설정 복원
                        if (window.allAttributes && Object.keys(currentAttributeSettings).length > 0) {
                            window.allAttributes.forEach(attr => {
                                if (currentAttributeSettings[attr.id]) {
                                    attr.view_select = { ...currentAttributeSettings[attr.id] };
                                }
                            });
                        }
                        
                        // 이전 활성 탭 복원
                        if (currentStatusId !== null) {    
                            setTimeout(() => {
                                const newActiveTab = document.querySelector(`.status-tab[data-status-id=${currentStatusId}]`);
                                if (newActiveTab) {
                                    // 기존 활성 탭 비활성화
                                    document.querySelectorAll('.status-tab').forEach(tab => {
                                        tab.classList.remove('active');
                                    });
                                    // 새 활성 탭 활성화
                                    newActiveTab.classList.add('active');
                                    window.currentStatusTab = currentStatusId;
                                }
                            }, 200);
                        }
                    }
                })
                .catch(error => {
                    console.error('상태 탭 새로고침 중 오류:', error);
                });
        }
  }
  
  // 속성 설정 복원
  if (window.allAttributes && Object.keys(currentAttributeSettings).length > 0) {
      window.allAttributes.forEach(attr => {
          if (currentAttributeSettings[attr.id]) {
              attr.view_select = { ...currentAttributeSettings[attr.id] };
          }
      });
  }
  
  // 이전 활성 탭 복원 (기존 데이터 사용 시)
  if (currentStatusId !== null && window.statusOptions) {    
      setTimeout(() => {
          const newActiveTab = document.querySelector(`.status-tab[data-status-id=${currentStatusId}]`);
          if (newActiveTab) {
              // 기존 활성 탭 비활성화
              document.querySelectorAll('.status-tab').forEach(tab => {
                  tab.classList.remove('active');
              });
              // 새 활성 탭 활성화
              newActiveTab.classList.add('active');
              window.currentStatusTab = currentStatusId;
          }
      }, 200);
  }
}

// 상태 속성 변경 감지 및 탭 리랜더링 함수
function handleStatusAttributeChange(fieldName) {
  console.log('상태 속성 변경 감지:', fieldName, '현재 상태 속성:', window.statusAttributeName);
  
  // 변경된 필드가 현재 상태 속성과 일치하는지 확인
  if (fieldName === window.statusAttributeName) {
      console.log('상태 속성이 변경되었으므로 상태 탭을 새로고침합니다.');
      console.log('현재 활성 탭 상태:', window.currentStatusTab);
      
      // 기존 상태 옵션 캐시 삭제
      window.statusOptions = null;
      
      // 상태 탭 강제 새로고침 (서버에서 최신 데이터 가져오기)
      refreshStatusTabsFromServer();
  } else {
      console.log('변경된 필드가 상태 속성이 아니므로 상태 탭을 새로고침하지 않습니다.');
  }
}

// 서버에서 최신 상태 데이터를 가져와서 탭 새로고침
function refreshStatusTabsFromServer() {
  console.log('서버에서 상태 탭 데이터 새로고침 시작');
  
  // 현재 활성 탭 상태 저장
  const activeTab = document.querySelector('.status-tab.active');
  const currentStatusId = activeTab ? activeTab.getAttribute('data-status-id') : null;
  
  // 현재 속성 설정 상태 백업
  const currentAttributeSettings = {};
  if (window.allAttributes) {
      window.allAttributes.forEach(attr => {
          if (attr.view_select) {
              currentAttributeSettings[attr.id] = { ...attr.view_select };
          }
      });
  }
  
  // 서버에서 최신 상태 탭 데이터 가져오기
  fetch('/sales/get_status_tabs/')
      .then(response => response.json())
      .then(data => {
          console.log('서버에서 받은 최신 상태 탭 데이터:', data);
          
          if (data.success) {
              // 상태 옵션 업데이트
              window.statusOptions = data.options;
              window.statusAttributeName = data.attribute_name;
              
              // 탭 컨테이너 초기화
              const tabContainer = document.getElementById('tabContainer');
              if (tabContainer) {
                  tabContainer.innerHTML = '';
              }
              
              // 새로운 상태 탭 생성
              createStatusTabs(data.options);
              
              // 속성 설정 복원
              if (window.allAttributes && Object.keys(currentAttributeSettings).length > 0) {
                  window.allAttributes.forEach(attr => {
                      if (currentAttributeSettings[attr.id]) {
                          attr.view_select = { ...currentAttributeSettings[attr.id] };
                      }
                  });
              }
              
              // 이전 활성 탭 복원 시도
              if (currentStatusId !== null) {
                  setTimeout(() => {
                      const newActiveTab = document.querySelector(`.status-tab[data-status-id="${currentStatusId}"]`);
                      if (newActiveTab) {
                          // 기존 활성 탭 비활성화
                          document.querySelectorAll('.status-tab').forEach(tab => {
                              tab.classList.remove('active');
                          });
                          // 새 활성 탭 활성화
                          newActiveTab.classList.add('active');
                          window.currentStatusTab = currentStatusId;
                          
                          console.log('이전 활성 탭 복원 완료:', currentStatusId);
                          
                          // 테이블 데이터 새로고침 (현재 상태로)
                          loadFilteredData(currentStatusId);
                      } else {
                          // 이전 탭이 삭제된 경우 전체 탭으로 돌아가기
                          console.log('이전 활성 탭을 찾을 수 없어 전체 탭으로 전환');
                          const allTab = document.querySelector('.status-tab[data-status-id="all"]');
                          if (allTab) {
                              document.querySelectorAll('.status-tab').forEach(tab => {
                                  tab.classList.remove('active');
                              });
                              allTab.classList.add('active');
                              window.currentStatusTab = null;
                              
                              // 전체 데이터로 테이블 새로고침
                              loadFilteredData(null);
                          }
                      }
                  }, 200);
              } else {
                  // 전체 탭이 활성화된 상태였다면 유지
                  setTimeout(() => {
                      const allTab = document.querySelector('.status-tab[data-status-id="all"]');
                      if (allTab && !allTab.classList.contains('active')) {
                          document.querySelectorAll('.status-tab').forEach(tab => {
                              tab.classList.remove('active');
                          });
                          allTab.classList.add('active');
                      }
                      
                      // 전체 데이터로 테이블 새로고침
                      loadFilteredData(null);
                  }, 200);
              }
              
              console.log('상태 탭 새로고침 완료');
          } else {
              console.error('상태 탭 데이터 로드 실패:', data.error);
          }
      })
      .catch(error => {
          console.error('상태 탭 새로고침 중 오류:', error);
      });
}

// 전역 상태 속성 변경 이벤트 리스너 설정
function setupStatusAttributeChangeListener() {
  // 커스텀 이벤트 리스너 등록
  document.addEventListener('statusAttributeChanged', function(event) {
      const { fieldName, action } = event.detail;
      console.log('상태 속성 변경 이벤트 수신:', { fieldName, action });
      
      // 상태 속성 변경 처리
      handleStatusAttributeChange(fieldName);
  });
  
  console.log('상태 속성 변경 이벤트 리스너 설정 완료');
}

// 드롭다운 옵션 변경 후 상태 필터 안전 재적용 함수
function safeApplyStatusFilterAfterChange() {
  console.log('드롭다운 옵션 변경 후 상태 필터 안전 재적용 시작');
  
  // 현재 상태 탭이 활성화되어 있는지 확인
  if (window.currentStatusTab === null || window.currentStatusTab === 'all') {
    console.log('전체 탭이 활성화되어 있어 필터 적용 불필요');
    return;
  }
  
  // 상태 속성이 설정되어 있는지 확인
  if (!window.statusAttributeName) {
    console.log('상태 속성이 설정되지 않음');
    return;
  }
  
  // 테이블이 로드되어 있는지 확인
  const tbody = document.getElementById('entryTbody');
  if (!tbody) {
    console.log('테이블 본문을 찾을 수 없음');
    return;
  }
  
  // 약간의 지연 후 필터 적용 (DOM 업데이트 완료 대기)
  setTimeout(() => {
    console.log('지연 후 상태 필터 적용 실행');
    if (typeof applyStatusFilter === 'function') {
      applyStatusFilter();
    } else {
      console.error('applyStatusFilter 함수를 찾을 수 없음');
    }
  }, 100);
}

// 상태 셀의 data-value 속성 강제 업데이트 함수
function forceUpdateStatusCellValue(rowId, fieldName, newValue) {
  console.log(`상태 셀 강제 업데이트: 행 ID=${rowId}, 필드=${fieldName}, 값=${newValue}`);
  
  const row = document.querySelector(`tr[data-id="${rowId}"]`);
  if (!row) {
    console.error(`행을 찾을 수 없음: ${rowId}`);
    return false;
  }
  
  const statusCell = row.querySelector(`td[data-field="${fieldName}"]`);
  if (!statusCell) {
    console.error(`상태 셀을 찾을 수 없음: ${fieldName}`);
    return false;
  }
  
  // data-value 속성 업데이트
  statusCell.setAttribute('data-value', newValue);
  
  // 셀 내용도 업데이트 (옵션명 표시)
  if (window.statusOptions) {
    const option = window.statusOptions.find(opt => String(opt.id) === String(newValue));
    if (option) {
      statusCell.innerHTML = `<div style="display:inline-block; padding:4px 14px; border-radius:16px; font-size:13px; font-weight:500; min-width:48px; text-align:center; background-color:${option.color ? hexToRgba(option.color, 0.18) : '#f8f9fa'}; color:#333;">${option.name}</div>`;
    }
  }
  
  console.log(`상태 셀 업데이트 완료: ${fieldName} = ${newValue}`);
  return true;
}

// 16진수 색상을 RGBA로 변환하는 헬퍼 함수
function hexToRgba(hex, alpha = 1) {
    // # 제거
    hex = hex.replace('#', '');
    
    // 3자리인 경우 6자리로 확장
    if (hex.length === 3) {
        hex = hex.split('').map(char => char + char).join('');
    }
    
    // RGB 값 추출
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// 새로운 상태 옵션 추가 후 테이블 데이터 즉시 업데이트 함수
function refreshTableAfterNewStatusOption() {
  console.log('새로운 상태 옵션 추가 후 테이블 데이터 즉시 업데이트 시작');
  
  // 현재 활성 탭 상태 확인
  const activeTab = document.querySelector('.status-tab.active');
  if (!activeTab) {
    console.log('활성 탭을 찾을 수 없음');
    return;
  }
  
  const currentStatusId = activeTab.getAttribute('data-status-id');
  console.log('현재 활성 탭 ID:', currentStatusId);
  
  // 전체 탭이 아닌 경우에만 테이블 데이터 새로고침
  if (currentStatusId !== 'all') {
    console.log('특정 상태 탭이 활성화되어 있음, 테이블 데이터 새로고침 실행');
    
    // 서버에서 최신 테이블 데이터 가져오기
    const url = new URL('/sales/entry_table_partial/', window.location.origin);
    url.searchParams.set('status_id', currentStatusId);
    
    fetch(url)
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.text();
      })
      .then(html => {
        console.log('테이블 데이터 새로고침 완료');
        
        // 테이블 내용 업데이트
        const currentTable = document.querySelector('#tableView');
        if (currentTable) {
          currentTable.innerHTML = html;
          
          // 테이블 이벤트 재바인딩
          if (typeof bindTableCellEvents === 'function') {
            bindTableCellEvents();
          }
          
          // 드래그앤드롭 재초기화
          if (typeof reinitializeDragDrop === 'function') {
            reinitializeDragDrop();
          }
          
          // 행 드래그앤드롭 재초기화
          if (typeof reinitializeRowDragDrop === 'function') {
            reinitializeRowDragDrop();
          }
          
          // 컬럼 리사이저 재초기화
          if (typeof reinitializeColumnResizer === 'function') {
            reinitializeColumnResizer();
          }
          
          // 상태 필터 즉시 적용
          setTimeout(() => {
            if (typeof applyStatusFilter === 'function') {
              console.log('새로운 상태 옵션 추가 후 상태 필터 재적용');
              applyStatusFilter();
            }
          }, 100);
          
          // 필터 상태 업데이트
          if (typeof updateFilterStatus === 'function') {
            updateFilterStatus();
          }
          
          // 테이블 데이터 초기화
          if (typeof initializeTableData === 'function') {
            initializeTableData();
          }
        }
      })
      .catch(error => {
        console.error('테이블 데이터 새로고침 오류:', error);
      });
  } else {
    console.log('전체 탭이 활성화되어 있어 테이블 데이터 새로고침 불필요');
  }
}

// 상태 탭 클릭 시 즉시 테이블 데이터 업데이트 함수
function selectStatusTabWithImmediateUpdate(statusId) {
  console.log('상태 탭 선택 및 즉시 테이블 업데이트:', statusId);
  
  // 기존 활성 탭 비활성화
  document.querySelectorAll('.status-tab').forEach(tab => {
    tab.classList.remove('active');
  });
  
  // 클릭된 탭 활성화
  event.target.classList.add('active');
  
  // 상태 필터 적용
  window.currentStatusTab = statusId;
  
  // 로딩 표시
  if (typeof showTableLoading === 'function') {
    showTableLoading();
  }
  
  // 서버에 요청하여 필터링된 데이터 가져오기
  loadFilteredData(statusId);
  
  // URL을 기본 URL로 변경 (쿼리스트링 제거)
  const baseUrl = window.location.origin + '/sales/';
  window.history.pushState({}, '', baseUrl);
}