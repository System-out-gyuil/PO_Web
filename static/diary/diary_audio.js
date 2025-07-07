// updateAudioFileOrder 함수 복구
function updateAudioFileOrder(rowId, fileId, newOrder) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch('/600/update_audio_file_order/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
          row_id: rowId,
          file_id: fileId,
          new_order: newOrder
      })
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          console.log('오디오 파일 순서 업데이트 성공');
      } else {
          console.error('오디오 파일 순서 업데이트 실패:', data.error);
      }
  })
  .catch(error => {
      console.error('오디오 파일 순서 업데이트 오류:', error);
  });
}

function updateAudioFileManagement(audioFileValue) {
  console.log('updateAudioFileManagement 호출됨:', audioFileValue);
  console.log('audioFileValue 타입:', typeof audioFileValue);
  
  const audioFilesList = document.getElementById('audioFilesList');
  const noAudioFilesMessage = document.getElementById('noAudioFilesMessage');
  const selectedAudioTextArea = document.getElementById('selectedAudioTextArea');
  
  if (!audioFilesList) {
      console.error('audioFilesList 요소를 찾을 수 없습니다.');
      return;
  }
  
  // 기존 선택 상태 초기화
  if (selectedAudioTextArea) {
      selectedAudioTextArea.style.display = 'none';
  }
  window.selectedAudioFile = null;
  
  // 음성파일 값이 JSON인지 확인
  let audioFileData = null;
  try {
      if (audioFileValue && typeof audioFileValue === 'string' && audioFileValue.startsWith('{')) {
          audioFileData = JSON.parse(audioFileValue);
      } else if (audioFileValue && typeof audioFileValue === 'object') {
          audioFileData = audioFileValue;
      }
  } catch (e) {
      console.log('JSON 파싱 실패:', e);
      audioFileData = null;
  }
  
  console.log('최종 audioFileData:', audioFileData);
  
  // 기존 내용 초기화
  audioFilesList.innerHTML = '';
  
  // 2. 음성파일과 텍스트 노트 렌더링
  if (audioFileData && Object.keys(audioFileData).length > 0) {
      // 모든 아이템을 하나의 배열로 수집
      let allItems = [];
      
      // 날짜별로 오디오 파일과 텍스트 노트 수집
      Object.keys(audioFileData).forEach(date => {
          if(date === 'texts') return; // 기존 texts 배열은 무시
          const dateItems = audioFileData[date] || {};
          Object.keys(dateItems).forEach(itemId => {
              const itemInfo = dateItems[itemId];
              
              // 기존 아이템에 type 필드가 없으면 추가
              if (!itemInfo.type) {
                  // 파일 정보가 있으면 오디오, 없으면 텍스트로 판단
                  if (itemInfo.original_filename || itemInfo.file_size) {
                      itemInfo.type = 'audio';
                  } else {
                      itemInfo.type = 'text';
                  }
              }
              
              if (itemInfo.type === 'audio') {
                  allItems.push({
                      type: 'audio',
                      date: date,
                      fileId: itemId,
                      fileInfo: itemInfo,
                      uploadTime: new Date(itemInfo.upload_time || '2024-01-01'),
                      order: itemInfo.order !== undefined ? itemInfo.order : 9999
                  });
              } else if (itemInfo.type === 'text') {
                  allItems.push({
                      type: 'text',
                      noteId: itemId,
                      text: itemInfo.text || '',
                      order: itemInfo.order !== undefined ? itemInfo.order : 9999
                  });
              }
          });
      });
      
      // order 필드로 정렬
      allItems.sort((a, b) => {
          if (a.order !== 9999 && b.order !== 9999) {
              return a.order - b.order;
          }
          if (a.order !== 9999 && b.order === 9999) {
              return -1;
          }
          if (a.order === 9999 && b.order !== 9999) {
              return 1;
          }
          // 둘 다 order가 없으면 타입별로 정렬 (텍스트가 위로)
          if (a.type === 'text' && b.type === 'audio') {
              return -1;
          }
          if (a.type === 'audio' && b.type === 'text') {
              return 1;
          }
          // 같은 타입이면 업로드 시간으로 정렬 (최신이 위)
          if (a.type === 'audio' && b.type === 'audio') {
              return b.uploadTime - a.uploadTime;
          }
          return 0;
      });
      
      if (allItems.length > 0) {
          if (noAudioFilesMessage) {
              noAudioFilesMessage.style.display = 'none';
          }
          
          // 드래그 앤 드롭 컨테이너 생성
          const sortableContainer = document.createElement('div');
          sortableContainer.id = 'sortableAudioContainer';
          sortableContainer.style.cssText = 'display: flex; flex-direction: column; gap: 0; position: relative;';
          
          // 맨 앞에 placeholder
          sortableContainer.appendChild(createAddPlaceholder(0));
          
          allItems.forEach((item, index) => {
              if (item.type === 'audio') {
                  console.log('audio 아이템:', item);
                  const fileElement = createAudioFileElement(item, index);
                  sortableContainer.appendChild(fileElement);
              } else if (item.type === 'text') {
                  const textElement = createTextNoteElement(item, index);
                  sortableContainer.appendChild(textElement);
              }
              // 각 셀 뒤에 placeholder
              sortableContainer.appendChild(createAddPlaceholder(index + 1));
          });
          
          audioFilesList.appendChild(sortableContainer);
          
          // Sortable.js 적용 (드래그 앤 드롭)
          if (typeof Sortable !== 'undefined') {
              new Sortable(sortableContainer, {
                  animation: 150,
                  ghostClass: 'sortable-ghost',
                  chosenClass: 'sortable-chosen',
                  dragClass: 'sortable-drag',
                  onEnd: function (evt) {
                      console.log('아이템 순서 변경:', evt.oldIndex, '->', evt.newIndex);
                      saveAllOrderToServer(sortableContainer);
                  }
              });
          }
      } else {
          // 오디오 파일과 텍스트 노트가 모두 없는 경우
          showNoContentMessage(audioFilesList, noAudioFilesMessage);
      }
  } else {
      // 데이터가 없는 경우
      showNoContentMessage(audioFilesList, noAudioFilesMessage);
  }
  
  // 음성파일 데이터를 전역 변수에 저장
  window.audioFileData = audioFileData;
}

