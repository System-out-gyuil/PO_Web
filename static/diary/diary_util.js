// 숫자에 콤마 추가하는 함수
function formatNumberWithComma(value) {
    console.log('formatNumberWithComma 호출됨:', value);
    if (!value && value !== 0) return '';
    const num = typeof value === 'string' ? parseInt(value.replace(/[^\d]/g, '')) : value;
    if (isNaN(num)) return '';
    return num.toLocaleString();
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

function updateEntryField(id, field, value) {
  fetch('/sales/update_row_field/', {
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
      return fetch('/sales/update/?id='+id);
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
            fetch(`/sales/get_file_preview_url/${currentRowId}/${fieldName}/`, {
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
                    <div style="font-size: 48px; margin-bottom: 20px;">📊</div>
                    <div style="font-size: 18px; margin-bottom: 20px; color: #333;">엑셀 파일은 미리보기가 불가능 합니다.</div>
                    <button onclick="window.open('${fileInfo.download_url || previewUrl}', '_blank')"
                            style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;">
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