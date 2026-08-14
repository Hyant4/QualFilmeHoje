const MEDIA_TYPES = ["movie", "tv"];
const NAVIGATION_KEYS = ["ArrowLeft", "ArrowRight", "Home", "End"];

function updateRangeDisplay(input, output, suffix = "", decimals = 1) {
  if (!input || !output) return;
  const value = Number(input.value);
  const min = Number(input.min);
  const max = Number(input.max);
  const progress = ((value - min) / (max - min)) * 100;
  const label = `${value.toFixed(decimals)}${suffix}`;
  output.value = label;
  output.textContent = label;
  input.style.setProperty("--range-progress", `${progress}%`);
}

function pulseRangeValue(output) {
  if (!output || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  output.classList.remove("is-updating");
  window.requestAnimationFrame(() => output.classList.add("is-updating"));
}

export function initGenerator() {
  const ratingInput = document.querySelector("#min_rating");
  const ratingOutput = document.querySelector("#ratingOutput");
  const maxRatingInput = document.querySelector("#max_rating");
  const maxRatingOutput = document.querySelector("#maxRatingOutput");
  const releaseYearInput = document.querySelector("#min_release_year");
  const releaseYearOutput = document.querySelector("#releaseYearOutput");
  const mediaInput = document.querySelector("[data-media-input]");
  const mediaButtons = [...document.querySelectorAll("[data-media-option]")];
  const genreFields = [...document.querySelectorAll("[data-genre-field]")];
  const movieOnlyFields = [...document.querySelectorAll("[data-movie-only]")];

  function selectMedia(mediaType, focus = false) {
    if (!mediaInput || !MEDIA_TYPES.includes(mediaType)) return;
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
    movieOnlyFields.forEach((field) => {
      const selected = mediaType === "movie";
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
      if (!NAVIGATION_KEYS.includes(event.key)) return;
      event.preventDefault();
      let nextIndex = index;
      if (event.key === "ArrowRight") nextIndex = (index + 1) % mediaButtons.length;
      if (event.key === "ArrowLeft") {
        nextIndex = (index - 1 + mediaButtons.length) % mediaButtons.length;
      }
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = mediaButtons.length - 1;
      selectMedia(mediaButtons[nextIndex].dataset.mediaOption, true);
    });
  });
  selectMedia(mediaInput?.value || "movie");

  function updateRatingRange(changedInput) {
    if (!ratingInput || !maxRatingInput) return;
    if (changedInput === ratingInput && Number(ratingInput.value) > Number(maxRatingInput.value)) {
      maxRatingInput.value = ratingInput.value;
    }
    if (changedInput === maxRatingInput && Number(maxRatingInput.value) < Number(ratingInput.value)) {
      ratingInput.value = maxRatingInput.value;
    }
    updateRangeDisplay(ratingInput, ratingOutput, "+");
    updateRangeDisplay(maxRatingInput, maxRatingOutput);
  }

  ratingInput?.addEventListener("input", () => {
    updateRatingRange(ratingInput);
    pulseRangeValue(ratingOutput);
  });
  maxRatingInput?.addEventListener("input", () => {
    updateRatingRange(maxRatingInput);
    pulseRangeValue(maxRatingOutput);
  });
  updateRatingRange();

  function updateReleaseYearDisplay() {
    updateRangeDisplay(releaseYearInput, releaseYearOutput, "", 0);
  }

  releaseYearInput?.addEventListener("input", () => {
    updateReleaseYearDisplay();
    pulseRangeValue(releaseYearOutput);
  });
  updateReleaseYearDisplay();

  document.querySelector("[data-alert-close]")?.addEventListener("click", (event) => {
    event.currentTarget.closest("[data-error-alert]")?.remove();
    document.body.classList.remove("has-top-alert");
  });

  const generatorForm = document.querySelector("[data-generator-form]");
  generatorForm?.addEventListener("submit", () => {
    const button = generatorForm.querySelector("[data-generate-button]");
    const label = button?.querySelector(".button-label");
    const hero = document.querySelector(".hero");
    const tvScreen = document.querySelector("[data-hero-tv-screen]");
    if (button) button.disabled = true;
    if (label) {
      label.textContent = mediaInput?.value === "tv" ? "Procurando série" : "Procurando filme";
    }
    hero?.classList.add("is-searching");
    tvScreen?.classList.add("is-loading");
    tvScreen?.setAttribute("aria-busy", "true");
    try {
      window.sessionStorage.setItem("qualfilmehoje:reveal-result", "true");
    } catch (_error) {
      // O sorteio continua funcionando quando o armazenamento está indisponível.
    }
  });
}
