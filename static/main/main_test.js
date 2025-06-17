window.addEventListener("scroll", function () {
  const subtitle = document.querySelector(".ai-banner-text-box-subtitle");
  const title = document.querySelector(".ai-banner-text-box-title");
  const sub = document.querySelector(".ai-banner-text-box-sub");
  const innerImage = document.querySelector(".ai-banner-mobile-inner-image");
  const scrollY = window.scrollY;
  console.log(scrollY);

  if (scrollY > 250) {
    subtitle.style.opacity = 0;
    title.style.opacity = 0;
    sub.style.opacity = 0;
  } else {
    subtitle.style.opacity = 1;
    title.style.opacity = 1;
    sub.style.opacity = 1;
  }

  if (scrollY > 275 && scrollY < 1500) {
    innerImage.classList.add("visible");
  } else {
    innerImage.classList.remove("visible");
  }

  const bizTextBoxTitle = document.querySelector(".biz-text-box-title");
  const bizTextBoxSub = document.querySelector(".biz-text-box-sub");
  const coins = document.querySelector(".coins");

  if (scrollY > 1200 && scrollY < 2200) {
    bizTextBoxTitle.classList.add("visible-2");
    bizTextBoxSub.classList.add("visible-2");
    coins.classList.add("visible-2");
  } else {
    bizTextBoxTitle.classList.remove("visible-2");
    bizTextBoxSub.classList.remove("visible-2");
    coins.classList.remove("visible-2");
  }

  const bizTextBoxTitle2 = document.querySelector(".biz-text-box-title2");
  const bizTextBoxSub2 = document.querySelector(".biz-text-box-sub2");
  const wallet = document.querySelector(".wallet");

  if (scrollY > 1900 && scrollY < 2900) {
    bizTextBoxTitle2.classList.add("visible-2");
    bizTextBoxSub2.classList.add("visible-2");
    wallet.classList.add("visible-2");
  } else {
    bizTextBoxTitle2.classList.remove("visible-2");
    bizTextBoxSub2.classList.remove("visible-2");
    wallet.classList.remove("visible-2");
  }
  

  const bizTextBoxTitle3 = document.querySelector(".biz-text-box-title3");
  const analysis = document.querySelector(".analysis");

  if (scrollY > 2600 && scrollY < 3600) {
    bizTextBoxTitle3.classList.add("visible-2");
    analysis.classList.add("visible-2");
  } else {
    bizTextBoxTitle3.classList.remove("visible-2");
    analysis.classList.remove("visible-2");
  }
});