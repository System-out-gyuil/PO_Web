// updateAudioFileOrder 함수 복구
function updateAudioFileOrder(rowId, fileId, newOrder) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch('/sales/update_audio_file_order/', {
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
      
      // data 객체에서 파일들을 수집
      if (audioFileData.data) {
          Object.keys(audioFileData.data).forEach(fileId => {
              const fileInfo = audioFileData.data[fileId];
              
              // 파일 타입 결정 (서버에서 저장된 타입 우선)
              let fileType = fileInfo.type || 'file'; // 기본값
              
              // 타입이 없거나 불분명한 경우 content_type으로 추론
              if (!fileType || fileType === 'file') {
                  if (fileInfo.content_type) {
                      if (fileInfo.content_type.startsWith('audio/')) {
                          fileType = 'audio';
                      } else if (fileInfo.content_type.startsWith('image/')) {
                          fileType = 'image';
                      } else {
                          fileType = 'file';
                      }
                  }
              }
              
              console.log(`파일 ${fileId} 타입 결정:`, fileType, fileInfo);
              
              // 텍스트 노트인 경우 특별 처리
              if (fileType === 'text') {
                  allItems.push({
                      type: 'text',
                      fileId: fileId,
                      noteId: fileId, // 텍스트 노트용 ID
                      text: fileInfo.text || '',
                      order: fileInfo.order !== undefined ? fileInfo.order : 9999
                  });
              } else {
                  allItems.push({
                      type: fileType,
                      fileId: fileId,
                      fileInfo: fileInfo,
                      uploadTime: new Date(fileInfo.upload_time || '2024-01-01'),
                      order: fileInfo.order !== undefined ? fileInfo.order : 9999
                  });
              }
          });
      }
      
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
          if (a.type === 'text' && b.type !== 'text') {
              return -1;
          }
          if (a.type !== 'text' && b.type === 'text') {
              return 1;
          }
          // 같은 타입이면 업로드 시간으로 정렬 (최신이 위)
          return b.uploadTime - a.uploadTime;
      });
      
      console.log('정렬된 모든 아이템:', allItems);
      
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
              console.log(`렌더링 아이템 ${index}:`, item);
              
              if (item.type === 'audio') {
                  console.log('audio 아이템 렌더링:', item);
                  const fileElement = createAudioFileElement(item, index);
                  sortableContainer.appendChild(fileElement);
              } else if (item.type === 'image') {
                  console.log('image 아이템 렌더링:', item);
                  const imageElement = createImageFileElement(item, index);
                  sortableContainer.appendChild(imageElement);
              } else if (item.type === 'file') {
                  console.log('file 아이템 렌더링:', item);
                  const fileElement = createDocumentFileElement(item, index);
                  sortableContainer.appendChild(fileElement);
              } else if (item.type === 'text') {
                  console.log('text 아이템 렌더링:', item);
                  // 텍스트 노트 데이터 안전하게 처리
                  const textNoteData = {
                      noteId: item.fileId || item.noteId || ('t' + Date.now() + '_' + Math.floor(Math.random()*10000)),
                      text: item.text || '',
                      order: item.order || index
                  };
                  console.log('텍스트 노트 데이터:', textNoteData);
                  const textElement = createTextNoteElement(textNoteData, index);
                  sortableContainer.appendChild(textElement);
              }
              // 각 셀 뒤에 placeholder
              sortableContainer.appendChild(createAddPlaceholder(index + 1));
          });
          
          audioFilesList.appendChild(sortableContainer);
          
          // 드래그 앤 드롭 이벤트 추가
          setupDragAndDrop(sortableContainer);
          
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
                <div style="font-size: 14px; color: #888; margin-bottom: 24px;">
                    음성파일을 업로드하거나 텍스트 노트를 추가해보세요
                </div>
                <div style="font-size: 12px; color: #999; margin-bottom: 24px; padding: 15px; border: 2px dashed #ddd; border-radius: 8px; background: #fafafa;">
                    💡 파일을 여기에 드래그 앤 드롭하거나 Ctrl+V로 붙여넣기하여 업로드할 수도 있습니다
                </div>
                <div style="display: flex; justify-content: center; gap: 12px;">
                    <button onclick="addTextCell()" style="padding: 10px 18px; background: #bfcfc2; color: #222; border: none; border-radius: 6px; font-size: 15px; font-weight: bold; cursor: pointer;">
                        + 텍스트 추가
                    </button>
                    <button onclick="addFileCell()" style="padding: 10px 18px; background: #22b573; color: #fff; border: none; border-radius: 6px; font-size: 15px; font-weight: bold; cursor: pointer;">
                        + 파일 추가
                    </button>
                </div>
            </div>
        `;
        audioFilesList.appendChild(noAudioFilesMessage);
        
        // 빈 상태에서도 드래그 앤 드롭 설정
        setupDragAndDrop(audioFilesList);
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
          <div style="text-align: center; padding: 40px 20px; color: #666;">
                <div style="font-size: 48px; margin-bottom: 15px;">📝</div>
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">음성파일과 텍스트 노트가 없습니다</div>
                <div style="font-size: 14px; color: #888; margin-bottom: 24px;">
                    음성파일을 업로드하거나 텍스트 노트를 추가해보세요
                </div>
                <div style="font-size: 12px; color: #999; margin-bottom: 24px; padding: 15px; border: 2px dashed #ddd; border-radius: 8px; background: #fafafa;">
                    💡 파일을 여기에 드래그 앤 드롭하거나 Ctrl+V로 붙여넣기하여 업로드할 수도 있습니다
                </div>
                <div style="display: flex; justify-content: center; gap: 12px;">
                    <button onclick="addTextCell()" style="padding: 10px 18px; background: #bfcfc2; color: #222; border: none; border-radius: 6px; font-size: 15px; font-weight: bold; cursor: pointer;">
                        + 텍스트 추가
                    </button>
                    <button onclick="addFileCell()" style="padding: 10px 18px; background: #22b573; color: #fff; border: none; border-radius: 6px; font-size: 15px; font-weight: bold; cursor: pointer;">
                        + 파일 추가
                    </button>
                </div>
            </div>
      `;
      audioFilesList.appendChild(messageDiv);
      
      // 빈 상태에서도 드래그 앤 드롭 설정
      setupDragAndDrop(audioFilesList);
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
  
  fetch('/sales/update_audio_file_order/', {
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
  const { fileId, fileInfo } = fileData;
  
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
                  🎵 ${fileInfo.original_filename || fileInfo.filename}
              </div>
              <div style="font-size: 12px; color: #666;">
                  업로드: ${fileInfo.upload_date || 'N/A'} ${fileInfo.upload_time || ''} | 크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB
              </div>
          </div>
          <div style="display: flex; gap: 5px; margin-left: 15px;">
              <button onclick="showTranscript('${fileId}', ${JSON.stringify(fileInfo).replace(/"/g, '&quot;')})" 
                      style="padding: 6px 12px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                  녹취록
              </button>
              <a href="${fileInfo.download_url}" download="${fileInfo.original_filename || fileInfo.filename}" 
                 style="padding: 6px 12px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; display: inline-block;">
                  다운로드
              </a>
              <button onclick="deleteAudioFileItem('${fileId}', '${fileInfo.original_filename || fileInfo.filename}')" 
                      style="padding: 6px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                  삭제
              </button>
          </div>
      </div>
      
      <!-- AI 요약 토글 영역 -->
      ${fileInfo.gpt_summary ? `
          <div style="margin-bottom: 10px;">
              <button onclick="toggleSummary('summary-${fileId}')" 
                      style="background: none; border: none; color: #007bff; cursor: pointer; display: flex; align-items: center; font-weight: bold; padding: 5px 0;">
                  <span id="toggle-icon-summary-${fileId}" style="margin-right: 5px;">▶</span>
                  AI 요약
              </button>
              <div id="summary-${fileId}" style="background: #e7f3ff; border: 1px solid #bee5eb; border-radius: 4px; padding: 12px; margin-top: 5px; display: none;">
                  <div style="font-size: 13px; line-height: 1.4; color: #0c5460; white-space: pre-wrap;">${fileInfo.gpt_summary}
                  </div>
              </div>
          </div>
      ` : `
          <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 12px; margin-bottom: 10px; text-align: center;">
              <div style="font-size: 13px; color: #6c757d;">AI 요약이 없습니다.</div>
          </div>
      `}
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
function deleteAudioFileItem(fileId, filename) {
    if (!window.currentDetailRowId || !fileId) {
        alert('row_id 또는 file_id가 없습니다.');
        return;
    }
    // fileInfo에서 s3_key 추출
    let s3Key = '';
    if (window.audioFileData && window.audioFileData.data && window.audioFileData.data[fileId]) {
        s3Key = window.audioFileData.data[fileId].s3_key || '';
    }
    if (!s3Key) {
        alert('s3_key가 없습니다. 파일 정보를 확인하세요.');
        return;
    }
    if (!confirm('정말 삭제하시겠습니까?')) return;
    fetch('/sales/delete_note_file/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&file_id=${encodeURIComponent(fileId)}&s3_key=${encodeURIComponent(s3Key)}`
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            refreshAudioFileData();
        } else {
            alert('파일 삭제 실패: ' + (data.error || ''));
        }
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
  
  fetch('/sales/delete_audio_file/', {
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

// 영업노트 섹션 비동기 리렌더링 함수
async function refreshSalesNoteSection() {
    console.log('=== 영업노트 섹션 리렌더링 시작 ===');
    
    if (!window.currentDetailRowId) {
        console.warn('현재 행 ID가 없습니다.');
        return;
    }
    
    try {
        // 서버에서 최신 데이터 가져오기
        const response = await fetch(`/sales/get_row_details/${window.currentDetailRowId}/`);
        const data = await response.json();
        
        if (data.success) {
            const audioFileValue = data.row_data['음성파일'];
            console.log('새로고침된 음성파일 데이터:', audioFileValue);
            
            // DOM 요소가 준비된 후에 실행
            setTimeout(() => {
                try {
                    updateAudioFileManagement(audioFileValue);
                    console.log('영업노트 섹션 리렌더링 완료');
                } catch (error) {
                    console.error('영업노트 섹션 업데이트 오류:', error);
                }
            }, 100);
        } else {
            console.error('행 상세 데이터 가져오기 실패:', data.error);
        }
    } catch (error) {
        console.error('영업노트 섹션 리렌더링 오류:', error);
    }
}

// refreshAudioFileData 함수를 새로운 함수로 교체
function refreshAudioFileData() {
    refreshSalesNoteSection();
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
function showTranscript(fileId, fileInfo) {
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
          <h3 style="margin: 0; color: #333;"> ${fileInfo.original_filename || fileInfo.filename} - 녹취록</h3>
          <button onclick="this.closest('.transcript-modal').remove()" 
                  style="background: #dc3545; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 16px;">
              ×
          </button>
      </div>
      <div style="font-size: 12px; color: #666; margin-bottom: 15px;">
          파일 크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB
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
          <button onclick="showTranscript('${fileId}', ${JSON.stringify(fileInfo).replace(/"/g, '&quot;')}); this.closest('.edit-modal').remove();" 
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
  
  fetch('/sales/update_audio_text/', {
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
  
  fetch('/sales/update_audio_memo/', {
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
    console.log('=== saveTextNotesToServer 시작 ===');
    console.log('현재 window.audioFileData:', window.audioFileData);
    
    const sortableContainer = document.getElementById('sortableAudioContainer');
    if (!sortableContainer) return;
    
    const actualItems = sortableContainer.querySelectorAll('.audio-file-item, .image-file-item, .document-file-item, .text-note-item');
    const allItems = [];
    
    actualItems.forEach((item, index) => {
        if (item.classList.contains('audio-file-item') || item.classList.contains('image-file-item') || item.classList.contains('document-file-item')) {
            const fileId = item.getAttribute('data-file-id');
            const type = item.dataset.type || 'audio';
            
            // 파일 정보를 window.audioFileData에서 가져오기
            let fileInfo = {};
            if (window.audioFileData && window.audioFileData.data && window.audioFileData.data[fileId]) {
                fileInfo = window.audioFileData.data[fileId];
                console.log(`파일 ${fileId}의 기존 정보:`, fileInfo);
            } else {
                console.warn(`파일 ${fileId}의 기존 정보를 찾을 수 없음`);
            }
            
            allItems.push({
                ...fileInfo,
                id: fileId, 
                order: index, 
                type: fileInfo.type || type || 'file'
            });
        } else if (item.classList.contains('text-note-item')) {
            const noteId = item.dataset.noteId;
            const textarea = item.querySelector('textarea');
            const textValue = textarea ? textarea.value : '';
            
            // 기존 텍스트 노트 정보 가져오기
            let textInfo = {};
            if (window.audioFileData && window.audioFileData.data && window.audioFileData.data[noteId]) {
                textInfo = window.audioFileData.data[noteId];
            }
            
            allItems.push({ 
                ...textInfo,
                id: noteId, 
                text: textValue, 
                order: index, 
                type: 'text', 
                upload_date: textInfo.upload_date || getTodayStr() 
            });
        }
    });
    
    console.log('서버로 보낼 allItems:', allItems);
    
    fetch('/sales/update_audio_file_order_and_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&notes=${encodeURIComponent(JSON.stringify(allItems))}`
    }).then(r => r.json()).then(data => {
        console.log('서버 응답:', data);
        if (data.success) {
            console.log('텍스트 노트 저장 성공');
        } else {
            console.error('텍스트 노트 저장 실패:', data.error);
        }
    }).catch(error => {
        console.error('텍스트 노트 저장 중 오류:', error);
    });
}

// 텍스트 셀 추가 함수
function addTextCell() {
    console.log('addTextCell 호출됨');
    
    // audioFileData 초기화
    if (!window.audioFileData) {
        window.audioFileData = { data: {} };
    }
    
    const newId = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
    const order = Object.keys(window.audioFileData.data).length;
    
    // 새 텍스트 노트 데이터 생성
    const newTextNote = {
        id: newId,
        type: 'text',
        text: '',
        order: order,
        upload_date: getTodayStr()
    };
    
    // 로컬 데이터에 추가
    window.audioFileData.data[newId] = newTextNote;
    
    console.log('새 텍스트 노트 데이터:', newTextNote);
    console.log('업데이트된 audioFileData:', window.audioFileData);
    
    // 서버에 저장
    fetch('/sales/update_audio_file_order_and_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&notes=${encodeURIComponent(JSON.stringify([newTextNote]))}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('텍스트 노트 서버 저장 성공');
            // 성공 알림
            showNotification('텍스트 노트가 추가되었습니다.', 'success');
            // 영업노트 섹션 비동기 리렌더링
            refreshSalesNoteSection();
        } else {
            console.error('텍스트 노트 서버 저장 실패:', data.error);
            showNotification('텍스트 노트 추가 실패: ' + (data.error || ''), 'error');
        }
    })
    .catch(error => {
        console.error('텍스트 노트 추가 중 오류:', error);
        showNotification('텍스트 노트 추가 중 오류가 발생했습니다.', 'error');
    });
}

// 파일 추가 함수 (파일 업로드 input 트리거)
function addFileCell() {
    console.log('addFileCell 호출됨');
    
    let fileInput = document.getElementById('multiFileInput');
    if (!fileInput) {
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'multiFileInput';
        fileInput.style.display = 'none';
        fileInput.onchange = function() { 
            handleMultiFileUpload(this); 
        };
        document.body.appendChild(fileInput);
    }
    fileInput.value = '';
    fileInput.click();
}

// 파일 업로드 핸들러 (오디오는 기존 로직, 그 외는 type별로 dict 저장)
function handleMultiFileUpload(fileInput) {
  const file = fileInput.files[0];
  if (!file) return;
  // 오디오는 기존 로직 사용
  if (file.type.startsWith('audio/')) {
    handleAudioFileUpload(file, 0); // insertIndex를 0으로 설정
    return;
  }
  // 이미지/문서/기타 파일 처리
  if (!window.audioFileData) window.audioFileData = { data: {} };
  const dataDict = window.audioFileData;
  const newId = 'f' + Date.now() + '_' + Math.floor(Math.random()*10000);
  const order = Object.keys(dataDict.data).length;
  let type = 'file';
  if (file.type.startsWith('image/')) type = 'img';

  // S3 업로드: 서버에 FormData로 업로드 요청
  const formData = new FormData();
  formData.append('row_id', window.currentDetailRowId);
  formData.append('file', file);

  fetch('/sales/upload_note_file/', {
    method: 'POST',
    body: formData
  })
  .then(r => r.json())
  .then(data => {
    if (data.success && data.file_info) {
      dataDict.data[newId] = {
        id: newId,
        type,
        filename: data.file_info.original_filename,
        order,
        url: data.file_info.preview_url || data.file_info.download_url || '',
        download_url: data.file_info.download_url || '',
        preview_url: data.file_info.preview_url || '',
        file_size: data.file_info.file_size,
        content_type: data.file_info.content_type
      };
      
      // 성공 알림
      showNotification('파일이 업로드되었습니다.', 'success');
      
      // 영업노트 섹션 비동기 리렌더링
      refreshSalesNoteSection();
    } else {
      alert('파일 업로드 실패: ' + (data.error || ''));
    }
  })
  .catch(err => {
    alert('파일 업로드 중 오류: ' + err);
  });
}

// 노트 셀(파일/이미지/텍스트 등) 삭제 함수
function deleteNoteCell(cellId) {
  if (!window.audioFileData || !window.audioFileData.data[cellId]) return;
  delete window.audioFileData.data[cellId];
  
  // 성공 알림
  showNotification('항목이 삭제되었습니다.', 'success');
  
  // 영업노트 섹션 비동기 리렌더링
  refreshSalesNoteSection();
}

// 이미지 파일 요소 생성 함수
function createImageFileElement(fileData, index) {
  const { fileId, fileInfo } = fileData;
  
  const imageElement = document.createElement('div');
  imageElement.className = 'image-file-item';
  imageElement.style.cssText = `
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 15px;
      background: #f9f9f9;
      cursor: move;
      transition: all 0.2s ease;
      margin-bottom: 10px;
  `;
  imageElement.setAttribute('data-file-id', fileId);
  imageElement.setAttribute('data-type', 'image');
  imageElement.setAttribute('data-order', fileInfo.order || 0);
  
  // 호버 효과
  imageElement.onmouseenter = () => imageElement.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
  imageElement.onmouseleave = () => imageElement.style.boxShadow = 'none';
  
  // 먼저 기본 구조 생성 (이미지 URL은 나중에 설정)
  imageElement.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
          <div style="flex: 1;">
              <div style="font-weight: bold; color: #333; margin-bottom: 8px;">
                  🖼️ ${fileInfo.original_filename || fileInfo.filename}
              </div>
              <div style="font-size: 12px; color: #666; margin-bottom: 10px;">
                  크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB
              </div>
              
              <!-- 이미지 썸네일 영역 -->
              <div style="position: relative; display: inline-block; cursor: pointer;" onclick="showImagePreview('${fileId}', '${fileInfo.original_filename || fileInfo.filename}')">
                  <div id="image-thumbnail-${fileId}" style="width: 250px; height: 200px; border-radius: 6px; border: 1px solid #ddd; background: #f8f9fa; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;">
                      <div style="text-align: center; color: #6c757d;">
                          <div style="font-size: 24px; margin-bottom: 8px;">⏳</div>
                          <div style="font-size: 12px;">이미지 로딩 중...</div>
                      </div>
                  </div>
              </div>
              <div style="font-size: 11px; color: #888; margin-top: 5px; font-style: italic;">
                  이미지를 클릭하면 확대해서 볼 수 있습니다
              </div>
          </div>
          
          <div style="gap: 5px; margin-left: 15px;">
              <button onclick="showFilePreview('${fileId}', ${JSON.stringify(fileInfo).replace(/\"/g, '&quot;')})" 
                      style="padding: 6px 12px; background: #ffc107; color: #333; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
                  미리보기
              </button>
              <a href="${fileInfo.download_url}" download="${fileInfo.original_filename || fileInfo.filename}" 
                 style="padding: 6px 12px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; display: inline-block; text-align: center;">
                  다운로드
              </a>
              <button onclick="deleteAudioFileItem('${fileId}', '${fileInfo.original_filename || fileInfo.filename}')" 
                      style="padding: 6px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                  삭제
              </button>
          </div>
      </div>
  `;
  
  // 이미지 URL 요청 및 썸네일 설정
  loadImageThumbnail(fileId, fileInfo);
  
  return imageElement;
}

// 이미지 썸네일 로드 함수
function loadImageThumbnail(fileId, fileInfo) {
    // 서버에서 새로운 서명된 URL 요청
    fetch(`/sales/get_file_preview_url_note/${fileId}/?row_id=${window.currentDetailRowId}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        const thumbnailContainer = document.getElementById(`image-thumbnail-${fileId}`);
        if (!thumbnailContainer) return;
        
        if (data.success && data.preview_url) {
            // 성공적으로 URL을 받았으면 이미지 표시
            thumbnailContainer.innerHTML = `
                <img src="${data.preview_url}" 
                     alt="${fileInfo.original_filename || fileInfo.filename}"
                     style="max-width: 250px; max-height: 200px; border-radius: 6px; object-fit: cover; transition: all 0.2s ease;"
                     onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgZmlsbD0iIzZjNzU3ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlPC90ZXh0Pjwvc3ZnPg==';"
                     onmouseenter="this.style.transform='scale(1.05)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.2)';"
                     onmouseleave="this.style.transform='scale(1)'; this.style.boxShadow='none';">
            `;
        } else {
            // URL을 받지 못했으면 에러 상태 표시
            thumbnailContainer.innerHTML = `
                <div style="text-align: center; color: #dc3545;">
                    <div style="font-size: 24px; margin-bottom: 8px;">❌</div>
                    <div style="font-size: 12px;">이미지 로드 실패</div>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('이미지 썸네일 로드 실패:', error);
        const thumbnailContainer = document.getElementById(`image-thumbnail-${fileId}`);
        if (thumbnailContainer) {
            thumbnailContainer.innerHTML = `
                <div style="text-align: center; color: #dc3545;">
                    <div style="font-size: 24px; margin-bottom: 8px;">❌</div>
                    <div style="font-size: 12px;">이미지 로드 실패</div>
                </div>
            `;
        }
    });
}

// 이미지 확대 보기 함수 (썸네일 클릭 시)
function showImagePreview(fileId, filename) {
    // 기존 모달이 있으면 제거
    const existingModal = document.getElementById('imagePreviewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 생성
    const modal = document.createElement('div');
    modal.id = 'imagePreviewModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        cursor: pointer;
    `;
    
    // 로딩 상태 표시
    modal.innerHTML = `
        <div style="position: relative; max-width: 90%; max-height: 90%; text-align: center;">
            <div style="color: white; margin-bottom: 20px;">
                <div style="font-size: 48px; margin-bottom: 10px;">⏳</div>
                <div style="font-size: 16px;">이미지를 로딩 중...</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 새로운 서명된 URL 요청
    fetch(`/sales/get_file_preview_url_note/${fileId}/?row_id=${window.currentDetailRowId}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.preview_url) {
            // 성공적으로 URL을 받았으면 이미지 표시
            modal.innerHTML = `
                <div style="position: relative; max-width: 90%; max-height: 90%;">
                    <img src="${data.preview_url}" 
                         alt="${filename}"
                         style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px;"
                         onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzZjNzU3ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIGxvYWQgZmFpbGVkPC90ZXh0Pjwvc3ZnPg==';">
                    <button onclick="closeImagePreviewModal()" 
                            style="position: absolute; top: -40px; right: 0; background: #dc3545; color: white; border: none; border-radius: 4px; padding: 8px 12px; cursor: pointer; font-size: 14px;">
                        닫기
                    </button>
                </div>
            `;
        } else {
            // URL을 받지 못했으면 에러 상태 표시
            modal.innerHTML = `
                <div style="position: relative; max-width: 90%; max-height: 90%; text-align: center;">
                    <div style="color: white; margin-bottom: 20px;">
                        <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
                        <div style="font-size: 18px; margin-bottom: 10px;">이미지 로드 실패</div>
                        <div style="font-size: 14px; color: #ccc;">${data.error || '이미지를 불러올 수 없습니다.'}</div>
                    </div>
                    <button onclick="closeImagePreviewModal()" 
                            style="background: #dc3545; color: white; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer; font-size: 14px;">
                        닫기
                    </button>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('이미지 미리보기 로드 실패:', error);
        modal.innerHTML = `
            <div style="position: relative; max-width: 90%; max-height: 90%; text-align: center;">
                <div style="color: white; margin-bottom: 20px;">
                    <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
                    <div style="font-size: 18px; margin-bottom: 10px;">이미지 로드 실패</div>
                    <div style="font-size: 14px; color: #ccc;">네트워크 오류가 발생했습니다.</div>
                </div>
                <button onclick="closeImagePreviewModal()" 
                        style="background: #dc3545; color: white; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer; font-size: 14px;">
                    닫기
                </button>
            </div>
        `;
    });
    
    // 모달 외부 클릭시 닫기
    modal.onclick = function(e) {
        if (e.target === modal) {
            closeImagePreviewModal();
        }
    };
}

// 이미지 미리보기 모달 닫기 함수
function closeImagePreviewModal() {
    const modal = document.getElementById('imagePreviewModal');
    if (modal) {
        modal.remove();
    }
}

// 문서 파일 요소 생성 함수
function createDocumentFileElement(fileData, index) {
  const { fileId, fileInfo } = fileData;
  
  const fileElement = document.createElement('div');
  fileElement.className = 'document-file-item';
  fileElement.style.cssText = `
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 15px;
      background: #f9f9f9;
      cursor: move;
      transition: all 0.2s ease;
      margin-bottom: 10px;
  `;
  fileElement.setAttribute('data-file-id', fileId);
  fileElement.setAttribute('data-type', 'file');
  fileElement.setAttribute('data-order', fileInfo.order || 0);
  
  // 호버 효과
  fileElement.onmouseenter = () => fileElement.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
  fileElement.onmouseleave = () => fileElement.style.boxShadow = 'none';
  
  // 파일 타입별 아이콘 결정
  let fileIcon = '📄';
  if (fileInfo.content_type) {
      if (fileInfo.content_type.includes('pdf')) {
          fileIcon = '📕';
      } else if (fileInfo.content_type.includes('word') || fileInfo.content_type.includes('docx')) {
          fileIcon = '📘';
      } else if (fileInfo.content_type.includes('excel') || fileInfo.content_type.includes('xlsx')) {
          fileIcon = '📗';
      } else if (fileInfo.content_type.includes('powerpoint') || fileInfo.content_type.includes('pptx')) {
          fileIcon = '��';
      }
  }
  
  // 미리보기, 다운로드, 삭제 버튼 컨테이너 생성
  const buttonContainer = document.createElement('div');
  buttonContainer.style.display = 'flex';
  buttonContainer.style.gap = '5px';
  buttonContainer.style.marginLeft = '15px';

  // 미리보기 버튼
  const previewBtn = document.createElement('button');
  previewBtn.textContent = '미리보기';
  previewBtn.style.cssText = 'padding: 6px 12px; background: #ffc107; color: #333; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;';
  previewBtn.onclick = function(e) {
    e.stopPropagation();
    showFilePreview(fileId, fileInfo);
  };

  // 다운로드 버튼
  const downloadBtn = document.createElement('a');
  downloadBtn.textContent = '다운로드';
  downloadBtn.href = fileInfo.download_url;
  downloadBtn.download = fileInfo.original_filename || fileInfo.filename;
  downloadBtn.style.cssText = 'padding: 6px 12px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; display: inline-block;';

  // 삭제 버튼
  const deleteBtn = document.createElement('button');
  deleteBtn.textContent = '삭제';
  deleteBtn.style.cssText = 'padding: 6px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;';
  deleteBtn.onclick = function(e) {
    e.stopPropagation();
    deleteAudioFileItem(fileId, fileInfo.original_filename || fileInfo.filename);
  };

  buttonContainer.appendChild(previewBtn);
  buttonContainer.appendChild(downloadBtn);
  buttonContainer.appendChild(deleteBtn);

  // 파일 정보 영역 생성
  const infoDiv = document.createElement('div');
  infoDiv.style.flex = '1';
  infoDiv.innerHTML = `
      <div style="font-weight: bold; color: #333; margin-bottom: 4px;">
          ${fileIcon} ${fileInfo.original_filename || fileInfo.filename}
      </div>
      <div style="font-size: 12px; color: #666;">
          크기: ${(fileInfo.file_size / 1024 / 1024).toFixed(2)}MB
      </div>
  `;

  // 전체 레이아웃
  const rowDiv = document.createElement('div');
  rowDiv.style.display = 'flex';
  rowDiv.style.justifyContent = 'space-between';
  rowDiv.style.alignItems = 'center';
  rowDiv.style.marginBottom = '10px';
  rowDiv.appendChild(infoDiv);
  rowDiv.appendChild(buttonContainer);

  fileElement.appendChild(rowDiv);
  return fileElement;
}

// 오디오 파일 업로드 처리 함수
function handleAudioFileUpload(file, insertIndex) {
    const formData = new FormData();
    formData.append('audio_file', file);
    formData.append('row_id', window.currentDetailRowId);
    
    fetch('/sales/upload_audio_file/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('오디오 파일 업로드 성공');
            
            // 성공 알림
            showNotification('오디오 파일이 업로드되었습니다.', 'success');
            
            // 영업노트 섹션 비동기 리렌더링
            refreshSalesNoteSection();
            
        } else {
            console.error('오디오 파일 업로드 실패:', data.error);
            alert('오디오 파일 업로드 실패: ' + (data.error || ''));
        }
    })
    .catch(error => {
        console.error('오디오 파일 업로드 중 오류:', error);
        alert('오디오 파일 업로드 중 오류가 발생했습니다.');
    });
}

// 일반 파일 업로드 처리 함수
function handleGeneralFileUpload(file, insertIndex) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('row_id', window.currentDetailRowId);
    
    fetch('/sales/upload_note_file/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.file_info) {
            console.log('일반 파일 업로드 성공');
            
            // 성공 알림
            showNotification('파일이 업로드되었습니다.', 'success');
            
            // 영업노트 섹션 비동기 리렌더링
            refreshSalesNoteSection();
            
        } else {
            console.error('일반 파일 업로드 실패:', data.error);
            alert('파일 업로드 실패: ' + (data.error || ''));
        }
    })
    .catch(error => {
        console.error('일반 파일 업로드 중 오류:', error);
        alert('파일 업로드 중 오류가 발생했습니다.');
    });
}

function insertTextNoteAtIndex(index) {
    // 1. 현재 모든 아이템 수집
    const sortableContainer = document.getElementById('sortableAudioContainer');
    if (!sortableContainer) return;
    const actualItems = sortableContainer.querySelectorAll('.audio-file-item, .image-file-item, .document-file-item, .text-note-item');
    const allItems = [];

    // 2. index 이전 아이템들 추가
    for (let i = 0; i < index; i++) {
        const item = actualItems[i];
        if (!item) continue;
        if (item.classList.contains('audio-file-item') || item.classList.contains('image-file-item') || item.classList.contains('document-file-item')) {
            const fileInfo = getFileInfoFromDOM(item);
            allItems.push({
                ...fileInfo,
                id: item.getAttribute('data-file-id'),
                order: i,
                type: fileInfo.type || item.dataset.type || 'file'
            });
        } else if (item.classList.contains('text-note-item')) {
            const noteId = item.dataset.noteId;
            const textarea = item.querySelector('textarea');
            allItems.push({
                id: noteId,
                text: textarea ? textarea.value : '',
                order: i,
                type: 'text',
                upload_date: getTodayStr()
            });
        }
    }

    // 3. 새 텍스트 노트 추가
    const noteId = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
    allItems.push({
        id: noteId,
        text: '',
        order: index,
        type: 'text',
        upload_date: getTodayStr()
    });

    // 4. index 이후 아이템들 추가 (order + 1)
    for (let i = index; i < actualItems.length; i++) {
        const item = actualItems[i];
        if (!item) continue;
        if (item.classList.contains('audio-file-item') || item.classList.contains('image-file-item') || item.classList.contains('document-file-item')) {
            const fileInfo = getFileInfoFromDOM(item);
            allItems.push({
                ...fileInfo,
                id: item.getAttribute('data-file-id'),
                order: i + 1,
                type: fileInfo.type || item.dataset.type || 'file'
            });
        } else if (item.classList.contains('text-note-item')) {
            const noteId2 = item.dataset.noteId;
            const textarea = item.querySelector('textarea');
            allItems.push({
                id: noteId2,
                text: textarea ? textarea.value : '',
                order: i + 1,
                type: 'text',
                upload_date: getTodayStr()
            });
        }
    }

    // 5. 서버에 전체 데이터 저장
    fetch('/sales/update_audio_file_order_and_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&notes=${encodeURIComponent(JSON.stringify(allItems))}`
    }).then(r=>r.json()).then(data=>{
        if(data.success) {
            // 서버 저장 성공 후 전체 데이터 새로고침
            refreshAudioFileData();
        } else {
            alert('텍스트 노트 추가 실패: '+(data.error||''));
        }
    }).catch(error => {
        alert('텍스트 노트 추가 중 오류가 발생했습니다.');
    });
}
window.insertTextNoteAtIndex = insertTextNoteAtIndex;

function getFileInfoFromDOM(item) {
    const fileId = item.getAttribute('data-file-id');
    let fileInfo = {};
    if (window.audioFileData && window.audioFileData.data && window.audioFileData.data[fileId]) {
        fileInfo = window.audioFileData.data[fileId];
    }
    // DOM에서 보완 (예시: 파일명)
    if (!fileInfo.original_filename) {
        const nameEl = item.querySelector('.file-name');
        if (nameEl) fileInfo.original_filename = nameEl.textContent.trim();
    }
    // 필요시 download_url, s3_key 등도 보완
    return fileInfo;
}

// 셀 사이에 hover 시만 보이는 텍스트/파일 추가 placeholder 생성 함수
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
    // 내부 버튼 컨테이너
    const btnContainer = document.createElement('div');
    btnContainer.style.cssText = `
        display: none;
        height: 60px;
        border: 1px dashed #bbb;
        border-radius: 10px;
        padding: 8px;
        font-size: 13px;
        color: #888;
        transition: all 0.2s;
        pointer-events: none;
        user-select: none;
        width: 100%;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 8px;
    `;
    // 텍스트 추가 버튼
    const textBtn = document.createElement('div');
    textBtn.textContent = '📝 텍스트 추가';
    textBtn.style.cssText = `
        padding: 6px 12px;
        background: #bfcfc2;
        color: #222;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s;
        pointer-events: auto;
        text-align: center;
        width: 100%;
    `;
    // 파일 추가 버튼
    const fileBtn = document.createElement('div');
    fileBtn.textContent = '📎 파일 추가';
    fileBtn.style.cssText = `
        padding: 6px 12px;
        background: #22b573;
        color: #fff;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s;
        pointer-events: auto;
        text-align: center;
        width: 100%;
    `;
    // 호버 효과
    textBtn.onmouseenter = () => {
        textBtn.style.background = '#a8c2ae';
        textBtn.style.transform = 'scale(1.02)';
    };
    textBtn.onmouseleave = () => {
        textBtn.style.background = '#bfcfc2';
        textBtn.style.transform = 'scale(1)';
    };
    fileBtn.onmouseenter = () => {
        fileBtn.style.background = '#1ea366';
        fileBtn.style.transform = 'scale(1.02)';
    };
    fileBtn.onmouseleave = () => {
        fileBtn.style.background = '#22b573';
        fileBtn.style.transform = 'scale(1)';
    };
    // 클릭 이벤트
    textBtn.onclick = function(e) {
        e.stopPropagation();
        window.insertTextNoteAtIndex(insertIndex);
    };
    fileBtn.onclick = function(e) {
        e.stopPropagation();
        addFileCell();
    };
    btnContainer.appendChild(textBtn);
    btnContainer.appendChild(fileBtn);
    placeholder.appendChild(btnContainer);
    // hover 시만 보이게
    placeholder.onmouseenter = () => { 
        placeholder.style.height = '80px';
        placeholder.style.marginTop = '5px';
        placeholder.style.marginBottom = '15px';
        btnContainer.style.display = 'flex';
    };
    placeholder.onmouseleave = () => { 
        placeholder.style.height = '10px';
        placeholder.style.marginTop = '0px';
        placeholder.style.marginBottom = '0px';
        btnContainer.style.display = 'none';
    };
    // 항상 비어있을 때도 placeholder가 하나는 남도록 보장 (렌더링 로직에서 체크 필요)
    return placeholder;
}

