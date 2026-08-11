const ratingInput = document.querySelector("#min_rating");
const ratingOutput = document.querySelector("#ratingOutput");
const maxRatingInput = document.querySelector("#max_rating");
const maxRatingOutput = document.querySelector("#maxRatingOutput");
const releaseYearInput = document.querySelector("#min_release_year");
const releaseYearOutput = document.querySelector("#releaseYearOutput");
const mediaInput = document.querySelector("[data-media-input]");
const mediaButtons = [...document.querySelectorAll("[data-media-option]")];
const genreFields = [...document.querySelectorAll("[data-genre-field]")];

function selectMedia(mediaType, focus = false) {
  if (!mediaInput || !["movie", "tv"].includes(mediaType)) return;
  mediaInput.value = mediaType;
  mediaButtons.forEach((button) => {
    const selected = button.dataset.mediaOption === mediaType;
    button.setAttribute("aria-selected", String(selected));
    button.tabIndex = selected ? 0 : -1;
    if (selected && focus) button.focus();
  });
  genreFields.forEach((field) => {
    const selected = field.dataset.genreField === mediaType;
    field.hidden = !selected;
    const select = field.querySelector("select");
    if (select) select.disabled = !selected;
  });
  document.querySelectorAll("[data-media-noun]").forEach((element) => {
    element.textContent = element.dataset[mediaType];
  });
}

mediaButtons.forEach((button, index) => {
  button.addEventListener("click", () => selectMedia(button.dataset.mediaOption));
  button.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % mediaButtons.length;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + mediaButtons.length) % mediaButtons.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = mediaButtons.length - 1;
    selectMedia(mediaButtons[nextIndex].dataset.mediaOption, true);
  });
});

selectMedia(mediaInput?.value || "movie");

function updateRatingDisplay(input, output, suffix = "") {
  if (!input || !output) return;
  const value = Number(input.value);
  const min = Number(input.min);
  const max = Number(input.max);
  const progress = ((value - min) / (max - min)) * 100;
  output.value = `${value.toFixed(1)}${suffix}`;
  output.textContent = `${value.toFixed(1)}${suffix}`;
  input.style.setProperty("--range-progress", `${progress}%`);
}

function updateRatingRange(changedInput) {
  if (!ratingInput || !maxRatingInput) return;
  if (changedInput === ratingInput && Number(ratingInput.value) > Number(maxRatingInput.value)) {
    maxRatingInput.value = ratingInput.value;
  }
  if (changedInput === maxRatingInput && Number(maxRatingInput.value) < Number(ratingInput.value)) {
    ratingInput.value = maxRatingInput.value;
  }
  updateRatingDisplay(ratingInput, ratingOutput, "+");
  updateRatingDisplay(maxRatingInput, maxRatingOutput);
}

ratingInput?.addEventListener("input", () => updateRatingRange(ratingInput));
maxRatingInput?.addEventListener("input", () => updateRatingRange(maxRatingInput));
updateRatingRange();

function updateReleaseYearDisplay() {
  if (!releaseYearInput || !releaseYearOutput) return;
  const value = Number(releaseYearInput.value);
  const min = Number(releaseYearInput.min);
  const max = Number(releaseYearInput.max);
  const progress = ((value - min) / (max - min)) * 100;
  releaseYearOutput.value = String(value);
  releaseYearOutput.textContent = String(value);
  releaseYearInput.style.setProperty("--range-progress", `${progress}%`);
}

releaseYearInput?.addEventListener("input", updateReleaseYearDisplay);
updateReleaseYearDisplay();

document.querySelector("[data-alert-close]")?.addEventListener("click", (event) => {
  event.currentTarget.closest("[data-error-alert]")?.remove();
  document.body.classList.remove("has-top-alert");
});

const generatorForm = document.querySelector("[data-generator-form]");
generatorForm?.addEventListener("submit", () => {
  const button = generatorForm.querySelector("[data-generate-button]");
  const label = button?.querySelector(".button-label");
  if (button) button.disabled = true;
  if (label) label.textContent = mediaInput?.value === "tv" ? "Procurando série" : "Procurando filme";
});

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
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
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

document.querySelectorAll("[data-trends]").forEach((carousel) => {
  const viewport = carousel.querySelector("[data-trends-viewport]");
  const cards = [...carousel.querySelectorAll("[data-trend-card]")];
  const previousButton = carousel.querySelector("[data-trends-prev]");
  const nextButton = carousel.querySelector("[data-trends-next]");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let timer;

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
    if (!reducedMotion && !document.hidden) {
      timer = window.setInterval(() => move(1), 4200);
    }
  }

  function manualMove(direction) {
    move(direction);
    startAutoScroll();
  }

  previousButton?.addEventListener("click", () => manualMove(-1));
  nextButton?.addEventListener("click", () => manualMove(1));
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
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
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

  startAutoScroll();
});

const result = document.querySelector("[data-movie-result]");
if (result && window.location.hash !== "#gerador") {
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

document.querySelectorAll("[data-favorite-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("[data-favorite-button]");
    const icon = form.querySelector("[data-favorite-icon]");
    const label = form.querySelector("[data-favorite-label]");
    const feedback = form.querySelector("[data-favorite-feedback]");
    if (!button) return;

    button.disabled = true;
    if (feedback) feedback.textContent = "Salvando…";

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Não foi possível atualizar a minha lista.");

      button.setAttribute("aria-pressed", String(data.favorited));
      if (icon) icon.textContent = data.favorited ? "★" : "☆";
      if (label) label.textContent = data.favorited ? "Na minha lista" : "Adicionar à minha lista";
      if (feedback) feedback.textContent = data.message;

      if (!data.favorited) {
        const mediaType = form.querySelector("[name='media_type']")?.value;
        const tmdbId = form.querySelector("[name='tmdb_id']")?.value;
        document.querySelector(`[data-favorite-card="${mediaType}:${tmdbId}"]`)?.remove();
      }
    } catch (error) {
      if (feedback) feedback.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
});
