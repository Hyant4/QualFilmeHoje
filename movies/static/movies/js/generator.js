const MEDIA_TYPES = ["movie", "tv"];
const NAVIGATION_KEYS = ["ArrowLeft", "ArrowRight", "Home", "End"];

function updateRangeDisplay(input, output, suffix = "", decimals = 1) {
  if (!input) return;
  const value = Number(input.value);
  const min = Number(input.min);
  const max = Number(input.max);
  const progress = ((value - min) / (max - min)) * 100;
  const label = `${value.toFixed(decimals)}${suffix}`;
  if (output) {
    output.value = label;
    output.textContent = label;
  }
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
  const releaseYearInput = document.querySelector("#min_release_year");
  const maxReleaseYearInput = document.querySelector("#max_release_year");
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
    const minRating = Number(ratingInput.value).toFixed(1);
    const maxRating = Number(maxRatingInput.value).toFixed(1);
    updateRangeDisplay(ratingInput, null, "");
    updateRangeDisplay(maxRatingInput, null, "");
    ratingOutput.value = `${minRating} — ${maxRating}`;
    ratingOutput.textContent = `${minRating} — ${maxRating}`;
  }

  ratingInput?.addEventListener("input", () => {
    updateRatingRange(ratingInput);
    pulseRangeValue(ratingOutput);
  });
  maxRatingInput?.addEventListener("input", () => {
    updateRatingRange(maxRatingInput);
    pulseRangeValue(ratingOutput);
  });
  updateRatingRange();

  function updateReleaseYearRange(changedInput) {
    if (!releaseYearInput || !maxReleaseYearInput) return;
    if (changedInput === releaseYearInput && Number(releaseYearInput.value) > Number(maxReleaseYearInput.value)) {
      maxReleaseYearInput.value = releaseYearInput.value;
    }
    if (changedInput === maxReleaseYearInput && Number(maxReleaseYearInput.value) < Number(releaseYearInput.value)) {
      releaseYearInput.value = maxReleaseYearInput.value;
    }
    updateRangeDisplay(releaseYearInput, null, "", 0);
    updateRangeDisplay(maxReleaseYearInput, null, "", 0);
    const minYear = Number(releaseYearInput.value).toFixed(0);
    const maxYear = Number(maxReleaseYearInput.value).toFixed(0);
    releaseYearOutput.value = `${minYear} — ${maxYear}`;
    releaseYearOutput.textContent = `${minYear} — ${maxYear}`;
  }

  releaseYearInput?.addEventListener("input", () => {
    updateReleaseYearRange(releaseYearInput);
    pulseRangeValue(releaseYearOutput);
  });
  maxReleaseYearInput?.addEventListener("input", () => {
    updateReleaseYearRange(maxReleaseYearInput);
    pulseRangeValue(releaseYearOutput);
  });
  updateReleaseYearRange();

  function markAiSuggested(element) {
    element?.closest(".field")?.classList.add("is-ai-suggested");
  }

  function hasOption(select, value) {
    return [...select.options].some((option) => option.value === String(value));
  }

  function setAiSuggestedValue(element, value) {
    if (!element || value === null || value === undefined) return false;
    const textValue = String(value);
    if (element.tagName === "SELECT" && !hasOption(element, textValue)) return false;
    if (element.type === "range") {
      const numericValue = Number(value);
      if (
        !Number.isFinite(numericValue)
        || numericValue < Number(element.min)
        || numericValue > Number(element.max)
      ) {
        return false;
      }
    }
    element.value = textValue;
    element.dispatchEvent(new Event("input", { bubbles: true }));
    markAiSuggested(element);
    return true;
  }

  function applyAiFilters(filters) {
    if (!filters || typeof filters !== "object" || Array.isArray(filters)) return;
    if (MEDIA_TYPES.includes(filters.media_type)) {
      selectMedia(filters.media_type);
      document.querySelector(".media-picker")?.classList.add("is-ai-suggested");
    }

    const activeMediaType = mediaInput?.value;
    const genreInput = document.querySelector(`#${activeMediaType}_genre_id`);
    setAiSuggestedValue(genreInput, filters.genre_value);
    setAiSuggestedValue(releaseYearInput, filters.min_release_year);
    setAiSuggestedValue(ratingInput, filters.min_rating);
    setAiSuggestedValue(maxRatingInput, filters.max_rating);
    setAiSuggestedValue(
      document.querySelector("#runtime_filter"),
      filters.runtime_filter,
    );
    if (activeMediaType === "movie") {
      setAiSuggestedValue(
        document.querySelector("#certification"),
        filters.certification,
      );
    }
  }

  document.addEventListener("qualfilmehoje:apply-ai-filter", (event) => {
    applyAiFilters(event.detail?.filters);
  });

  document.querySelector("[data-generator-form]")?.addEventListener(
    "input",
    (event) => {
      event.target.closest(".field")?.classList.remove("is-ai-suggested");
    },
  );

  mediaButtons.forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelector(".media-picker")?.classList.remove("is-ai-suggested");
    });
  });

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