// 오늘 날짜를 YY.MM.DD 형식으로 반환하는 함수
function getTodayStr() {
    const d = new Date();
    return d.toISOString().slice(2, 10).replace(/-/g, '.');
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
  // text 값이 undefined나 null인 경우 빈 문자열로 처리
  const safeText = text || '';
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
                    style="width: 100%; min-height: 50px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; line-height: 1.5; resize: none; box-sizing: border-box; overflow: hidden;"
                    placeholder="텍스트 노트를 입력하세요...">${safeText}</textarea>
      </div>
  `;
  
  // textarea 입력시 저장 및 자동 높이 조절
  const textarea = textElement.querySelector(`#text-note-${noteId}`);
  
  if (textarea) {
      // 자동 높이 조절 함수
      function adjustHeight() {
          textarea.style.height = 'auto';
          textarea.style.height = textarea.scrollHeight + 'px';
      }
      
      // 디바운스된 저장 함수 (중복 저장 방지)
      let saveTimeout;
      textarea.addEventListener('input', function() {
          // 자동 높이 조절
          adjustHeight();
          
          // 저장
          clearTimeout(saveTimeout);
          saveTimeout = setTimeout(() => {
              console.log('텍스트 입력 감지:', this.value);
              saveTextNotesToServer();
          }, 500); // 0.5초 후 저장
      });
      
      // 초기 높이 설정
      setTimeout(() => {
          adjustHeight();
      }, 100);
  } else {
      console.error('textarea를 찾을 수 없음:', noteId);
  }
  
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
            if (!textarea) {
                console.warn('textarea를 찾을 수 없음:', el);
                return;
            }
            
            let id = el.dataset.noteId;
            if (!id) {
                id = 't' + Date.now() + '_' + Math.floor(Math.random()*10000);
                el.dataset.noteId = id;
            }
            const adjustedIndex = idx > targetIndex ? idx - 1 : idx;
            
            // 텍스트 값이 undefined나 null인 경우 빈 문자열로 처리
            const textValue = textarea.value || '';
            
            remainingNotes.push({ 
                id, 
                text: textValue, 
                order: adjustedIndex,
                type: 'text',
                upload_date: getTodayStr()
            });
        }
    });
    console.log('삭제 후 남을 노트들:', remainingNotes);
    
    // 서버에 업데이트된 노트 목록 저장
    fetch('/sales/update_audio_text_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&date=${encodeURIComponent('data')}&notes=${encodeURIComponent(JSON.stringify(remainingNotes))}`
    }).then(r=>r.json()).then(data=>{
        if(data.success) {
            console.log('텍스트 노트 삭제 성공');
            // 삭제된 요소 제거
            noteElement.remove();
        } else {
            console.error('텍스트 노트 삭제 실패:', data.error);
            alert('텍스트 노트 삭제 실패: '+(data.error||''));
        }
    }).catch(error => {
        console.error('텍스트 노트 삭제 중 오류:', error);
        alert('텍스트 노트 삭제 중 오류가 발생했습니다.');
    });
}

