const NAVIGATION_KEYS = ["ArrowLeft", "ArrowRight", "Home", "End"];

export function initTabs() {
  document.querySelectorAll("[data-tabs]").forEach((tabs) => {
    const buttons = [...tabs.querySelectorAll("[role='tab']")];
    const panels = [...tabs.querySelectorAll("[role='tabpanel']")];

    function activateTab(button, focus = true) {
      const tabName = button.dataset.tab;
      buttons.forEach((item) => {
        const selected = item === button;
        item.setAttribute("aria-selected", String(selected));
        item.tabIndex = selected ? 0 : -1;
      });
      panels.forEach((panel) => {
        panel.hidden = panel.dataset.panel !== tabName;
      });
      if (focus) button.focus();
    }

    buttons.forEach((button, index) => {
      button.addEventListener("click", () => activateTab(button, false));
      button.addEventListener("keydown", (event) => {
        if (!NAVIGATION_KEYS.includes(event.key)) return;
        event.preventDefault();
        let nextIndex = index;
        if (event.key === "ArrowRight") nextIndex = (index + 1) % buttons.length;
        if (event.key === "ArrowLeft") nextIndex = (index - 1 + buttons.length) % buttons.length;
        if (event.key === "Home") nextIndex = 0;
        if (event.key === "End") nextIndex = buttons.length - 1;
        activateTab(buttons[nextIndex]);
      });
    });
  });
}

export function initTrends() {
  document.querySelectorAll("[data-trends]").forEach((carousel) => {
    const viewport = carousel.querySelector("[data-trends-viewport]");
    const cards = [...carousel.querySelectorAll("[data-trend-card]")];
    const previousButton = carousel.querySelector("[data-trends-prev]");
    const nextButton = carousel.querySelector("[data-trends-next]");
    const toggleButton = carousel.querySelector("[data-trends-toggle]");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let timer;
    let userPaused = reducedMotion;

    if (!viewport || cards.length < 2) return;

    function cardStep() {
      const track = viewport.querySelector(".trends-track");
      const gap = Number.parseFloat(window.getComputedStyle(track).columnGap) || 0;
      return cards[0].getBoundingClientRect().width + gap;
    }

    function move(direction) {
      const step = cardStep();
      const maxScroll = Math.max(viewport.scrollWidth - viewport.clientWidth, 0);
      const reachedEnd = viewport.scrollLeft >= maxScroll - step * 0.5;
      const reachedStart = viewport.scrollLeft <= step * 0.5;

      if (direction > 0 && reachedEnd) {
        viewport.scrollTo({ left: 0, behavior: reducedMotion ? "auto" : "smooth" });
      } else if (direction < 0 && reachedStart) {
        viewport.scrollTo({ left: maxScroll, behavior: reducedMotion ? "auto" : "smooth" });
      } else {
        viewport.scrollBy({ left: direction * step, behavior: reducedMotion ? "auto" : "smooth" });
      }
    }

    function stopAutoScroll() {
      window.clearInterval(timer);
    }

    function startAutoScroll() {
      stopAutoScroll();
      if (!userPaused && !document.hidden) {
        timer = window.setInterval(() => move(1), 4200);
      }
    }

    function updateToggleButton() {
      if (!toggleButton) return;
      toggleButton.setAttribute("aria-pressed", String(userPaused));
      toggleButton.setAttribute(
        "aria-label",
        userPaused ? "Retomar rotação automática" : "Pausar rotação automática",
      );
      toggleButton.textContent = userPaused ? "Retomar" : "Pausar";
    }

    function manualMove(direction) {
      move(direction);
      startAutoScroll();
    }

    previousButton?.addEventListener("click", () => manualMove(-1));
    nextButton?.addEventListener("click", () => manualMove(1));
    toggleButton?.addEventListener("click", () => {
      userPaused = !userPaused;
      updateToggleButton();
      if (userPaused) stopAutoScroll();
      else startAutoScroll();
    });
    carousel.addEventListener("mouseenter", stopAutoScroll);
    carousel.addEventListener("mouseleave", startAutoScroll);
    carousel.addEventListener("focusin", stopAutoScroll);
    carousel.addEventListener("focusout", (event) => {
      if (!carousel.contains(event.relatedTarget)) startAutoScroll();
    });
    viewport.addEventListener("pointerdown", stopAutoScroll);
    viewport.addEventListener("pointerup", startAutoScroll);
    viewport.addEventListener("pointercancel", startAutoScroll);
    viewport.addEventListener("keydown", (event) => {
      if (!NAVIGATION_KEYS.includes(event.key)) return;
      event.preventDefault();
      if (event.key === "Home") {
        viewport.scrollTo({ left: 0, behavior: reducedMotion ? "auto" : "smooth" });
      } else if (event.key === "End") {
        viewport.scrollTo({ left: viewport.scrollWidth, behavior: reducedMotion ? "auto" : "smooth" });
      } else {
        manualMove(event.key === "ArrowRight" ? 1 : -1);
      }
    });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) stopAutoScroll();
      else startAutoScroll();
    });

    updateToggleButton();
    startAutoScroll();
  });
}