// 내용이 없을 때 메시지 표시 함수
function showNoContentMessage(audioFilesList, noAudioFilesMessage) {
  if (noAudioFilesMessage) {
      noAudioFilesMessage.style.display = 'block';
      noAudioFilesMessage.innerHTML = `
          <div style="text-align: center; padding: 40px 20px; color: #666;">
              <div style="font-size: 48px; margin-bottom: 15px;">📝</div>
              <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">음성파일과 텍스트 노트가 없습니다</div>
              <div style="font-size: 14px; color: #888;">
                  음성파일을 업로드하거나 텍스트 노트를 추가해보세요
              </div>
          </div>
      `;
      audioFilesList.appendChild(noAudioFilesMessage);
  } else {
      // noAudioFilesMessage가 없는 경우 새로 생성
      const messageDiv = document.createElement('div');
      messageDiv.id = 'noAudioFilesMessage';
      messageDiv.style.cssText = `
          text-align: center; 
          padding: 40px 20px; 
          color: #666;
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          margin: 20px 0;
      `;
      messageDiv.innerHTML = `
          <div style="font-size: 48px; margin-bottom: 15px;">📝</div>
          <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">음성파일과 텍스트 노트가 없습니다</div>
          <div style="font-size: 14px; color: #888;">
              음성파일을 업로드하거나 텍스트 노트를 추가해보세요
          </div>
      `;
      audioFilesList.appendChild(messageDiv);
  }
}

// 음성파일 순서 저장 함수
function saveAudioFileOrder(sortableContainer) {
  if (!window.currentDetailRowId) {
      console.error('현재 행 ID가 없습니다.');
      return;
  }
  
  const fileElements = sortableContainer.children;
  const orderedFiles = [];
  
  for (let i = 0; i < fileElements.length; i++) {
      const element = fileElements[i];
      const date = element.getAttribute('data-date');
      const fileId = element.getAttribute('data-file-id');
      
      if (date && fileId) {
          orderedFiles.push({
              date: date,
              file_id: fileId
          });
      }
  }
  
  console.log('저장할 순서:', orderedFiles);
  
  fetch('/600/update_audio_file_order/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&ordered_files=${encodeURIComponent(JSON.stringify(orderedFiles))}`
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          console.log('파일 순서 저장 완료');
          // 성공 알림 (선택사항)
          showNotification('파일 순서가 저장되었습니다.', 'success');
      } else {
          console.error('파일 순서 저장 실패:', data.error);
          showNotification('파일 순서 저장에 실패했습니다.', 'error');
      }
  })
  .catch(error => {
      console.error('파일 순서 저장 오류:', error);
      showNotification('파일 순서 저장 중 오류가 발생했습니다.', 'error');
  });
}

