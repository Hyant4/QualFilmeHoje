const ratingInput = document.querySelector("#min_rating");
const ratingOutput = document.querySelector("#ratingOutput");
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

function updateRating() {
  if (!ratingInput || !ratingOutput) return;
  const value = Number(ratingInput.value);
  const min = Number(ratingInput.min);
  const max = Number(ratingInput.max);
  const progress = ((value - min) / (max - min)) * 100;
  ratingOutput.value = `${value.toFixed(1)}+`;
  ratingOutput.textContent = `${value.toFixed(1)}+`;
  ratingInput.style.setProperty("--range-progress", `${progress}%`);
}

ratingInput?.addEventListener("input", updateRating);
updateRating();

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

const result = document.querySelector("[data-movie-result]");
if (result && window.location.hash !== "#gerador") {
  window.requestAnimationFrame(() => {
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  });
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
      if (!response.ok) throw new Error(data.error || "Não foi possível atualizar os favoritos.");

      button.setAttribute("aria-pressed", String(data.favorited));
      if (icon) icon.textContent = data.favorited ? "★" : "☆";
      if (label) label.textContent = data.favorited ? "Nos favoritos" : "Adicionar aos favoritos";
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