// saveAllOrderToServer 함수
function saveAllOrderToServer() {
    const sortableContainer = document.getElementById('sortableAudioContainer');
    if (!sortableContainer) return;
    
    const actualItems = sortableContainer.querySelectorAll('.audio-file-item, .image-file-item, .document-file-item, .text-note-item');
    const allItems = [];
    
    actualItems.forEach((item, index) => {
        if (item.classList.contains('audio-file-item') || item.classList.contains('image-file-item') || item.classList.contains('document-file-item')) {
            const fileId = item.getAttribute('data-file-id');
            let fileInfo = {};
            if (window.audioFileData && window.audioFileData.data && window.audioFileData.data[fileId]) {
                fileInfo = window.audioFileData.data[fileId];
            }
            allItems.push({
                ...fileInfo,
                id: fileId,
                order: index,
                type: fileInfo.type || item.dataset.type || 'file'
            });
        } else if (item.classList.contains('text-note-item')) {
            const noteId = item.dataset.noteId;
            const textarea = item.querySelector('textarea');
            const textValue = textarea ? textarea.value : '';
            
            // 기존 텍스트 노트 정보 가져오기
            let textInfo = {};
            if (window.audioFileData && window.audioFileData.data && window.audioFileData.data[noteId]) {
                textInfo = window.audioFileData.data[noteId];
            }
            allItems.push({ 
                ...textInfo,
                id: noteId, 
                text: textValue, 
                order: index, 
                type: 'text', 
                upload_date: textInfo.upload_date || getTodayStr() 
            });
        }
    });
    
    console.log('서버에 저장할 모든 아이템:', allItems);
    
    fetch('/sales/update_audio_file_order_and_notes/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `row_id=${encodeURIComponent(window.currentDetailRowId)}&notes=${encodeURIComponent(JSON.stringify(allItems))}`
    }).then(r => r.json()).then(data => {
        if (data.success) {
            console.log('순서 저장 성공');
        } else {
            console.error('순서 저장 실패:', data.error);
        }
    }).catch(error => {
        console.error('순서 저장 중 오류:', error);
    });
}