// 개별 음성파일 요소 생성 함수
function createAudioFileElement(fileData, index) {
  const { date, fileId, fileInfo } = fileData;
  
  const fileElement = document.createElement('div');
  fileElement.className = 'audio-file-item';
  fileElement.style.cssText = `
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 15px;
      background: #f9f9f9;
      cursor: move;
      transition: all 0.2s ease;
      margin-bottom: 10px;
  `;
  fileElement.setAttribute('data-date', date);
  fileElement.setAttribute('data-file-id', fileId);
  fileElement.setAttribute('data-type', 'audio');
  fileElement.setAttribute('data-order', fileInfo.order || 0);
  
  // 호버 효과
  fileElement.onmouseenter = () => fileElement.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
  fileElement.onmouseleave = () => fileElement.style.boxShadow = 'none';
  
  fileElement.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <div style="flex: 1;">
              <div style="font-weight: bold; color: #333; margin-bottom: 4px;">
                  🎵 ${fileInfo.original_filename}
              </div>
              <div style="font-size: 12px; color: #666;">
                  업로드: ${fileInfo.upload_date} ${fileInfo.upload_time} | 크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB
              </div>
          </div>
          <div style="display: flex; gap: 5px; margin-left: 15px;">
            
              <a href="${fileInfo.download_url}" download="${fileInfo.original_filename}" 
                 style="padding: 6px 12px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; display: inline-block;">
                  다운로드
              </a>
              <button onclick="showTranscript('${date}', '${fileId}', ${JSON.stringify(fileInfo).replace(/"/g, '&quot;')})" 
                      style="padding: 6px 12px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                  녹취록
              </button>
              <button onclick="deleteAudioFileItem('${date}', '${fileId}', '${fileInfo.original_filename}')" 
                      style="padding: 6px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                  삭제
              </button>
          </div>
      </div>
      
      <!-- AI 요약 토글 영역 -->
      ${fileInfo.gpt_summary ? `
          <div style="margin-bottom: 10px;">
              <button onclick="toggleSummary('summary-${date}-${fileId}')" 
                      style="background: none; border: none; color: #007bff; cursor: pointer; display: flex; align-items: center; font-weight: bold; padding: 5px 0;">
                  <span id="toggle-icon-summary-${date}-${fileId}" style="margin-right: 5px;">▶</span>
                  AI 요약
              </button>
              <div id="summary-${date}-${fileId}" style="background: #e7f3ff; border: 1px solid #bee5eb; border-radius: 4px; padding: 12px; margin-top: 5px; display: none;">
                  <div style="font-size: 13px; line-height: 1.4; color: #0c5460; white-space: pre-wrap;">${fileInfo.gpt_summary}
                  </div>
              </div>
          </div>
      ` : `
          <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 12px; margin-bottom: 10px; text-align: center;">
              <div style="font-size: 13px; color: #6c757d;">AI 요약이 없습니다.</div>
          </div>
      `}
      
      <!-- 메모 영역 제거 - 편집 모달에서만 메모 편집 가능 -->
  `;
  
  return fileElement;
}

// AI 요약 토글 함수
function toggleSummary(summaryId) {
  const summaryDiv = document.getElementById(summaryId);
  const toggleIcon = document.getElementById('toggle-icon-' + summaryId);
  
  if (summaryDiv && toggleIcon) {
      if (summaryDiv.style.display === 'none') {
          summaryDiv.style.display = 'block';
          toggleIcon.textContent = '▼';
      } else {
          summaryDiv.style.display = 'none';
          toggleIcon.textContent = '▶';
      }
  }
}

// 메모 저장 함수 제거됨 - 편집 모달에서만 메모 편집 가능

// 개별 파일 삭제 함수
function deleteAudioFileItem(date, fileId, filename) {
  if (!confirm(`"${filename}" 파일을 삭제하시겠습니까?\n삭제된 파일과 텍스트는 복구할 수 없습니다.`)) {
      return;
  }
  
  fetch('/600/delete_audio_file/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent(date)}&file_id=${encodeURIComponent(fileId)}`
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          alert('파일이 성공적으로 삭제되었습니다.');
          
          // 선택된 텍스트 영역 숨기기 (삭제된 파일이 선택되어 있던 경우)
          if (window.selectedAudioFile && 
              window.selectedAudioFile.date === date && 
              window.selectedAudioFile.fileId === fileId) {
              const selectedAudioTextArea = document.getElementById('selectedAudioTextArea');
              if (selectedAudioTextArea) {
                  selectedAudioTextArea.style.display = 'none';
              }
              window.selectedAudioFile = null;
          }
          
          // 음성파일 데이터 새로고침
          refreshAudioFileData();
          
          // 테이블과 칸반보드 새로고침
          refreshTable();
          if (window.kanbanAttribute && '음성파일' === window.kanbanAttribute) {
              refreshKanban();
          }
      } else {
          alert('파일 삭제 실패: ' + (data.error || '알 수 없는 오류'));
      }
  })
  .catch(error => {
      console.error('파일 삭제 오류:', error);
      alert('파일 삭제 중 오류가 발생했습니다.');
  });
}

