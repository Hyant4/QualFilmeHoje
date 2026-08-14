const STORAGE_KEY = "qualfilmehoje:history:v1";
const HISTORY_LIMIT = 8;

export function normaliseBrowserHistory(value) {
  if (!Array.isArray(value)) return [];
  return value.filter((item) => (
    item
    && Number.isSafeInteger(Number(item.id))
    && ["movie", "tv"].includes(item.media_type)
    && typeof item.title === "string"
    && typeof item.detail_url === "string"
    && item.detail_url.startsWith("/titulo/")
  )).slice(0, HISTORY_LIMIT);
}

function readBrowserHistory() {
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "[]");
    return normaliseBrowserHistory(value);
  } catch (_error) {
    return [];
  }
}

function writeBrowserHistory(history) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, HISTORY_LIMIT)));
  } catch (_error) {
    // Navegação privada ou armazenamento indisponível não bloqueiam o sorteio.
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

export function initBrowserHistory() {
  const history = readBrowserHistory();
  const generatedHistoryData = document.getElementById("anonymous-history-item");
  if (generatedHistoryData) {
    try {
      const generatedItem = JSON.parse(generatedHistoryData.textContent);
      const previousItem = history[0];
      if (
        !previousItem
        || String(previousItem.id) !== String(generatedItem.id)
        || previousItem.media_type !== generatedItem.media_type
      ) {
        history.unshift(generatedItem);
        history.splice(HISTORY_LIMIT);
        writeBrowserHistory(history);
      }
    } catch (_error) {
      // Um payload inválido não deve impedir o restante da página.
    }
  }
  renderBrowserHistory(history);
}
