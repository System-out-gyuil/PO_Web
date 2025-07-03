// updateAudioFileOrder 함수 복구
function updateAudioFileOrder(rowId, fileId, newOrder) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch('/diary/update_audio_file_order/', {
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
  
  if (audioFileData && Object.keys(audioFileData).length > 0) {
      // 모든 파일을 하나의 배열로 수집
      let allFiles = [];
      Object.keys(audioFileData).forEach(date => {
          const dateFiles = audioFileData[date] || {};
          Object.keys(dateFiles).forEach(fileId => {
              const fileInfo = dateFiles[fileId];
              allFiles.push({
                  date: date,
                  fileId: fileId,
                  fileInfo: fileInfo,
                  uploadTime: new Date(fileInfo.upload_time || '2024-01-01'),
                  order: fileInfo.order !== undefined ? fileInfo.order : 9999 // order가 없는 경우 가장 뒤로
              });
          });
      });
      
      // 1차: order 필드로 정렬 (order가 있는 파일들)
      // 2차: 업로드 시간으로 정렬 (새로 업로드된 파일이 위에 오도록)
      allFiles.sort((a, b) => {
          // order가 둘 다 있으면 order로 정렬
          if (a.order !== 9999 && b.order !== 9999) {
              return a.order - b.order;
          }
          // 한쪽만 order가 없으면 order가 있는 것이 앞으로
          if (a.order !== 9999 && b.order === 9999) {
              return -1;
          }
          if (a.order === 9999 && b.order !== 9999) {
              return 1;
          }
          // 둘 다 order가 없으면 업로드 시간으로 정렬 (최신이 위)
          return b.uploadTime - a.uploadTime;
      });
      
      if (allFiles.length > 0) {
          if (noAudioFilesMessage) {
              noAudioFilesMessage.style.display = 'none';
          }
          
          // 드래그 앤 드롭 컨테이너 생성
          const sortableContainer = document.createElement('div');
          sortableContainer.id = 'sortableAudioContainer';
          sortableContainer.style.cssText = 'display: flex; flex-direction: column; gap: 15px;';
          
          allFiles.forEach((fileData, index) => {
              const fileElement = createAudioFileElement(fileData, index);
              sortableContainer.appendChild(fileElement);
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
                      console.log('파일 순서 변경:', evt.oldIndex, '->', evt.newIndex);
                      saveAudioFileOrder(sortableContainer);
                  }
              });
          }
      } else {
          if (noAudioFilesMessage) {
              noAudioFilesMessage.style.display = 'block';
              audioFilesList.appendChild(noAudioFilesMessage);
          }
      }
  } else {
      if (noAudioFilesMessage) {
          noAudioFilesMessage.style.display = 'block';
          audioFilesList.appendChild(noAudioFilesMessage);
      }
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
  
  fetch('/diary/update_audio_file_order/', {
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
  `;
  fileElement.setAttribute('data-date', date);
  fileElement.setAttribute('data-file-id', fileId);
  
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
                  ${date} | 크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB | 업로드: ${fileInfo.upload_time}
              </div>
          </div>
          <div style="display: flex; gap: 5px; margin-left: 15px;">
              <button onclick="showEditModal('${date}', '${fileId}', ${JSON.stringify(fileInfo).replace(/"/g, '&quot;')})" 
                      style="display: none; padding: 6px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                  편집
              </button>
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
              <div id="summary-${date}-${fileId}" style=" border: 1px solid #bee5eb; border-radius: 4px; padding: 12px; margin-top: 5px; display: none;">
                  <div style="font-size: 13px; line-height: 1.4;  white-space: pre-wrap;">${fileInfo.gpt_summary}</div>
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
  
  fetch('/diary/delete_audio_file/', {
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
  
  fetch('/diary/delete_audio_file/', {
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
  fetch('/diary/get_row_details/' + window.currentDetailRowId + '/')
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
      <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 15px; white-space: pre-wrap; line-height: 1.6; font-family: monospace;">${fileInfo.converted_text || '변환된 텍스트가 없습니다.'}</div>
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
  
  fetch('/diary/update_audio_text/', {
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
  
  fetch('/diary/update_audio_memo/', {
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