// 음성파일 선택하여 편집 모드로 전환
function selectAudioFile(date, fileId, fileInfo) {
  const selectedAudioTextArea = document.getElementById('selectedAudioTextArea');
  const selectedAudioFileName = document.getElementById('selectedAudioFileName');
  const convertedText = document.getElementById('convertedText');
  
  // 전역 변수에 선택된 파일 정보 저장
  window.selectedAudioFile = {
      date: date,
      fileId: fileId,
      fileInfo: fileInfo
  };
  
  // 텍스트 영역 표시 및 내용 설정
  selectedAudioTextArea.style.display = 'flex';
  selectedAudioFileName.textContent = `(${fileInfo.original_filename || 'Unknown'})`;
  convertedText.value = fileInfo.converted_text || '';
  
  // 텍스트 영역으로 스크롤
  selectedAudioTextArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// deleteAudioFile 함수 복구
function deleteAudioFile(date, fileId) {
  if (!confirm('이 음성파일을 삭제하시겠습니까?')) {
      return;
  }
  
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch('/600/delete_audio_file/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken
      },
      body: `row_id=${window.currentDetailRowId}&date=${date}&file_id=${fileId}`
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          alert('음성파일이 삭제되었습니다.');
          refreshAudioFileData();
          
          // 선택된 파일이 삭제된 경우 편집 영역 숨기기
          if (window.selectedAudioFile && 
              window.selectedAudioFile.date === date && 
              window.selectedAudioFile.fileId === fileId) {
              const selectedAudioTextArea = document.getElementById('selectedAudioTextArea');
              if (selectedAudioTextArea) {
                  selectedAudioTextArea.style.display = 'none';
              }
              window.selectedAudioFile = null;
          }
          
          refreshTable();
      } else {
          alert('삭제 실패: ' + (data.error || '알 수 없는 오류'));
      }
  })
  .catch(error => {
      console.error('음성파일 삭제 오류:', error);
      alert('삭제 중 오류가 발생했습니다.');
  });
}

// refreshAudioFileData 함수 복구
function refreshAudioFileData() {
  if (!window.currentDetailRowId) return;
  
  // 현재 행의 전체 상세 데이터를 다시 가져와서 모달 업데이트
  fetch('/600/get_row_details/' + window.currentDetailRowId + '/')
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          // 음성파일 데이터만 업데이트
          const audioFileValue = data.row_data['음성파일'];
          console.log('새로고침된 음성파일 데이터:', audioFileValue);
          
          // DOM 요소가 준비된 후에 실행하도록 setTimeout 사용
          setTimeout(() => {
              try {
                  updateAudioFileManagement(audioFileValue);
              } catch (error) {
                  console.error('음성파일 관리 영역 업데이트 오류:', error);
              }
          }, 100);
      } else {
          console.error('행 상세 데이터 가져오기 실패:', data.error);
      }
  })
  .catch(error => {
      console.error('음성파일 데이터 새로고침 오류:', error);
  });
}

// 음성파일 삭제 함수 (기존 호환성을 위해 유지)
function deleteAudioFile() {
  if (window.selectedAudioFile) {
      deleteSelectedAudioFile();
  } else {
      alert('선택된 파일이 없습니다.');
  }
}

// 녹취록 보기 함수
function showTranscript(date, fileId, fileInfo) {
  const modal = document.createElement('div');
  modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
  `;
  
  const content = document.createElement('div');
  content.style.cssText = `
      background: white;
      border-radius: 8px;
      padding: 20px;
      max-width: 80%;
      max-height: 80%;
      overflow-y: auto;
      position: relative;
  `;
  
  content.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
          <h3 style="margin: 0; color: #333;"> ${fileInfo.original_filename} - 녹취록</h3>
          <button onclick="this.closest('.transcript-modal').remove()" 
                  style="background: #dc3545; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 16px;">
              ×
          </button>
      </div>
      <div style="font-size: 12px; color: #666; margin-bottom: 15px;">
          업로드 시간: ${fileInfo.upload_time} | 파일 크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB
      </div>
      <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 15px; white-space: pre-wrap; line-height: 1.6; font-family: monospace;">${fileInfo.converted_text || '변환된 텍스트가 없습니다.'}
      </div>
      <div style="text-align: right; margin-top: 15px;">
          <button onclick="this.closest('.transcript-modal').remove()" 
                  style="padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
              닫기
          </button>
      </div>
  `;
  
  modal.className = 'transcript-modal';
  modal.appendChild(content);
  document.body.appendChild(modal);
  
  // 모달 외부 클릭 시 닫기
  modal.onclick = function(e) {
      if (e.target === modal) {
          modal.remove();
      }
  };
}