// 파일 미리보기 함수
function showFilePreview(fileId, fileInfo) {
    console.log('showFilePreview 호출됨:', fileId, fileInfo);
    
    // 기존 미리보기 모달이 있으면 제거
    const existingModal = document.getElementById('filePreviewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 생성
    const modal = document.createElement('div');
    modal.id = 'filePreviewModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    const fileName = fileInfo.original_filename || fileInfo.filename || 'Unknown';
    const contentType = fileInfo.content_type || '';
    const fileExt = fileName.split('.').pop()?.toLowerCase() || '';
    
    // 로딩 상태 표시
    modal.innerHTML = `
        <div style="position: relative; width: 90%; height: 90%; background: white; border-radius: 8px; overflow: hidden;">
            <!-- 헤더 -->
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 60px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 10;">
                <div style="font-size: 16px; font-weight: bold; color: #333;">${fileName}</div>
                <button onclick="closeFilePreviewModal()" 
                        style="background: #dc3545; color: white; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer; font-size: 14px;">
                    닫기
                </button>
            </div>
            
            <!-- 로딩 콘텐츠 -->
            <div style="position: absolute; top: 60px; left: 0; right: 0; bottom: 0; padding: 20px; display: flex; align-items: center; justify-content: center;">
                <div style="text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 20px;">⏳</div>
                    <div style="font-size: 16px; color: #666;">미리보기를 로딩 중...</div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 새로운 S3 서명된 URL 요청
    fetch(`/sales/get_file_preview_url_note/${fileId}/?row_id=${window.currentDetailRowId}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.preview_url) {
            const fileUrl = data.preview_url;
            let previewContent = '';
            
            // 파일 타입에 따른 미리보기 생성
            if (contentType.startsWith('image/') || fileInfo.type === 'img') {
                // 이미지 파일
                previewContent = `
                    <img src="${fileUrl}" 
                         alt="${fileName}"
                         style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px;"
                         onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzZjNzU3ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIGxvYWQgZmFpbGVkPC90ZXh0Pjwvc3ZnPg==';">
                `;
            } else if (contentType === 'application/pdf' || fileExt === 'pdf' || fileInfo.type === 'pdf') {
                // PDF 파일
                previewContent = `
                    <iframe src="${fileUrl}" 
                            style="width: 100%; height: 100%; border: none; border-radius: 8px;"
                            title="${fileName}">
                    </iframe>
                `;
            } else if (contentType.includes('text/') || contentType.includes('application/json') || contentType.includes('application/xml')) {
                // 텍스트 파일
                previewContent = `
                    <iframe src="${fileUrl}" 
                            style="width: 100%; height: 100%; border: none; border-radius: 8px;"
                            title="${fileName}">
                    </iframe>
                `;
            } else if (contentType.includes('video/')) {
                // 비디오 파일
                previewContent = `
                    <video controls style="max-width: 100%; max-height: 100%; border-radius: 8px;">
                        <source src="${fileUrl}" type="${contentType}">
                        Your browser does not support the video tag.
                    </video>
                `;
            } else if (contentType.includes('audio/')) {
                // 오디오 파일
                previewContent = `
                    <div style="text-align: center; background: #f8f9fa; padding: 40px; border-radius: 8px;">
                        <div style="font-size: 48px; margin-bottom: 20px;">🎵</div>
                        <div style="font-size: 18px; margin-bottom: 20px; color: #333;">${fileName}</div>
                        <audio controls style="width: 100%; max-width: 400px;">
                            <source src="${fileUrl}" type="${contentType}">
                            Your browser does not support the audio tag.
                        </audio>
                    </div>
                `;
            } else if (['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'].includes(fileExt) || 
                       contentType.includes('wordprocessingml') || 
                       contentType.includes('presentationml') || 
                       contentType.includes('spreadsheetml') ||
                       contentType.includes('msword')) {
                // Office 문서 파일들 - Google Docs Viewer 사용
                const encodedUrl = encodeURIComponent(fileUrl);
                previewContent = `
                    <div style="width: 100%; height: 100%; display: flex; flex-direction: column;">
                        <iframe src="https://docs.google.com/viewer?url=${encodedUrl}&embedded=true"
                                style="flex: 1; border: none; border-radius: 8px;"
                                title="${fileName}">
                        </iframe>
                        <div style="text-align: center; margin-top: 15px; padding: 10px;">
                            <button onclick="window.open('${fileUrl}', '_blank')" 
                                    style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px;">
                                새 창에서 열기
                            </button>
                            <button onclick="window.open('${fileInfo.download_url || fileUrl}', '_blank')" 
                                    style="padding: 8px 16px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                다운로드
                            </button>
                        </div>
                    </div>
                `;
            } else {
                // 지원하지 않는 파일 타입
                previewContent = `
                    <div style="text-align: center; background: #f8f9fa; padding: 40px; border-radius: 8px;">
                        <div style="font-size: 48px; margin-bottom: 20px;">📄</div>
                        <div style="font-size: 18px; margin-bottom: 20px; color: #333;">${fileName}</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            이 파일 타입은 미리보기를 지원하지 않습니다.
                        </div>
                        <button onclick="window.open('${fileUrl}', '_blank')" 
                                style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; font-weight: 500; margin-right: 10px; cursor: pointer;">
                            새 창에서 열기
                        </button>
                        <button onclick="window.open('${fileInfo.download_url || fileUrl}', '_blank')" 
                                style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; font-weight: 500; cursor: pointer;">
                            다운로드
                        </button>
                    </div>
                `;
            }
            
            // 미리보기 콘텐츠 업데이트
            const contentDiv = modal.querySelector('div[style*="position: absolute; top: 60px"]');
            if (contentDiv) {
                contentDiv.innerHTML = previewContent;
            }
        } else {
            // 파일 경로를 가져오지 못한 경우
            const contentDiv = modal.querySelector('div[style*="position: absolute; top: 60px"]');
            if (contentDiv) {
                contentDiv.innerHTML = `
                    <div style="text-align: center; background: #f8f9fa; padding: 40px; border-radius: 8px;">
                        <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                        <div style="font-size: 18px; margin-bottom: 20px; color: #333;">미리보기 로드 실패</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            ${data.error || '파일을 불러올 수 없습니다.'}
                        </div>
                        <button onclick="window.open('${fileInfo.preview_url || fileInfo.download_url}', '_blank')" 
                                style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; font-weight: 500; cursor: pointer;">
                            새 창에서 열기
                        </button>
                    </div>
                `;
            }
        }
    })
    .catch(error => {
        console.error('파일 미리보기 URL 가져오기 실패:', error);
        // 에러 발생 시 기본 URL 사용
        const contentDiv = modal.querySelector('div[style*="position: absolute; top: 60px"]');
        if (contentDiv) {
            contentDiv.innerHTML = `
                <div style="text-align: center; background: #f8f9fa; padding: 40px; border-radius: 8px;">
                    <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                    <div style="font-size: 18px; margin-bottom: 20px; color: #333;">미리보기 로드 실패</div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 20px;">
                        파일을 불러올 수 없습니다. 새 창에서 열어주세요.
                    </div>
                    <button onclick="window.open('${fileInfo.preview_url || fileInfo.download_url}', '_blank')" 
                            style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; font-weight: 500; cursor: pointer;">
                        새 창에서 열기
                    </button>
                </div>
            `;
        }
    });
    
    // 모달 외부 클릭시 닫기
    modal.onclick = function(e) {
        if (e.target === modal) {
            closeFilePreviewModal();
        }
    };
}

