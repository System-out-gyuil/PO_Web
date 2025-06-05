const input = document.querySelector('#naver-blog-input');
const inputButton = document.querySelector('#naver-blog-button');
const inputFile = document.querySelector('#naver-blog-input-file');

const output = document.querySelector('#naver-blog-output');
const outputButton = document.querySelector('#naver-blog-output-button');


inputButton.addEventListener('click', () => {
  console.log(input.value);
  const local = 'http://127.0.0.1:8000';

  fetch(`${local}/blog/naver-blog/`, {
    method: 'POST',
    body: JSON.stringify({
      input: input.value,
      file: inputFile.value
    })
  });

});

inputFile.addEventListener('change', () => {
  console.log(inputFile.value);
});