// 음성파일 편집 모달창 표시 함수
function showEditModal(date, fileId, fileInfo) {
  const modal = document.createElement('div');
  modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
  `;
  
  const content = document.createElement('div');
  content.style.cssText = `
      background: white;
      border-radius: 8px;
      padding: 20px;
      max-width: 80%;
      max-height: 80%;
      overflow-y: auto;
      position: relative;
  `;
  
  content.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
          <h3 style="margin: 0; color: #333;">${fileInfo.original_filename} - 편집</h3>
          <button onclick="this.closest('.edit-modal').remove()" 
                  style="background: #dc3545; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 16px;">
              ×
          </button>
      </div>
      <div style="font-size: 12px; color: #666; margin-bottom: 15px;">
          업로드 시간: ${fileInfo.upload_time} | 파일 크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB
      </div>
      
      <!-- 변환된 텍스트 편집 영역 -->
      <div style="margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <h4 style="margin: 0; color: #333;">변환된 텍스트</h4>
              <button onclick="saveEditedText('${date}', '${fileId}')" 
                      style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                  텍스트 저장
              </button>
          </div>
          <textarea id="editModal-convertedText-${date}-${fileId}" 
                    style="width: 100%; min-height: 200px; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; line-height: 1.5; resize: vertical; box-sizing: border-box;"
                    placeholder="변환된 텍스트를 편집하세요...">${fileInfo.converted_text || ''}</textarea>
      </div>
      
      <!-- 메모 편집 영역 -->
      <div style="margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <h4 style="margin: 0; color: #333;">메모</h4>
              <button onclick="saveEditedMemo('${date}', '${fileId}')" 
                      style="padding: 8px 16px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer;">
                  메모 저장
              </button>
          </div>
          <textarea id="editModal-memo-${date}-${fileId}" 
                    style="width: 100%; min-height: 100px; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; line-height: 1.5; resize: vertical; box-sizing: border-box;"
                    placeholder="메모를 입력하세요...">${fileInfo.memo || ''}</textarea>
      </div>
      
      <!-- AI 요약 표시 영역 -->
      ${fileInfo.gpt_summary ? `
          <div style="margin-bottom: 20px;">
              <h4 style="margin: 0 0 10px 0; color: #333;">AI 요약</h4>
              <div style="background: #e7f3ff; border: 1px solid #bee5eb; border-radius: 4px; padding: 15px;">
                  <div style="font-size: 14px; line-height: 1.6; color: #0c5460; white-space: pre-wrap;">
                      ${fileInfo.gpt_summary}
                  </div>
              </div>
          </div>
      ` : `
          <div style="margin-bottom: 20px;">
              <h4 style="margin: 0 0 10px 0; color: #333;">AI 요약</h4>
              <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 15px; text-align: center;">
                  <div style="font-size: 14px; color: #6c757d;">AI 요약이 없습니다.</div>
              </div>
          </div>
      `}
      
      <div style="text-align: right; margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px;">
          <button onclick="this.closest('.edit-modal').remove()" 
                  style="padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px;">
              닫기
          </button>
          <button onclick="showTranscript('${date}', '${fileId}', ${JSON.stringify(fileInfo).replace(/"/g, '&quot;')}); this.closest('.edit-modal').remove();" 
                  style="padding: 8px 16px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer;">
              녹취록 보기
          </button>
      </div>
  `;
  
  modal.className = 'edit-modal';
  modal.appendChild(content);
  document.body.appendChild(modal);
  
  // 모달 외부 클릭 시 닫기
  modal.onclick = function(e) {
      if (e.target === modal) {
          modal.remove();
      }
  };
}

// 편집된 텍스트 저장 함수
function saveEditedText(date, fileId) {
  const textArea = document.getElementById(`editModal-convertedText-${date}-${fileId}`);
  if (!textArea || !window.currentDetailRowId) {
      alert('텍스트를 저장할 수 없습니다.');
      return;
  }
  
  const textValue = textArea.value;
  
  fetch('/600/update_audio_text/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent(date)}&file_id=${encodeURIComponent(fileId)}&converted_text=${encodeURIComponent(textValue)}`
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          showNotification('텍스트가 성공적으로 저장되었습니다.', 'success');
          // 음성파일 데이터 새로고침
          refreshAudioFileData();
      } else {
          showNotification('텍스트 저장에 실패했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
      }
  })
  .catch(error => {
      console.error('텍스트 저장 오류:', error);
      showNotification('텍스트 저장 중 오류가 발생했습니다.', 'error');
  });
}

// 편집된 메모 저장 함수
function saveEditedMemo(date, fileId) {
  const memoTextarea = document.getElementById(`editModal-memo-${date}-${fileId}`);
  if (!memoTextarea || !window.currentDetailRowId) {
      alert('메모를 저장할 수 없습니다.');
      return;
  }
  
  const memoText = memoTextarea.value;
  
  fetch('/600/update_audio_memo/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent(date)}&file_id=${encodeURIComponent(fileId)}&memo=${encodeURIComponent(memoText)}`
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          showNotification('메모가 성공적으로 저장되었습니다.', 'success');
          // 음성파일 데이터 새로고침
          refreshAudioFileData();
      } else {
          showNotification('메모 저장에 실패했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
      }
  })
  .catch(error => {
      console.error('메모 저장 오류:', error);
      showNotification('메모 저장 중 오류가 발생했습니다.', 'error');
  });
}

