// 파일 미리보기 함수
function showFilePreview(fileId, fileInfo, rowId, fieldName) {
  // fileId가 없거나 숫자가 아니면 fileInfo에서 최대한 추출
  if (!fileId || fileId === 'undefined' || fileId === 'null') {
      fileId = (fileInfo && (fileInfo.id || fileInfo.stored_filename || fileInfo.filename)) || '';
  }
  // rowId도 없으면 fileInfo에서 추출 시도
  if (!rowId && fileInfo && fileInfo.row_id) {
      rowId = fileInfo.row_id;
  }
  if (!fileId) {
      showNotification('파일 정보가 올바르지 않습니다.', 'error');
      return;
  }
  if (!rowId) {
      showNotification('행 정보가 올바르지 않습니다.', 'error');
      return;
  }
  
  const fileName = fileInfo.original_filename || fileInfo.filename || fileInfo.stored_filename || 'Unknown';
  const contentType = fileInfo.content_type || '';
  const fileExt = fileName.split('.').pop()?.toLowerCase() || '';
  
  // 서버에 row_id도 함께 전달
  fetch(`/sales/get_file_preview_url/${fileId}/${fieldName}/?row_id=${rowId}`)
      .then(r => r.json())
      .then(data => {
          if (data.success && data.preview_url) {
              // 파일 타입에 따라 미리보기 모달 표시
              let contentHtml = '';
              const fileUrl = data.preview_url;
              
              if (contentType.startsWith('image/') || fileInfo.type === 'img') {
                  // 이미지 파일
                  contentHtml = `<img src="${fileUrl}" alt="미리보기" style="max-width:100%;max-height:70vh;display:block;margin:0 auto;">`;
              } else if (contentType === 'application/pdf' || fileExt === 'pdf' || fileInfo.type === 'pdf') {
                  // PDF 파일
                  contentHtml = `<iframe src="${fileUrl}" style="width:90vw;height:70vh;border:none;"></iframe>`;
              } else if (contentType.includes('audio/') || fileInfo.type === 'audio') {
                  // 오디오 파일
                  contentHtml = `<audio controls src="${fileUrl}" style="width:100%;"></audio>`;
              } else if (contentType.includes('video/') || fileInfo.type === 'video') {
                  // 비디오 파일
                  contentHtml = `<video controls src="${fileUrl}" style="max-width:100%;max-height:70vh;"></video>`;
              } else if (['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'].includes(fileExt) || 
                         contentType.includes('wordprocessingml') || 
                         contentType.includes('presentationml') || 
                         contentType.includes('spreadsheetml') ||
                         contentType.includes('msword')) {
                  // Office 문서 파일들 - Google Docs Viewer 사용
                  const encodedUrl = encodeURIComponent(fileUrl);
                  contentHtml = `
                      <div style="width: 90vw; height: 70vh; display: flex; flex-direction: column;">
                          <iframe src="https://docs.google.com/viewer?url=${encodedUrl}&embedded=true"
                                  style="flex: 1; border: none;"
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
              } else if (contentType.includes('text/') || contentType.includes('application/json') || contentType.includes('application/xml')) {
                  // 텍스트 파일
                  contentHtml = `<iframe src="${fileUrl}" style="width:90vw;height:70vh;border:none;"></iframe>`;
              } else {
                  // 지원하지 않는 파일 타입
                  contentHtml = `
                      <div style="text-align:center;padding:40px 0;">
                          <div style="font-size:48px;color:#dc3545;">📄</div>
                          <div style="margin-top:16px;font-size:18px;font-weight:500;">${fileName}</div>
                          <div style="margin-top:8px;color:#888;">이 파일 타입은 미리보기를 지원하지 않습니다.</div>
                          <button onclick="window.open('${fileUrl}','_blank')" 
                                  style="margin-top:20px;padding:10px 24px;background:#007bff;color:white;border:none;border-radius:6px;font-size:16px;cursor:pointer;margin-right:10px;">
                              새 창에서 열기
                          </button>
                          <button onclick="window.open('${fileInfo.download_url || fileUrl}','_blank')" 
                                  style="margin-top:20px;padding:10px 24px;background:#28a745;color:white;border:none;border-radius:6px;font-size:16px;cursor:pointer;">
                              다운로드
                          </button>
                      </div>
                  `;
              }
              
              showModal({
                  title: fileName,
                  content: contentHtml
              });
          } else {
              showModal({
                  title: fileName,
                  content: `<div style="text-align:center;padding:40px 0;"><div style="font-size:48px;color:#dc3545;">✗</div><div style="margin-top:16px;font-size:18px;font-weight:500;">미리보기 로드 실패</div><div style="margin-top:8px;color:#888;">${data.error || '파일을 찾을 수 없습니다.'}</div><button onclick="window.open('${fileInfo && fileInfo.download_url ? fileInfo.download_url : '#'}','_blank')" style="margin-top:20px;padding:10px 24px;background:#007bff;color:white;border:none;border-radius:6px;font-size:16px;cursor:pointer;">새 창에서 열기</button></div>`
              });
          }
      })
      .catch(err => {
          showModal({
              title: fileName,
              content: `<div style="text-align:center;padding:40px 0;"><div style="font-size:48px;color:#dc3545;">✗</div><div style="margin-top:16px;font-size:18px;font-weight:500;">미리보기 로드 실패</div><div style="margin-top:8px;color:#888;">${err.message || '알 수 없는 오류'}</div></div>`
          });
      });
}

// 파일 다운로드 함수
function downloadFile(rowId, fieldName) {
  // 직접 다운로드 URL로 이동
  window.open(`/sales/download_file/${rowId}/${fieldName}/`, '_blank');
}

// 파일 삭제 함수
function deleteFile(rowId, fieldName, fileIndex = null) {
  console.log('deleteFile 호출됨:', rowId, fieldName, fileIndex);
  console.log('fileIndex 타입:', typeof fileIndex);
  console.log('fileIndex 값:', fileIndex);
  
  // fileIndex가 문자열로 전달된 경우 숫자로 변환
  if (fileIndex !== null && typeof fileIndex === 'string') {
      fileIndex = parseInt(fileIndex, 10);
      console.log('변환된 fileIndex:', fileIndex);
  }
  
  const confirmMessage = fileIndex !== null 
      ? '이 파일을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.'
      : '모든 파일을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.';
  
  if (!confirm(confirmMessage)) {
      return;
  }
  
  const requestData = {
      row_id: rowId,
      field_name: fieldName
  };
  
  // 특정 파일 인덱스가 제공된 경우 추가
  if (fileIndex !== null) {
      requestData.file_index = fileIndex;
  }
  
  console.log('서버로 전송할 데이터:', requestData);
  
  fetch('/sales/delete_file/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrfToken()
      },
      body: new URLSearchParams(requestData).toString()
  })
  .then(response => response.json())
  .then(data => {
      console.log('파일 삭제 응답:', data);
      
      if (data.success) {
          const message = fileIndex !== null 
              ? '파일이 성공적으로 삭제되었습니다.'
              : '모든 파일이 성공적으로 삭제되었습니다.';
          showNotification(message, 'success');
          
          // 테이블 새로고침
          refreshTable();
          
          // 상세보기 모달이 열려있으면 해당 파일 필드 업데이트
          updateFileFieldInModalAfterDelete(rowId, fieldName);
          
      } else {
          alert('파일 삭제 실패: ' + (data.error || '알 수 없는 오류'));
      }
  })
  .catch(error => {
      console.error('파일 삭제 오류:', error);
      alert('파일 삭제 중 오류가 발생했습니다.');
  });
}

// 파일 업로드 함수 (여러 파일 지원)
function uploadFile(rowId, fieldName, fileInput) {
  console.log('uploadFile 호출됨:', rowId, fieldName, fileInput);
  
  const files = fileInput.files;
  if (!files || files.length === 0) {
      alert('파일을 선택해주세요.');
      return;
  }
  
  // 파일 개수 제한 (최대 10개)
  if (files.length > 10) {
      alert('한 번에 최대 10개 파일까지 업로드할 수 있습니다.');
      return;
  }
  
  // 각 파일에 대해 크기 체크
  for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file.size > 10 * 1024 * 1024) {
          alert(`파일 "${file.name}"의 크기가 10MB를 초과합니다.`);
          return;
      }
  }
  
  console.log('업로드할 파일들:', Array.from(files).map(f => f.name));
  
  // 업로드 진행 상황 표시
  const uploadNotification = document.createElement('div');
  uploadNotification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #007bff;
      color: white;
      padding: 15px 20px;
      border-radius: 6px;
      z-index: 1000;
      font-size: 14px;
  `;
  uploadNotification.textContent = `${files.length}개 파일 업로드 중...`;
  document.body.appendChild(uploadNotification);
  
  // 파일들을 순차적으로 업로드
  let uploadedCount = 0;
  let failedCount = 0;
  
  function uploadNextFile(index) {
      if (index >= files.length) {
          // 모든 파일 업로드 완료
          uploadNotification.remove();
          
          if (failedCount === 0) {
              showNotification(`${uploadedCount}개 파일이 성공적으로 업로드되었습니다.`, 'success');
          } else if (uploadedCount === 0) {
              showNotification('모든 파일 업로드에 실패했습니다.', 'error');
          } else {
              showNotification(`${uploadedCount}개 파일 업로드 성공, ${failedCount}개 파일 업로드 실패`, 'warning');
          }
          
          // 테이블 새로고침
          refreshTable();
          
          // 상세보기 모달이 열려있으면 파일 필드 새로고침
          updateFileFieldInModalAfterUpload(rowId, fieldName);
          
          // 파일 입력 초기화
          fileInput.value = '';
          return;
      }
      
      const file = files[index];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('row_id', rowId);
      formData.append('field_name', fieldName);
      
      // 진행 상황 업데이트
      uploadNotification.textContent = `${index + 1}/${files.length}개 파일 업로드 중... (${file.name})`;
      
      fetch('/sales/upload_file/', {
          method: 'POST',
          body: formData,
          headers: {
              'X-CSRFToken': getCsrfToken()
          }
      })
      .then(response => response.json())
      .then(data => {
          console.log(`파일 "${file.name}" 업로드 응답:`, data);
          
          if (data.success) {
              uploadedCount++;
              console.log(`파일 "${file.name}" 업로드 성공`);
          } else {
              failedCount++;
              console.error(`파일 "${file.name}" 업로드 실패:`, data.error);
          }
      })
      .catch(error => {
          console.error(`파일 "${file.name}" 업로드 오류:`, error);
          failedCount++;
      })
      .finally(() => {
          // 다음 파일 업로드
          uploadNextFile(index + 1);
      });
  }
  
  // 첫 번째 파일부터 업로드 시작
  uploadNextFile(0);
}

// 파일 업로드 처리 함수
function handleFileUpload(rowId, fieldName, fileInput) {
  const file = fileInput.files[0];
  if (!file) {
      return;
  }
  
  console.log('파일 업로드 시작:', file.name, file.size, file.type);
  
  // FormData 생성
  const formData = new FormData();
  formData.append('file', file);
  formData.append('row_id', rowId);
  formData.append('field_name', fieldName);
  
  // 업로드 중 표시
  const uploadingText = '업로드 중...';
  
  // 파일 업로드 요청
  fetch('/sales/upload_file/', {
      method: 'POST',
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      console.log('파일 업로드 응답:', data);
      
      if (data.success) {
          // 업로드 성공 - 상세 모달 새로고침
          alert('파일 업로드 완료!\n파일명: ' + file.name);
          
          // 모달 데이터 새로고침
          fetch('/sales/get_row_details/' + rowId + '/')
              .then(r => r.json())
              .then(function(data) {
                  if (data.success) {
                      showDetailModal(data.row_data, data.row_id);
                  }
              });
          
          // 테이블과 칸반보드도 새로고침
          refreshTable();
          // 칸반보드가 활성화되어 있고 업데이트된 필드가 현재 칸반보드 속성과 일치하는 경우에만 새로고침
          if (window.kanbanAttribute && '지역' === window.kanbanAttribute) {
              refreshKanban();
          }
          
          // 캘린더 업데이트
          refreshCalendar();
      } else {
          alert('파일 업로드 실패: ' + (data.error || '알 수 없는 오류'));
      }
  })
  .catch(error => {
      console.error('파일 업로드 오류:', error);
      alert('파일 업로드 중 오류가 발생했습니다.');
  });
  
  // 파일 입력 초기화
  fileInput.value = '';
}