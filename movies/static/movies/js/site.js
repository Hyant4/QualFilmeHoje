document.documentElement.classList.add("motion-ready");

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

function pulseRangeValue(output) {
  if (!output || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  output.classList.remove("is-updating");
  window.requestAnimationFrame(() => output.classList.add("is-updating"));
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
  if (!releaseYearInput || !releaseYearOutput) return;
  const value = Number(releaseYearInput.value);
  const min = Number(releaseYearInput.min);
  const max = Number(releaseYearInput.max);
  const progress = ((value - min) / (max - min)) * 100;
  releaseYearOutput.value = String(value);
  releaseYearOutput.textContent = String(value);
  releaseYearInput.style.setProperty("--range-progress", `${progress}%`);
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
  if (label) label.textContent = mediaInput?.value === "tv" ? "Procurando série" : "Procurando filme";
  hero?.classList.add("is-searching");
  tvScreen?.classList.add("is-loading");
  tvScreen?.setAttribute("aria-busy", "true");
  try {
    window.sessionStorage.setItem("qualfilmehoje:reveal-result", "true");
  } catch (_error) {
    // O sorteio continua funcionando quando o armazenamento esta indisponivel.
  }
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

  updateToggleButton();
  startAutoScroll();
});

const result = document.querySelector("[data-movie-result]");

const browserHistoryStorageKey = "qualfilmehoje:history:v1";
const browserHistoryLimit = 8;

function readBrowserHistory() {
  try {
    const value = JSON.parse(window.localStorage.getItem(browserHistoryStorageKey) || "[]");
    if (!Array.isArray(value)) return [];
    return value.filter((item) => (
      item
      && Number.isSafeInteger(Number(item.id))
      && ["movie", "tv"].includes(item.media_type)
      && typeof item.title === "string"
      && typeof item.detail_url === "string"
      && item.detail_url.startsWith("/titulo/")
    )).slice(0, browserHistoryLimit);
  } catch (_error) {
    return [];
  }
}

function writeBrowserHistory(history) {
  try {
    window.localStorage.setItem(
      browserHistoryStorageKey,
      JSON.stringify(history.slice(0, browserHistoryLimit)),
    );
  } catch (_error) {
    // Navegacao privada ou armazenamento indisponivel nao bloqueiam o sorteio.
  }
}