function showNewAudioUpload(targetDate = null) {
  window.targetUploadDate = targetDate; // 특정 날짜 지정 시 해당 날짜로 업로드
  
  // 파일 선택 다이얼로그 열기
  const fileInput = document.getElementById('audioFileInput');
  if (fileInput) {
      fileInput.click();
  }
}

// 음성파일 변경 함수 (기존 호환성을 위해 유지)
function changeAudioFile() {
  showNewAudioUpload();
}

function saveTextNotesToServer() {
    if (!window.currentDetailRowId) return;
    const notes = [];
    const container = document.getElementById('sortableAudioContainer');
    if (!container) return;
    const actualItems = container.querySelectorAll('.audio-file-item, .text-note-item');
    let noteIndex = 0;
    actualItems.forEach((el, idx) => {
        if (el.classList.contains('text-note-item')) {
            const textarea = el.querySelector('textarea');
            let id = el.dataset.noteId;
            if (!id) {
                id = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
                el.dataset.noteId = id;
            }
            notes.push({ 
                id, 
                text: textarea.value, 
                order: noteIndex,
                type: 'text',
                upload_date: getTodayStr()
            });
            noteIndex++;
        }
    });
    fetch('/600/update_audio_text_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent('data')}&notes=${encodeURIComponent(JSON.stringify(notes))}`
    }).then(r=>r.json()).then(data=>{
        if(!data.success) alert('텍스트 저장 실패: '+(data.error||''));
    });
}

function addTextArea() {
    let sortableContainer = document.getElementById('sortableAudioContainer');
    if (!sortableContainer) {
        // 음성파일이 없어도 컨테이너 생성
        sortableContainer = document.createElement('div');
        sortableContainer.id = 'sortableAudioContainer';
        sortableContainer.style.cssText = 'display: flex; flex-direction: column; gap: 0; position: relative;';
        const audioFilesList = document.getElementById('audioFilesList');
        if (audioFilesList) {
            audioFilesList.innerHTML = '';
            audioFilesList.appendChild(sortableContainer);
        }
        // 맨 앞에 placeholder 추가
        sortableContainer.appendChild(createAddPlaceholder(0));
    }
    const actualItems = sortableContainer.querySelectorAll('.audio-file-item, .text-note-item');
    const newIndex = actualItems.length;
    const noteId = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
    const newNoteData = {
        type: 'text',
        noteId: noteId,
        text: '',
        order: newIndex
    };
    const textElement = createTextNoteElement(newNoteData, newIndex);
    sortableContainer.appendChild(textElement);
    const placeholder = createAddPlaceholder(newIndex + 1);
    sortableContainer.appendChild(placeholder);
    saveTextNotesToServer();
}

function insertTextNoteAtIndex(index) {
    let sortableContainer = document.getElementById('sortableAudioContainer');
    if (!sortableContainer) {
        sortableContainer = document.createElement('div');
        sortableContainer.id = 'sortableAudioContainer';
        sortableContainer.style.cssText = 'display: flex; flex-direction: column; gap: 0; position: relative;';
        const audioFilesList = document.getElementById('audioFilesList');
        if (audioFilesList) {
            audioFilesList.innerHTML = '';
            audioFilesList.appendChild(sortableContainer);
        }
        sortableContainer.appendChild(createAddPlaceholder(0));
        index = 0;
    }
    const actualItems = sortableContainer.querySelectorAll('.audio-file-item, .text-note-item');
    const newOrder = [];
    for (let i = 0; i < index; i++) {
        if (actualItems[i]) {
            const item = actualItems[i];
            if (item.classList.contains('audio-file-item')) {
                const fileId = item.getAttribute('data-file-id');
                newOrder.push({ file_id: fileId, order: i });
            } else if (item.classList.contains('text-note-item')) {
                const noteId = item.dataset.noteId;
                const textarea = item.querySelector('textarea');
                newOrder.push({ id: noteId, text: textarea ? textarea.value : '', order: i, type: 'text', upload_date: getTodayStr() });
            }
        }
    }
    const noteId = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
    newOrder.push({ id: noteId, text: '', order: index, type: 'text', upload_date: getTodayStr() });
    for (let i = index; i < actualItems.length; i++) {
        if (actualItems[i]) {
            const item = actualItems[i];
            if (item.classList.contains('audio-file-item')) {
                const fileId = item.getAttribute('data-file-id');
                newOrder.push({ file_id: fileId, order: i + 1 });
            } else if (item.classList.contains('text-note-item')) {
                const noteId = item.dataset.noteId;
                const textarea = item.querySelector('textarea');
                newOrder.push({ id: noteId, text: textarea ? textarea.value : '', order: i + 1, type: 'text', upload_date: getTodayStr() });
            }
        }
    }
    const notes = newOrder.filter(item => item.type === 'text');
    const audioOrders = newOrder.filter(item => !item.type);
    fetch('/600/update_audio_file_order_and_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent('data')}&notes=${encodeURIComponent(JSON.stringify(notes))}&ordered_files=${encodeURIComponent(JSON.stringify(audioOrders))}`
    }).then(r => r.json()).then(data => {
        if (data.success) {
            refreshAudioFileData();
        } else {
            console.error('텍스트 추가 실패:', data.error);
            alert('텍스트 추가 실패: ' + (data.error || ''));
        }
    });
}