// 파일 미리보기 모달 닫기 함수
function closeFilePreviewModal() {
    const modal = document.getElementById('filePreviewModal');
    if (modal) {
        modal.remove();
    }
}

// 드래그 앤 드롭 설정 함수
function setupDragAndDrop(container) {
    if (!container) return;
    
    // 드래그 오버 이벤트
    container.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.border = '2px dashed #22b573';
        this.style.backgroundColor = '#f0f8f0';
    });
    
    // 드래그 리브 이벤트
    container.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.border = '';
        this.style.backgroundColor = '';
    });
    
    // 드롭 이벤트
    container.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.border = '';
        this.style.backgroundColor = '';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            console.log('드래그 앤 드롭으로 파일 받음:', files);
            handleDroppedFiles(files);
        }
    });
    
    // 클립보드 붙여넣기 이벤트 추가
    container.addEventListener('paste', function(e) {
        // 현재 활성화된 요소가 입력 필드인 경우는 무시
        const activeElement = document.activeElement;
        if (activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' || 
            activeElement.contentEditable === 'true' ||
            activeElement.isContentEditable ||
            activeElement.type === 'text' ||
            activeElement.type === 'search' ||
            activeElement.type === 'email' ||
            activeElement.type === 'password' ||
            activeElement.type === 'url' ||
            activeElement.type === 'tel'
        )) {
            // 입력 필드에서는 기본 동작 허용 (텍스트 붙여넣기 등)
            return;
        }
        
        // 입력 필드가 아닌 경우에만 이벤트 차단
        e.preventDefault();
        e.stopPropagation();
        
        const items = e.clipboardData.items;
        if (!items) return;
        
        // 파일이 있는지 확인
        let hasFiles = false;
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file') {
                hasFiles = true;
                break;
            }
        }
        
        // 파일이 없으면 기본 동작 허용 (텍스트 붙여넣기 등)
        if (!hasFiles) {
            return;
        }
        
        const files = [];
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file') {
                const file = item.getAsFile();
                if (file) {
                    files.push(file);
                }
            }
        }
        
        if (files.length > 0) {
            console.log('클립보드에서 파일 붙여넣기:', files);
            handleDroppedFiles(files);
        }
    });
    
    // 키보드 이벤트 (Ctrl+V) 제거 - 전역 리스너에서 처리
}

