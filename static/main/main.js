document.addEventListener("DOMContentLoaded", () => {
  /* -----------------------------------------------------------------
     1) 디바이스 구분
  ----------------------------------------------------------------- */
  const mq = window.matchMedia("(max-width: 768px)");
  let isMobile = mq.matches;
  mq.addEventListener("change", (e) => (isMobile = e.matches));

  /* -----------------------------------------------------------------
     2) 애니메이션 대상 정의 (PC·모바일 각각 오프셋 지정)
  ----------------------------------------------------------------- */
  const animate = [
    { selector: ".ai-banner-text-box-subtitle", className: "visible-3", pc: "-10%", mobile: "-10%" },
    { selector: ".ai-banner-text-box-title",    className: "visible-3", pc: "-10%", mobile: "-10%" },
    { selector: ".ai-banner-text-box-sub",      className: "visible-3", pc: "-10%", mobile: "-10%" },
    { selector: ".ai-banner-mobile-inner-image", className: "visible",  pc: "-10%", mobile: "-10%" },

    { selector: ".biz-text-box-sub",   className: "visible-2", pc: "-30%", mobile: "-10%" },
    { selector: ".biz-text-box-title", className: "visible-2", pc: "-30%", mobile: "-10%" },
    { selector: ".coins",              className: "visible-2", pc: "-30%", mobile: "-10%" },

    { selector: ".biz-text-box-title2", className: "visible-2", pc: "-10%", mobile: "-10%" },
    { selector: ".biz-text-box-sub2",   className: "visible-2", pc: "-10%", mobile: "-10%" },
    { selector: ".wallet",             className: "visible-2", pc: "-10%", mobile: "-10%" },

    { selector: ".biz-text-box-title3", className: "visible-2", pc: "-10%", mobile: "-10%" },
    { selector: ".analysis",           className: "visible-2", pc: "-10%", mobile: "-10%" },

    { selector: ".intro-img-box-img1", className: "visible-2", pc: "-10%", mobile: "-10%" },
    { selector: ".intro-img-box-img2", className: "visible-2", pc: "-10%", mobile: "-10%" },

    { selector: ".namatji-intro-text-box-title", className: "visible-2", pc: "-10%", mobile: "-10%" },
    { selector: ".namatji-intro-img-box-text",   className: "visible-2", pc: "-10%", mobile: "-10%" },
    { selector: ".namatji-intro-img-box-text2",  className: "visible-2", pc: "-10%", mobile: "-10%" },

    { selector: ".namatji-wraper-button-box-button", className: "visible-2", pc: "10px", mobile: "10px" },
  ];

  /* -----------------------------------------------------------------
     3) PC·모바일 별 기준 설정
  ----------------------------------------------------------------- */
  const ratioShow = { pc: 0.25, mobile: 0.6 };  // 등장 비율
  const ratioHide = { pc: 0.10, mobile: 0.20 }; // 사라짐 비율

  /* -----------------------------------------------------------------
     4) 옵저버 생성 및 바인딩
  ----------------------------------------------------------------- */
  animate.forEach(({ selector, className, pc, mobile }) => {
    const offset = isMobile ? mobile : pc;
    const options = {
      root: null,
      rootMargin: `0px 0px ${offset} 0px`,
      threshold: isMobile ? [0, ratioShow.mobile] : [0, ratioShow.pc]
    };

    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        const show = isMobile ? ratioShow.mobile : ratioShow.pc;
        const hide = isMobile ? ratioHide.mobile : ratioHide.pc;

        if (entry.isIntersecting && entry.intersectionRatio >= show) {
          entry.target.classList.add(className);
        } else if (!entry.isIntersecting || entry.intersectionRatio < hide) {
          entry.target.classList.remove(className);
        }
      });
    }, options);

    document.querySelectorAll(selector).forEach((el) => io.observe(el));
  });
});

