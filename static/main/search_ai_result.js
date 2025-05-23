const titleTexts = document.querySelectorAll('.title-text-biz');

titleTexts.forEach(titleText => { 
  titleText.addEventListener('click', (e) => {
    detail = e.target.parentElement.nextElementSibling

    if (detail.style.display === 'flex') {
      detail.style.display = 'none'
    } else {
      detail.style.display = 'flex'
    }
  });
});