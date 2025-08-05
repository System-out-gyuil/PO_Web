# 우분투 환경에서 auto_blog.py 실행 가이드

## 🔧 필수 의존성 설치

### 1. Chrome 브라우저 설치

#### 최신 우분투 (18.04 이상) - 권장 방법
```bash
# Chrome GPG 키를 trusted.gpg.d에 직접 다운로드
sudo wget -O /usr/share/keyrings/google-chrome-keyring.gpg https://dl.google.com/linux/linux_signing_key.pub

# Chrome 저장소 추가 (keyring 지정)
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# 패키지 목록 업데이트 및 Chrome 설치
sudo apt update
sudo apt install google-chrome-stable
```

#### GPG 키 오류가 발생하는 경우
```bash
# 기존 Chrome 관련 파일들 정리
sudo rm -f /etc/apt/sources.list.d/google-chrome.list
sudo rm -f /usr/share/keyrings/google-chrome-keyring.gpg

# GPG 키를 올바른 형식으로 다운로드
curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg

# Chrome 저장소 다시 추가
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# 업데이트 및 설치
sudo apt update
sudo apt install google-chrome-stable
```

#### 구버전 우분투 (16.04 이하) - 레거시 방법
```bash
# Chrome 저장소 키 추가 (deprecated 경고 발생)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# Chrome 저장소 추가
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# 패키지 목록 업데이트 및 Chrome 설치
sudo apt update
sudo apt install google-chrome-stable
```

#### 대안: Snap을 통한 설치 (Ubuntu 18.04+)
```bash
sudo snap install chromium
```

### 2. 필수 라이브러리 설치
```bash
sudo apt install libgconf-2-4 libxss1 libappindicator1 libindicator7
```

### 3. Python 의존성 설치
```bash
pip install selenium webdriver-manager filelock
```

## 🖥️ 디스플레이 환경 설정

### GUI 환경이 있는 경우
```bash
# DISPLAY 환경변수 확인
echo $DISPLAY

# 없다면 설정
export DISPLAY=:0
```

### 헤드리스 환경 (서버, Docker 등)
- 자동으로 헤드리스 모드로 실행됩니다
- 수동 로그인이 필요한 경우 네이버 아이디/비밀번호를 제공해야 합니다

## 🚀 실행 방법

### 자동 로그인 (권장)
```python
# 네이버 아이디/비밀번호를 POST 요청에 포함
data = {
    'naver_id': 'your_naver_id',
    'naver_password': 'your_password',
    'typo_probability': 0.1,
    'typing_speed': 0.5
}
```

### 수동 로그인
- 네이버 아이디/비밀번호를 제공하지 않으면 60초 내에 수동 로그인 필요
- 헤드리스 환경에서는 수동 로그인 불가능

## 🐛 문제 해결

### 문제 1: "Chrome이 설치되지 않았습니다"
```bash
# Chrome 설치 확인
google-chrome --version

# 설치되지 않았다면 위의 Chrome 설치 과정 진행
```

### 문제 2: "GPG error: NO_PUBKEY" 또는 서명 검증 오류
```bash
# Chrome GPG 키 문제 해결
sudo rm -f /etc/apt/sources.list.d/google-chrome.list
sudo rm -f /usr/share/keyrings/google-chrome-keyring.gpg

# 올바른 GPG 키 다운로드 (dearmor 포함)
curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg

# Chrome 저장소 다시 추가
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# 다시 업데이트
sudo apt update
```

### 문제 3: "PPA 저장소에 Release 파일이 없음" (certbot 등)
```bash
# 문제가 되는 PPA 저장소 제거
sudo rm /etc/apt/sources.list.d/certbot-ubuntu-certbot-*.list

# 또는 모든 PPA 저장소 확인 후 정리
ls /etc/apt/sources.list.d/
sudo rm /etc/apt/sources.list.d/[문제되는파일명]

# 업데이트
sudo apt update
```

### 문제 4: "DISPLAY 환경변수가 설정되지 않음"
```bash
# GUI 환경에서
export DISPLAY=:0

# 또는 서버 환경에서는 헤드리스 모드 사용 (자동)
```

### 문제 5: "selenium.common.exceptions.WebDriverException"
```bash
# ChromeDriver 캐시 정리
rm -rf ~/.wdm

# 권한 문제 해결
sudo chown -R $USER:$USER ~/.wdm
```

### 문제 6: "Memory issues"
```bash
# 스왑 메모리 추가 (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## ⚙️ 성능 최적화

### 1. 메모리 사용량 줄이기
- 자동으로 `--disable-images` 옵션 적용
- `--memory-pressure-off` 옵션으로 메모리 압박 상황 회피

### 2. 타임아웃 단축
- 블로그 탭 대기시간: 600초 → 30초
- 수동 로그인 대기시간: 300초 → 60초

### 3. 헤드리스 모드 자동 감지
- SSH 접속이나 DISPLAY 없는 환경에서 자동으로 헤드리스 모드 활성화

## 📋 체크리스트

실행 전에 다음 사항들을 확인하세요:

- [ ] Chrome 브라우저 설치됨
- [ ] 필수 라이브러리 설치됨
- [ ] Python 의존성 설치됨
- [ ] 네이버 아이디/비밀번호 준비 (자동 로그인용)
- [ ] 충분한 메모리 확보 (최소 2GB 권장)

## 🔍 디버깅

문제 발생 시 로그를 확인하세요:

1. **의존성 체크**: 자동으로 실행되는 의존성 체크 메시지 확인
2. **Chrome 실행**: "🔧 생성된 임시 디렉토리" 메시지 확인
3. **로그인**: "✅ 자동 로그인 완료" 또는 "✅ 수동 로그인 완료" 확인
4. **블로그 접근**: "✅ 블로그 사용자 ID 추출 완료" 확인 