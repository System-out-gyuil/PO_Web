function toggleContent(id) {
  const summary = document.getElementById('summary-' + id);
  const fullText = document.getElementById('full-' + id);
  const button = document.getElementById('button-' + id);

  if (fullText.style.display === 'none') {
    fullText.style.display = 'block';
    summary.style.display = 'none';
    button.innerText = '접기';
  } else {
    fullText.style.display = 'none';
    summary.style.display = '-webkit-box';
    button.innerText = '더보기';
  }
}