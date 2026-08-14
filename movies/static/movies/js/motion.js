export function initResultReveal() {
  const result = document.querySelector("[data-movie-result]");
  if (!result || window.location.hash === "#gerador") return;

  let generatedReveal = false;
  try {
    generatedReveal = window.sessionStorage.getItem("qualfilmehoje:reveal-result") === "true";
    window.sessionStorage.removeItem("qualfilmehoje:reveal-result");
  } catch (_error) {
    generatedReveal = false;
  }

  if (generatedReveal || result.classList.contains("result-section--generated")) {
    result.classList.add("motion-result-enter");
    window.requestAnimationFrame(() => result.classList.add("is-visible"));
  }

  const revealResult = () => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.requestAnimationFrame(() => {
      result.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
    });
  };

  if (document.readyState === "complete") {
    revealResult();
  } else {
    window.addEventListener("load", revealResult, { once: true });
  }
}

export function initScrollReveals() {
  const revealTargets = [
    ...document.querySelectorAll(
      ".discovery-intro, .discovery-points article, .trends-section .section-head, .how-it-works .section-head, .steps article",
    ),
  ];
  if (!revealTargets.length) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  revealTargets.forEach((element, index) => {
    element.classList.add("motion-reveal");
    element.style.setProperty("--reveal-delay", `${Math.min(index % 3, 2) * 60}ms`);
  });

  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealTargets.forEach((element) => element.classList.add("is-visible"));
    return;
  }

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8%", threshold: 0.12 });
  revealTargets.forEach((element) => revealObserver.observe(element));
}
