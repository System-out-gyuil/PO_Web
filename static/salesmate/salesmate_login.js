// 전역 변수
let emailVerificationTimer = null;
let emailVerified = false;
let emailDuplicateChecked = false;

// DOM 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 로그인 폼 이벤트 리스너
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // 회원가입 폼 이벤트 리스너
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }

    // 이메일 입력 시 중복 검사 상태 초기화
    const signupEmailInput = document.getElementById('signup_id');
    if (signupEmailInput) {
        signupEmailInput.addEventListener('input', function() {
            emailDuplicateChecked = false;
            emailVerified = false;
            updateEmailStatus('', '');
            updateVerificationStatus('', '');
        });
    }

    // 비밀번호 확인 입력 시 실시간 검증
    const passwordInput = document.getElementById('signup_pw');
    const passwordConfirmInput = document.getElementById('signup_pw_confirm');
    
    if (passwordInput && passwordConfirmInput) {
        passwordConfirmInput.addEventListener('input', function() {
            const password = passwordInput.value;
            const confirmPassword = passwordConfirmInput.value;
            
            if (confirmPassword && password !== confirmPassword) {
                passwordConfirmInput.style.borderColor = '#dc3545';
            } else {
                passwordConfirmInput.style.borderColor = '#ddd';
            }
        });
    }
});

// 로그인 처리
async function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const loginError = document.getElementById('loginError');
    const loginSuccess = document.getElementById('loginSuccess');
    
    // 로딩 상태 표시
    setLoadingState(event.target, true);
    hideMessages();
    
    try {
        const response = await fetch('/salesmate/login/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(loginSuccess, data.message, 'success');
            setTimeout(() => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.href = '/salesmate/';
                }
            }, 1000);
        } else {
            showMessage(loginError, data.message, 'error');
        }
    } catch (error) {
        showMessage(loginError, '로그인 중 오류가 발생했습니다.', 'error');
    } finally {
        setLoadingState(event.target, false);
    }
}

// 회원가입 처리
async function handleSignup(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const signupError = document.getElementById('signupError');
    const signupSuccess = document.getElementById('signupSuccess');
    
    // 유효성 검사
    if (!validateSignupForm()) {
        return;
    }
    
    // 로딩 상태 표시
    setLoadingState(event.target, true);
    hideMessages();
    
    try {
        const response = await fetch('/salesmate/signup/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(signupSuccess, data.message, 'success');
            setTimeout(() => {
                closeSignupModal();
                // 로그인 폼으로 포커스
                const loginForm = document.getElementById('loginForm');
                if (loginForm) {
                    loginForm.querySelector('input[name="member_id"]').focus();
                }
            }, 2000);
        } else {
            showMessage(signupError, data.message, 'error');
        }
    } catch (error) {
        showMessage(signupError, '회원가입 중 오류가 발생했습니다.', 'error');
    } finally {
        setLoadingState(event.target, false);
    }
}

// 회원가입 폼 유효성 검사
function validateSignupForm() {
    const signupError = document.getElementById('signupError');
    
    // 이메일 중복 검사 확인
    if (!emailDuplicateChecked) {
        showMessage(signupError, '이메일 중복 검사를 완료해주세요.', 'error');
        return false;
    }
    
    // 이메일 인증 확인
    if (!emailVerified) {
        showMessage(signupError, '이메일 인증을 완료해주세요.', 'error');
        return false;
    }
    
    // 비밀번호 확인
    const password = document.getElementById('signup_pw').value;
    const confirmPassword = document.getElementById('signup_pw_confirm').value;
    
    if (password !== confirmPassword) {
        showMessage(signupError, '비밀번호가 일치하지 않습니다.', 'error');
        return false;
    }
    
    // 개인정보처리방침 동의 확인
    const privacyCheck = document.getElementById('privacy_check');
    if (!privacyCheck.checked) {
        showMessage(signupError, '개인정보처리방침에 동의해주세요.', 'error');
        return false;
    }
    
    // 이용약관 동의 확인
    const termsCheck = document.getElementById('terms_check');
    if (!termsCheck.checked) {
        showMessage(signupError, '이용약관에 동의해주세요.', 'error');
        return false;
    }
    
    return true;
}

// 이메일 중복 검사
async function checkEmailDuplicate() {
    const email = document.getElementById('signup_id').value.trim();
    const checkBtn = document.getElementById('check_duplicate_btn');
    
    if (!email) {
        updateEmailStatus('이메일을 입력해주세요.', 'error');
        return;
    }
    
    // 이메일 형식 검사
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        updateEmailStatus('올바른 이메일 형식을 입력해주세요.', 'error');
        return;
    }
    
    // 로딩 상태 표시
    checkBtn.disabled = true;
    checkBtn.textContent = '확인 중...';
    
    try {
        const formData = new FormData();
        formData.append('email', email);
        
        const response = await fetch('/salesmate/check_email_duplicate/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateEmailStatus(data.message, 'success');
            emailDuplicateChecked = true;
        } else {
            updateEmailStatus(data.message, 'error');
            emailDuplicateChecked = false;
        }
    } catch (error) {
        updateEmailStatus('이메일 중복 확인 중 오류가 발생했습니다.', 'error');
        emailDuplicateChecked = false;
    } finally {
        checkBtn.disabled = false;
        checkBtn.textContent = '중복 검사';
    }
}

