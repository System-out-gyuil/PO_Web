(function() {
    // ESC 키 이벤트 핸들러 (로컬 스코프)
    let inquiryModalEscapeHandler = null;

    // 문의하기 모달 열기
    window.openInquiryModal = function() {
        const modal = document.getElementById('inquiryModal');
        const textarea = document.getElementById('inquiryContent');
        
        // 모달 표시
        modal.style.display = 'flex';
        
        // 텍스트 영역 초기화
        textarea.value = '';
        document.getElementById('inquiryCharCount').textContent = '0';
        
        // 로딩 상태 초기화
        document.getElementById('inquiryLoading').style.display = 'none';
        document.getElementById('submitInquiryBtn').disabled = false;
        
        // 모달이 완전히 렌더링된 후 포커스 설정
        setTimeout(() => {
            if (textarea) {
                textarea.focus();
                // 커서를 텍스트 영역의 시작 위치로 이동
                textarea.setSelectionRange(0, 0);
                
                // 스크롤을 맨 위로 이동 (모바일에서 유용)
                textarea.scrollTop = 0;
            }
        }, 150);
        
        // ESC 키로 모달 닫기 이벤트 추가
        inquiryModalEscapeHandler = function(e) {
            if (e.key === 'Escape') {
                window.closeInquiryModal();
            }
        };
        document.addEventListener('keydown', inquiryModalEscapeHandler);
    };

    // 문의하기 모달 닫기
    window.closeInquiryModal = function() {
        const modal = document.getElementById('inquiryModal');
        modal.style.display = 'none';
        
        // 포커스를 모달 외부로 이동 (접근성 개선)
        const inquiryBtn = document.querySelector('.inquiry-btn');
        if (inquiryBtn) {
            inquiryBtn.focus();
        }
        
        // ESC 키 이벤트 리스너 정리
        if (inquiryModalEscapeHandler) {
            document.removeEventListener('keydown', inquiryModalEscapeHandler);
            inquiryModalEscapeHandler = null;
        }
    };

    // 문의 제출
    window.submitInquiry = function() {
        const content = document.getElementById('inquiryContent').value.trim();
        
        if (!content) {
            alert('문의 내용을 입력해주세요.');
            return;
        }
        
        if (content.length > 2000) {
            alert('문의 내용은 2000자를 초과할 수 없습니다.');
            return;
        }
        
        // 로딩 상태 표시
        document.getElementById('inquiryLoading').style.display = 'block';
        document.getElementById('submitInquiryBtn').disabled = true;
        
        // JSON 데이터 생성
        const data = {
            name: '',  // 사용자 이름은 빈 값으로 설정 (서버에서 처리)
            company_name: '',  // 회사명은 빈 값으로 설정
            contact: '',  // 연락처는 빈 값으로 설정
            content: content
        };
        
        // 문의 제출 요청
        fetch('/sales/submit_inquiry/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            // 로딩 상태 숨기기
            document.getElementById('inquiryLoading').style.display = 'none';
            document.getElementById('submitInquiryBtn').disabled = false;
            
            if (data.success) {
                alert('문의가 성공적으로 제출되었습니다.');
                window.closeInquiryModal();
            } else {
                alert('문의 제출 실패: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('문의 제출 오류:', error);
            document.getElementById('inquiryLoading').style.display = 'none';
            document.getElementById('submitInquiryBtn').disabled = false;
            alert('문의 제출 중 오류가 발생했습니다.');
        });
    };

    // 문자 수 카운트 업데이트
    window.updateInquiryCharCount = function() {
        const textarea = document.getElementById('inquiryContent');
        const charCount = document.getElementById('inquiryCharCount');
        const count = textarea.value.length;
        
        charCount.textContent = count;
        
        // 2000자 초과 시 경고 색상
        if (count > 2000) {
            charCount.style.color = '#dc3545';
        } else {
            charCount.style.color = '#6c757d';
        }
    };

    // 페이지 로드 시 이벤트 바인딩
    document.addEventListener('DOMContentLoaded', function() {
        // 문의 내용 텍스트 영역 이벤트
        const inquiryContent = document.getElementById('inquiryContent');
        if (inquiryContent) {
            inquiryContent.addEventListener('input', window.updateInquiryCharCount);
            inquiryContent.addEventListener('keydown', function(e) {
                // Ctrl+Enter로 제출
                if (e.ctrlKey && e.key === 'Enter') {
                    e.preventDefault();
                    window.submitInquiry();
                }
            });
        }
        
        // 모달 외부 클릭 시 닫기
        const inquiryModal = document.getElementById('inquiryModal');
        if (inquiryModal) {
            inquiryModal.addEventListener('click', function(e) {
                if (e.target === this) {
                    window.closeInquiryModal();
                }
            });
        }
    });
})();