function renderBrowserHistory(history) {
  const section = document.querySelector("[data-library-section]");
  const group = document.querySelector("[data-browser-history-group]");
  const list = document.querySelector("[data-browser-history-list]");
  const count = document.querySelector("[data-browser-history-count]");
  if (!section || !group || !list || !count || history.length === 0) return;

  list.replaceChildren();
  history.forEach((item, index) => {
    const row = document.createElement("li");
    const link = document.createElement("a");
    link.className = "history-link";
    link.href = item.detail_url;

    const position = document.createElement("span");
    position.className = "history-index mono";
    position.textContent = String(index + 1).padStart(2, "0");

    const copy = document.createElement("div");
    const title = document.createElement("h4");
    title.textContent = item.title;
    const details = document.createElement("p");
    const genre = item.genre_name || "Qualquer gênero";
    const rating = Number(item.min_rating);
    details.textContent = `${genre} · nota ${Number.isFinite(rating) ? rating.toFixed(1) : "0.0"}+`;
    copy.append(title, details);

    const time = document.createElement("time");
    time.className = "mono";
    const createdAt = new Date(item.created_at);
    if (!Number.isNaN(createdAt.getTime())) {
      time.dateTime = createdAt.toISOString();
      time.textContent = new Intl.DateTimeFormat("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(createdAt).replace(",", " ·");
    }

    link.append(position, copy, time);
    row.append(link);
    list.append(row);
  });

  count.textContent = String(history.length).padStart(2, "0");
  group.hidden = false;
  section.hidden = false;
}

const browserHistory = readBrowserHistory();
const generatedHistoryData = document.getElementById("anonymous-history-item");
if (generatedHistoryData) {
  try {
    const generatedItem = JSON.parse(generatedHistoryData.textContent);
    const previousItem = browserHistory[0];
    if (
      !previousItem
      || String(previousItem.id) !== String(generatedItem.id)
      || previousItem.media_type !== generatedItem.media_type
    ) {
      browserHistory.unshift(generatedItem);
      browserHistory.splice(browserHistoryLimit);
      writeBrowserHistory(browserHistory);
    }
  } catch (_error) {
    // Um payload invalido nao deve impedir o restante da pagina.
  }
}
renderBrowserHistory(browserHistory);

const streamingLoader = document.querySelector("[data-streaming-loader]");
if (streamingLoader) {
  const streamingUrl = streamingLoader.dataset.streamingUrl;
  const streamingLoaderTemplate = streamingLoader.cloneNode(true);
  let currentStreamingElement = streamingLoader;
  let streamingRequestNumber = 0;

  function replaceStreamingElement(nextElement) {
    currentStreamingElement.replaceWith(nextElement);
    currentStreamingElement = nextElement;
  }

  function renderStreamingEmpty(message, { retryable = false } = {}) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const label = document.createElement("span");
    label.className = "mono";
    label.textContent = "LINK INDISPONÍVEL";
    const copy = document.createElement("p");
    copy.textContent = message || "A Watchmode ainda não possui um link direto para este título no Brasil.";
    empty.append(label, copy);
    if (retryable) {
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "streaming-retry";
      retry.textContent = "Tentar novamente";
      retry.addEventListener("click", loadStreamingLinks);
      empty.append(retry);
    }
    replaceStreamingElement(empty);
  }

  function renderStreamingGroups(groups) {
    const wrapper = document.createElement("div");
    wrapper.className = "provider-groups";
    groups.forEach((group) => {
      if (!group || typeof group.label !== "string" || !Array.isArray(group.providers)) return;
      const section = document.createElement("section");
      section.className = "provider-group";
      const heading = document.createElement("h3");
      heading.textContent = group.label;
      const providers = document.createElement("div");
      providers.className = "providers";
      group.providers.forEach((provider) => {
        if (!provider || typeof provider.web_url !== "string" || typeof provider.provider_name !== "string") return;
        const link = document.createElement("a");
        link.className = "provider";
        link.href = provider.web_url;
        link.target = "_blank";
        link.rel = "noopener";
        link.setAttribute("aria-label", `Abrir no ${provider.provider_name}`);
        if (typeof provider.logo_url === "string" && provider.logo_url) {
          const logo = document.createElement("img");
          logo.src = provider.logo_url;
          logo.alt = `Logo do ${provider.provider_name}`;
          logo.loading = "lazy";
          link.append(logo);
        }
        const copy = document.createElement("span");
        const name = document.createElement("strong");
        name.textContent = provider.provider_name;
        copy.append(name);
        if (typeof provider.format === "string" && provider.format) {
          const format = document.createElement("small");
          format.textContent = provider.format;
          copy.append(format);
        }
        const icon = document.createElement("i");
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = "↗";
        link.append(copy, icon);
        providers.append(link);
      });
      if (providers.children.length) {
        section.append(heading, providers);
        wrapper.append(section);
      }
    });
    if (wrapper.children.length) {
      wrapper.querySelectorAll(".provider").forEach((provider, index) => {
        provider.style.setProperty("--provider-index", String(index));
      });
      replaceStreamingElement(wrapper);
      window.requestAnimationFrame(() => wrapper.classList.add("is-ready"));
    } else renderStreamingEmpty();
  }

  async function loadStreamingLinks() {
    const requestNumber = ++streamingRequestNumber;
    const loader = streamingLoaderTemplate.cloneNode(true);
    replaceStreamingElement(loader);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 9000);

    try {
      const response = await fetch(streamingUrl, {
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      const data = await response.json();
      if (requestNumber !== streamingRequestNumber) return;
      if (!response.ok && !Array.isArray(data.groups)) {
        throw new Error(data.error || "Não foi possível consultar onde assistir.");
      }
      if (Array.isArray(data.groups) && data.groups.length) {
        renderStreamingGroups(data.groups);
      } else {
        renderStreamingEmpty(data.error);
      }
    } catch (error) {
      if (requestNumber !== streamingRequestNumber) return;
      const timedOut = error?.name === "AbortError";
      renderStreamingEmpty(
        timedOut
          ? "A consulta demorou mais que o esperado. Tente novamente."
          : error.message || "Não foi possível consultar onde assistir.",
        { retryable: true },
      );
    } finally {
      window.clearTimeout(timeout);
    }
  }

  loadStreamingLinks();
}

if (result && window.location.hash !== "#gerador") {
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
      button.classList.remove("is-confirmed");
      window.requestAnimationFrame(() => button.classList.add("is-confirmed"));
      window.setTimeout(() => button.classList.remove("is-confirmed"), 520);

      if (!data.favorited) {
        const mediaType = form.querySelector("[name='media_type']")?.value;
        const tmdbId = form.querySelector("[name='tmdb_id']")?.value;
        document.querySelector(`[data-favorite-card="${mediaType}:${tmdbId}"]`)?.remove();
      }
    } catch (error) {
      if (feedback) feedback.textContent = error.message;
      button.classList.remove("has-error");
      window.requestAnimationFrame(() => button.classList.add("has-error"));
      window.setTimeout(() => button.classList.remove("has-error"), 520);
    } finally {
      button.disabled = false;
    }
  });
});

const revealTargets = [
  ...document.querySelectorAll(".discovery-intro, .discovery-points article, .trends-section .section-head, .how-it-works .section-head, .steps article"),
];

if (revealTargets.length) {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  revealTargets.forEach((element, index) => {
    element.classList.add("motion-reveal");
    element.style.setProperty("--reveal-delay", `${Math.min(index % 3, 2) * 60}ms`);
  });

  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealTargets.forEach((element) => element.classList.add("is-visible"));
  } else {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8%", threshold: 0.12 });
    revealTargets.forEach((element) => revealObserver.observe(element));
  }
}