function saveAllOrderToServer(sortableContainer) {
    if (!window.currentDetailRowId) return;
    const notes = [];
    const audioOrders = [];
    const container = sortableContainer || document.getElementById('sortableAudioContainer');
    if (!container) return;
    const actualItems = container.querySelectorAll('.audio-file-item, .text-note-item');
    actualItems.forEach((el, idx) => {
        if (el.classList.contains('text-note-item')) {
            const textarea = el.querySelector('textarea');
            let id = el.dataset.noteId;
            if (!id) {
                id = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
                el.dataset.noteId = id;
            }
            notes.push({ 
                id, 
                text: textarea.value, 
                order: idx,
                type: 'text',
                upload_date: getTodayStr()
            });
        } else if (el.classList.contains('audio-file-item')) {
            const date = el.getAttribute('data-date');
            const fileId = el.getAttribute('data-file-id');
            if (date && fileId) {
                audioOrders.push({ 
                    date, 
                    file_id: fileId, 
                    order: idx 
                });
            }
        }
    });
    fetch('/600/update_audio_file_order_and_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent('data')}&notes=${encodeURIComponent(JSON.stringify(notes))}&ordered_files=${encodeURIComponent(JSON.stringify(audioOrders))}`
    }).then(r=>r.json()).then(data=>{
        if(data.success) {
            console.log('순서 저장 성공');
        } else {
            console.error('순서 저장 실패:', data.error);
            alert('순서 저장 실패: '+(data.error||''));
            refreshAudioFileData();
        }
    }).catch(error => {
        console.error('순서 저장 중 오류:', error);
        alert('순서 저장 중 오류가 발생했습니다.');
        refreshAudioFileData();
    });
}

// 텍스트 노트 요소 생성 함수
function createTextNoteElement(noteData, index) {
  const { noteId, text, order } = noteData;
  
  const textElement = document.createElement('div');
  textElement.className = 'text-note-item';
  textElement.style.cssText = `
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 15px;
      cursor: move;
      transition: all 0.2s ease;
      margin-bottom: 10px;
  `;
  textElement.setAttribute('data-note-id', noteId);
  textElement.setAttribute('data-type', 'text');
  textElement.setAttribute('data-order', order);
  
  // 호버 효과
  textElement.onmouseenter = () => textElement.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
  textElement.onmouseleave = () => textElement.style.boxShadow = 'none';
  
  // 삭제 버튼 호버 효과 추가
  textElement.addEventListener('mouseenter', function() {
      const deleteBtn = this.querySelector('button');
      if (deleteBtn) {
          deleteBtn.style.background = '#c82333';
          deleteBtn.style.transform = 'scale(1.1)';
      }
  });
  
  textElement.addEventListener('mouseleave', function() {
      const deleteBtn = this.querySelector('button');
      if (deleteBtn) {
          deleteBtn.style.background = '#dc3545';
          deleteBtn.style.transform = 'scale(1)';
      }
  });
  
  textElement.innerHTML = `
      <div style="position: relative;">
          <button onclick="deleteTextNote('${noteId}')" 
                  style="position: absolute;
                    top: -8px;
                    right: -8px;
                    width: 24px;
                    height: 24px;
                    background: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    transition: all 0.2s ease;">×</button>
          <textarea id="text-note-${noteId}" 
                    style="width: 100%; min-height: 50px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; line-height: 1.5; resize: none; box-sizing: border-box; overflow-y: hidden;"
                    placeholder="텍스트 노트를 입력하세요...">${text}</textarea>
      </div>
  `;
  
  // textarea 입력시 저장
  const textarea = textElement.querySelector(`#text-note-${noteId}`);
  
  // 디바운스된 저장 함수 (중복 저장 방지)
  let saveTimeout;
  textarea.addEventListener('input', function() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      saveTextNotesToServer();
    }, 500); // 0.5초 후 저장
  });
  
  // textarea 높이 자동 조절 함수
  function autoResizeTextarea(textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
  }
  
  // 초기 높이 설정 (텍스트 내용이 설정된 후에 실행)
  setTimeout(() => {
      autoResizeTextarea(textarea);
  }, 0);
  
  // 입력 시 높이 자동 조절
  textarea.addEventListener('input', function() {
      autoResizeTextarea(this);
  });
  
  return textElement;
}

