// 파일 미리보기 함수
function showFilePreview(fileId, fileInfo, rowId, fieldName) {
    console.log('showFilePreview 호출됨:', fileId, fileInfo);
    
    // rowId와 fieldName이 필수
    if (!rowId) {
        showNotification('행 정보가 올바르지 않습니다.', 'error');
        return;
    }
    if (!fieldName) {
        showNotification('필드 정보가 올바르지 않습니다.', 'error');
        return;
    }
    
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
    
    const fileName = fileInfo.original_filename || fileInfo.filename || fileInfo.stored_filename || 'Unknown';
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
    fetch(`/sales/get_file_preview_url/${rowId}/${fieldName}/?file_id=${encodeURIComponent(fileId)}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('API 응답:', data); // 디버깅용 로그 추가
        console.log('API 응답 타입:', typeof data); // 타입 확인
        console.log('API 응답이 배열인가:', Array.isArray(data)); // 배열 여부 확인
        console.log('찾고 있는 fileId:', fileId); // 찾고 있는 파일 ID
        
        // data가 리스트인 경우 특정 fileId에 해당하는 파일 찾기
        if (Array.isArray(data)) {
            console.log('배열 길이:', data.length);
            console.log('배열 내용:', data);
            
            // fileId에 해당하는 파일 찾기
            const targetFile = data.find(file => 
                file.id === fileId || 
                file.stored_filename === fileId || 
                file.original_filename === fileId ||
                file.filename === fileId
            );
            
            if (targetFile) {
                console.log('찾은 파일:', targetFile);
                data = targetFile;
            } else {
                console.log('해당 fileId를 찾을 수 없음, 첫 번째 파일 사용');
                if (data.length > 0) {
                    data = data[0];
                } else {
                    throw new Error('파일 정보가 없습니다.');
                }
            }
        }
        
        console.log('처리된 data:', data);
        console.log('data.success:', data.success);
        console.log('data.preview_url:', data.preview_url);
        
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
                let errorMessage = '파일을 불러올 수 없습니다.';
                if (typeof data === 'object' && data.error) {
                    errorMessage = data.error;
                } else if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object' && data[0].error) {
                    errorMessage = data[0].error;
                }
                
                contentDiv.innerHTML = `
                    <div style="text-align: center; background: #f8f9fa; padding: 40px; border-radius: 8px;">
                        <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                        <div style="font-size: 18px; margin-bottom: 20px; color: #333;">미리보기 로드 실패</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            ${errorMessage}
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
  
  // AI 캐시 추적 - 파일 삭제
  if (window.trackFileChange) {
      // AI 캐시 매니저가 초기화되지 않은 경우 초기화
      if (!window.aiCacheManager || window.aiCacheManager.currentRowCache?.rowId !== rowId) {
          console.log('파일 삭제 시 AI 캐시 매니저 초기화:', rowId);
          initializeAICacheManager();
      }
      
      // 삭제할 파일의 정보를 가져오기 위해 DOM에서 파일 정보 찾기
      let fileInfo = null;
      if (fileIndex !== null) {
          // 특정 파일 인덱스의 정보 찾기
          const fileContainer = document.querySelector(`[data-row-id="${rowId}"][data-field-name="${fieldName}"]`);
          if (fileContainer) {
              const fileElements = fileContainer.querySelectorAll('.file-item, [data-file-index]');
              if (fileElements[fileIndex]) {
                  const fileName = fileElements[fileIndex].querySelector('.file-name, span')?.textContent || 'Unknown';
                  fileInfo = {
                      original_filename: fileName,
                      fieldName: fieldName,
                      fileIndex: fileIndex
                  };
              }
          }
      }
      
      window.trackFileChange(rowId, fieldName, 'deleted', fileInfo);
      console.log('AI 캐시에 파일 삭제 추적:', { rowId, fieldName, fileIndex, fileInfo });
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
          if (typeof refreshTable === 'function') {
              refreshTable();
          }
          
          // 상세보기 모달이 열려있으면 모달 전체 새로고침
          const detailModal = document.getElementById('detailModal');
          if (detailModal && detailModal.style.display !== 'none') {
              // 모달 새로고침
              fetch(`/sales/get_row_details/${rowId}/`)
                  .then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          showDetailModal(data.row_data, data.row_id);
                      }
                  })
                  .catch(error => {
                      console.error('모달 새로고침 오류:', error);
                  });
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
          if (typeof refreshTable === 'function') {
              refreshTable();
          }
          
          // 상세보기 모달이 열려있으면 모달 전체 새로고침
          const detailModal = document.getElementById('detailModal');
          if (detailModal && detailModal.style.display !== 'none') {
              // 모달 새로고침
              fetch(`/sales/get_row_details/${rowId}/`)
                  .then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          showDetailModal(data.row_data, data.row_id);
                      }
                  })
                  .catch(error => {
                      console.error('모달 새로고침 오류:', error);
                  });
          }
          
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
                      if (typeof showDetailModal === 'function') {
                          showDetailModal(data.row_data, data.row_id);
                      } else {
                          console.error('showDetailModal 함수가 정의되지 않았습니다.');
                      }
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