// 인증번호 발송
async function sendVerificationCode() {
    const email = document.getElementById('signup_id').value.trim();
    const sendBtn = document.getElementById('send_verification_btn');
    
    if (!email) {
        updateVerificationStatus('이메일을 먼저 입력해주세요.', 'error');
        return;
    }
    
    if (!emailDuplicateChecked) {
        updateVerificationStatus('이메일 중복 검사를 먼저 완료해주세요.', 'error');
        return;
    }
    
    // 로딩 상태 표시
    sendBtn.disabled = true;
    sendBtn.textContent = '발송 중...';
    
    try {
        const formData = new FormData();
        formData.append('email', email);
        
        const response = await fetch('/salesmate/send_verification_email/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateVerificationStatus(data.message, 'success');
            startCountdown();
        } else {
            updateVerificationStatus(data.message, 'error');
        }
    } catch (error) {
        updateVerificationStatus('인증번호 발송 중 오류가 발생했습니다.', 'error');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = '인증번호 발송';
    }
}

// 인증번호 확인
async function verifyEmail() {
    const email = document.getElementById('signup_id').value.trim();
    const verificationCode = document.getElementById('verification_code').value.trim();
    
    if (!email || !verificationCode) {
        updateVerificationStatus('이메일과 인증번호를 입력해주세요.', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('email', email);
        formData.append('verification_code', verificationCode);
        
        const response = await fetch('/salesmate/verify_email/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateVerificationStatus(data.message, 'success');
            emailVerified = true;
            clearCountdown();
        } else {
            updateVerificationStatus(data.message, 'error');
            emailVerified = false;
        }
    } catch (error) {
        updateVerificationStatus('이메일 인증 중 오류가 발생했습니다.', 'error');
        emailVerified = false;
    }
}

// 인증번호 입력 시 자동 인증
document.addEventListener('DOMContentLoaded', function() {
    const verificationCodeInput = document.getElementById('verification_code');
    if (verificationCodeInput) {
        verificationCodeInput.addEventListener('input', function() {
            if (this.value.length === 6) {
                verifyEmail();
            }
        });
    }
});

// 카운트다운 시작
function startCountdown() {
    let timeLeft = 300; // 5분 = 300초
    const countdownElement = document.getElementById('countdown_timer');
    
    if (countdownElement) {
        countdownElement.style.display = 'block';
    }
    
    emailVerificationTimer = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        if (countdownElement) {
            countdownElement.textContent = `인증번호 만료까지 ${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        
        timeLeft--;
        
        if (timeLeft < 0) {
            clearCountdown();
            updateVerificationStatus('인증번호가 만료되었습니다. 다시 발송해주세요.', 'error');
        }
    }, 1000);
}

// 카운트다운 정리
function clearCountdown() {
    if (emailVerificationTimer) {
        clearInterval(emailVerificationTimer);
        emailVerificationTimer = null;
    }
    
    const countdownElement = document.getElementById('countdown_timer');
    if (countdownElement) {
        countdownElement.style.display = 'none';
    }
}

// 이메일 상태 업데이트
function updateEmailStatus(message, type) {
    const statusElement = document.getElementById('email_status');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.style.color = type === 'success' ? '#155724' : type === 'error' ? '#dc3545' : '#666';
    }
}

// 인증 상태 업데이트
function updateVerificationStatus(message, type) {
    const statusElement = document.getElementById('verification_status');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.style.color = type === 'success' ? '#155724' : type === 'error' ? '#dc3545' : '#666';
    }
}

// 메시지 표시
function showMessage(element, message, type) {
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
        
        // 3초 후 자동 숨김
        setTimeout(() => {
            element.style.display = 'none';
        }, 3000);
    }
}

// 메시지 숨김
function hideMessages() {
    const errorElements = document.querySelectorAll('.error');
    const successElements = document.querySelectorAll('.success');
    
    errorElements.forEach(el => el.style.display = 'none');
    successElements.forEach(el => el.style.display = 'none');
}

// 로딩 상태 설정
function setLoadingState(form, isLoading) {
    const inputs = form.querySelectorAll('input, button');
    inputs.forEach(input => {
        input.disabled = isLoading;
    });
    
    if (isLoading) {
        form.classList.add('loading');
    } else {
        form.classList.remove('loading');
    }
}

// CSRF 토큰 가져오기
function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

// 회원가입 모달 열기
function openSignupModal() {
    const modal = document.getElementById('signupModal');
    if (modal) {
        modal.style.display = 'flex';
        // 이메일 입력 필드에 포커스
        setTimeout(() => {
            const emailInput = document.getElementById('signup_id');
            if (emailInput) {
                emailInput.focus();
            }
        }, 100);
    }
}

// 회원가입 모달 닫기
function closeSignupModal() {
    const modal = document.getElementById('signupModal');
    if (modal) {
        modal.style.display = 'none';
        // 폼 초기화
        resetSignupForm();
    }
}

// 회원가입 폼 초기화
function resetSignupForm() {
    const form = document.getElementById('signupForm');
    if (form) {
        form.reset();
    }
    
    // 상태 초기화
    emailVerified = false;
    emailDuplicateChecked = false;
    
    // 상태 메시지 초기화
    updateEmailStatus('', '');
    updateVerificationStatus('', '');
    
    // 카운트다운 정리
    clearCountdown();
    
    // 메시지 숨김
    hideMessages();
}

// 개인정보처리방침 모달 열기
function openPrivacyModal() {
    // 개인정보처리방침 내용을 새 창으로 열기
    window.open('/salesmate/personal_info/', '_blank', 'width=800,height=600');
}

// 이용약관 모달 열기
function openTermsModal() {
    // 이용약관 내용을 새 창으로 열기
    window.open('/salesmate/terms_of_service/', '_blank', 'width=800,height=600');
}

// 모달 외부 클릭 시 닫기
window.addEventListener('click', function(event) {
    const modal = document.getElementById('signupModal');
    if (event.target === modal) {
        closeSignupModal();
    }
});

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeSignupModal();
    }
});
