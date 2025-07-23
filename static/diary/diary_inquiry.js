// 문의하기 모달 열기
function openInquiryModal() {
    const modal = document.getElementById('inquiryModal');
    modal.style.display = 'flex';
    
    // 텍스트 영역 초기화
    document.getElementById('inquiryContent').value = '';
    document.getElementById('inquiryCharCount').textContent = '0';
    
    // 로딩 상태 초기화
    document.getElementById('inquiryLoading').style.display = 'none';
    document.getElementById('submitInquiryBtn').disabled = false;
    
    // 텍스트 영역에 포커스
    document.getElementById('inquiryContent').focus();
}

// 문의하기 모달 닫기
function closeInquiryModal() {
    const modal = document.getElementById('inquiryModal');
    modal.style.display = 'none';
}

// 문의 제출
function submitInquiry() {
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
    
    // FormData 생성
    const formData = new FormData();
    formData.append('content', content);
    
    // 문의 제출 요청
    fetch('/sales/submit_inquiry/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 로딩 상태 숨기기
        document.getElementById('inquiryLoading').style.display = 'none';
        document.getElementById('submitInquiryBtn').disabled = false;
        
        if (data.success) {
            alert('문의가 성공적으로 제출되었습니다.');
            closeInquiryModal();
        } else {
            alert('문의 제출 실패: ' + (data.error || '알 수 없는 오류'));
        }
    })
    .catch(error => {
        console.error('문의 제출 오류:', error);
        document.getElementById('inquiryLoading').style.display = 'none';
        document.getElementById('submitInquiryBtn').disabled = false;
        alert('문의 제출 중 오류가 발생했습니다.');
    });
}

// 문자 수 카운트 업데이트
function updateInquiryCharCount() {
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
}

// 페이지 로드 시 이벤트 바인딩
document.addEventListener('DOMContentLoaded', function() {
    // 문의 내용 텍스트 영역 이벤트
    const inquiryContent = document.getElementById('inquiryContent');
    if (inquiryContent) {
        inquiryContent.addEventListener('input', updateInquiryCharCount);
        inquiryContent.addEventListener('keydown', function(e) {
            // Ctrl+Enter로 제출
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                submitInquiry();
            }
        });
    }
    
    // 모달 외부 클릭 시 닫기
    const inquiryModal = document.getElementById('inquiryModal');
    if (inquiryModal) {
        inquiryModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeInquiryModal();
            }
        });
    }
});