// 드롭된 파일 처리 함수
function handleDroppedFiles(files) {
    console.log('드롭된 파일들 처리 시작:', files);
    
    // 파일 개수 제한 (최대 10개)
    if (files.length > 10) {
        showNotification('최대 10개까지 파일을 업로드할 수 있습니다.', 'warning');
        return;
    }
    
    let uploadedCount = 0;
    let errorCount = 0;
    
    Array.from(files).forEach((file, index) => {
        // 파일 크기 제한 (100MB)
        if (file.size > 100 * 1024 * 1024) {
            showNotification(`${file.name}은(는) 100MB를 초과하여 업로드할 수 없습니다.`, 'error');
            errorCount++;
            return;
        }
        
        // 파일 타입 확인
        if (file.type.startsWith('audio/')) {
            // 오디오 파일 처리
            handleAudioFileUpload(file, 0);
            uploadedCount++;
        } else {
            // 일반 파일 처리
            handleGeneralFileUpload(file, 0);
            uploadedCount++;
        }
    });
    
    if (uploadedCount > 0) {
        showNotification(`${uploadedCount}개 파일이 업로드되었습니다.`, 'success');
    }
    
    if (errorCount > 0) {
        showNotification(`${errorCount}개 파일 업로드에 실패했습니다.`, 'error');
    }
}



