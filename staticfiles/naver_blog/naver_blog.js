const input = document.querySelector('#naver-blog-input');
const inputButton = document.querySelector('#naver-blog-button');
const inputFile = document.querySelector('#naver-blog-input-file');

const outputButton = document.querySelector('#naver-blog-output-button');

const outputPageContainer = document.querySelector('.output-page-container');
const outputTextareas = document.querySelector('.output-textareas');
let num = 1;
const local = 'http://127.0.0.1:8000';

inputButton.addEventListener('click', () => {
  const formData = new FormData();

  formData.append("input", input.value);

  let pages = '';
  let textareas = '';

  // ✅ 모든 파일 추가
  for (let i = 0; i < inputFile.files.length; i++) {
    formData.append("files", inputFile.files[i]);  // key: files (복수형)
    pages += `<div class="output-page-number">${i + 1}</div>`;
    textareas += `<textarea type="text" class="tt${i + 1} output-textarea dis-none" placeholder="GPT 응답 출력 칸, 잠시만 기다려주십시오"></textarea>`;
  }

  outputPageContainer.innerHTML = pages;
  outputTextareas.innerHTML = textareas;

  fetch(`${local}/blog/naver-blog/`, {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    console.log(data);
    for (let i = 0; i < data.previews.length; i++) {
      document.querySelector('.tt'+(i + 1)).value = data.previews[i];
    }
  })
  .catch(error => {
    console.error('Error:', error);
  });
});

outputPageContainer.addEventListener('click', (e) => {
  const selected = e.target.textContent.trim();
  const targetClass = `.tt${selected}`;

  num = selected;

  // ✅ 형제 요소의 테두리를 모두 검정색으로 초기화
  Array.from(e.target.parentNode.children).forEach(sibling => {
    sibling.style.border = '1px solid #000';
  });

  // ✅ 클릭한 요소만 흰색 테두리로 변경
  e.target.style.border = '1px solid #fff';

  // ✅ 모든 tt 요소 숨기기
  document.querySelectorAll('*').forEach(el => {
    el.classList.forEach(className => {
      if (className.startsWith('tt')) {
        el.style.display = 'none';
      }
    });
  });

  // ✅ 선택된 tt 요소만 보이기
  const activeEl = document.querySelector(targetClass);
  if (activeEl) {
    activeEl.style.display = 'block';
  }
});

const downloadButton = document.querySelector('#naver-blog-download-button');

downloadButton.addEventListener('click', () => {
  window.location.href = '/blog/naver-blog/download-zip/';
});


// // 저장하기 버튼
// outputButton.addEventListener('click', () => {
//   let text = document.querySelector('.tt' + num).value;
//   console.log(text);
//   fetch(`${local}/blog/naver-blog/save-txt/`, {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json'
//     },
//     body: JSON.stringify({
//       input: text
//     })
//   })  
//   .then(response => response.json())
//   .then(data => {
//     alert(`${data.filename} 파일이 저장되었습니다.`);
//   })
//   .catch(error => {
//     console.error('Error:', error);
//   });
  
// });

// const writeButton = document.querySelector('#naver-blog-write-button');

// writeButton.addEventListener('click', () => {
//   console.log('네이버 블로그 작성하기 버튼 클릭');
//   fetch(`${local}/blog/naver-blog/write/`, {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json'
//     },
//   })
// });