// 텍스트 노트 삭제 함수
function deleteTextNote(noteId) {
    console.log('deleteTextNote 호출됨:', noteId);
    const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
    if (!noteElement) {
        console.log('삭제할 노트 요소를 찾을 수 없음:', noteId);
        return;
    }
    const sortableContainer = document.getElementById('sortableAudioContainer');
    if (!sortableContainer) {
        console.error('sortableAudioContainer를 찾을 수 없음');
        return;
    }
    const actualItems = sortableContainer.querySelectorAll('.audio-file-item, .text-note-item');
    let targetIndex = -1;
    for (let i = 0; i < actualItems.length; i++) {
        if (actualItems[i] === noteElement) {
            targetIndex = i;
            break;
        }
    }
    console.log('삭제할 요소 인덱스:', targetIndex);
    if (targetIndex === -1) {
        console.log('삭제할 요소의 인덱스를 찾을 수 없음');
        return;
    }
    const remainingNotes = [];
    actualItems.forEach((el, idx) => {
        if (el !== noteElement && el.classList.contains('text-note-item')) {
            const textarea = el.querySelector('textarea');
            let id = el.dataset.noteId;
            if (!id) {
                id = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
                el.dataset.noteId = id;
            }
            const adjustedIndex = idx > targetIndex ? idx - 1 : idx;
            remainingNotes.push({ 
                id, 
                text: textarea ? textarea.value : '', 
                order: adjustedIndex,
                type: 'text',
                upload_date: getTodayStr()
            });
        }
    });
    console.log('삭제 후 남을 노트들:', remainingNotes);
    fetch('/600/update_audio_text_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent('data')}&notes=${encodeURIComponent(JSON.stringify(remainingNotes))}`
    }).then(r=>r.json()).then(data=>{
        if(data.success) {
            console.log('서버에 삭제 상태 저장 성공');
            noteElement.remove();
            const placeholders = sortableContainer.querySelectorAll('.add-placeholder');
            for (let i = 0; i < placeholders.length - 1; i++) {
                const current = placeholders[i];
                const next = placeholders[i + 1];
                let hasOtherElement = false;
                let element = current.nextElementSibling;
                while (element && element !== next) {
                    if (!element.classList.contains('add-placeholder')) {
                        hasOtherElement = true;
                        break;
                    }
                    element = element.nextElementSibling;
                }
                if (!hasOtherElement) {
                    next.remove();
                }
            }
            console.log('텍스트 노트 삭제 완료');
        } else {
            console.error('텍스트 삭제 저장 실패:', data.error);
            alert('텍스트 삭제 실패: ' + (data.error || ''));
        }
    }).catch(error => {
        console.error('텍스트 삭제 요청 오류:', error);
        alert('텍스트 삭제 중 오류가 발생했습니다.');
    });
}

// 셀 사이에 hover 시만 보이는 텍스트 추가 placeholder 생성 함수
function createAddPlaceholder(insertIndex) {
    const placeholder = document.createElement('div');
    placeholder.className = 'add-placeholder';
    placeholder.style.cssText = `
        width: 100%;
        height: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        cursor: pointer;
        transition: all 0.2s;
        overflow: hidden;
    `;
    // 내부 버튼(실제 텍스트 추가 표시)
    const btn = document.createElement('div');
    btn.textContent = '텍스트 추가';
    btn.style.cssText = `
        display: none;
        height: 50px;
        border: 1px dashed #bbb;
        border-radius: 6px;
        padding: 2px 16px;
        font-size: 13px;
        color: #888;
        transition: all 0.2s;
        pointer-events: none;
        user-select: none;
        border: 1px dotted;
        width: 100%;
        border-radius: 10px;
        align-items: center;
        justify-content: center;
    `;
    placeholder.appendChild(btn);
    // hover 시만 보이게
    placeholder.onmouseenter = () => { 
        placeholder.style.height = '60px';
        placeholder.style.marginTop = '0px';
        placeholder.style.marginBottom = '10px';
        btn.style.display = 'flex';
    };
    placeholder.onmouseleave = () => { 
        placeholder.style.height = '5px';
        placeholder.style.marginTop = '0px';
        placeholder.style.marginBottom = '0px';
        btn.style.display = 'none';
    };
    // 클릭 시 텍스트 셀 추가
    placeholder.onclick = function(e) {
        e.stopPropagation();
        insertTextNoteAtIndex(insertIndex);
    };
    return placeholder;
}

// 오늘 날짜를 YY.MM.DD 형식으로 반환하는 함수
function getTodayStr() {
    const d = new Date();
    return d.toISOString().slice(2, 10).replace(/-/g, '.');
}