// 전역 클립보드 이벤트 리스너 설정
function setupGlobalClipboardListener() {
    // 이미 설정되어 있는지 확인
    if (window.globalClipboardListenerSet) return;
    
    document.addEventListener('paste', function(e) {
        // 현재 활성화된 요소가 입력 필드인 경우는 완전히 무시
        const activeElement = document.activeElement;
        if (activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' || 
            activeElement.contentEditable === 'true' ||
            activeElement.isContentEditable ||
            activeElement.type === 'text' ||
            activeElement.type === 'search' ||
            activeElement.type === 'email' ||
            activeElement.type === 'password' ||
            activeElement.type === 'url' ||
            activeElement.type === 'tel'
        )) {
            // 입력 필드에서는 파일 붙여넣기를 완전히 무시하고 기본 동작 허용
            return;
        }
        
        const items = e.clipboardData.items;
        if (!items) return;
        
        // 파일이 있는지 확인
        let hasFiles = false;
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file') {
                hasFiles = true;
                break;
            }
        }
        
        // 파일이 없으면 기본 동작 허용 (텍스트 붙여넣기 등)
        if (!hasFiles) {
            return;
        }
        
        // 파일이 있는 경우에만 처리
        const files = [];
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file') {
                const file = item.getAsFile();
                if (file) {
                    files.push(file);
                }
            }
        }
        
        if (files.length > 0) {
            console.log('전역 클립보드에서 파일 붙여넣기:', files);
            handleDroppedFiles(files);
        }
    });
    
    // 키보드 이벤트 (Ctrl+V) 추가 - 입력 필드에서는 무시
    document.addEventListener('keydown', function(e) {
        // 현재 활성화된 요소가 입력 필드인 경우는 제외
        const activeElement = document.activeElement;
        if (activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' || 
            activeElement.contentEditable === 'true' ||
            activeElement.isContentEditable ||
            activeElement.type === 'text' ||
            activeElement.type === 'search' ||
            activeElement.type === 'email' ||
            activeElement.type === 'password' ||
            activeElement.type === 'url' ||
            activeElement.type === 'tel'
        )) {
            return;
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
            console.log('전역 Ctrl+V 감지됨');
            // paste 이벤트가 자동으로 발생하므로 추가 처리만
        }
    });
    
    window.globalClipboardListenerSet = true;
}

// 페이지 로드 시 전역 클립보드 리스너 설정
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupGlobalClipboardListener);
} else {
    setupGlobalClipboardListener();
}