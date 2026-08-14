export function initFavorites() {
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
        if (!response.ok) {
          throw new Error(data.error || "Não foi possível atualizar a minha lista.");
        }

        button.setAttribute("aria-pressed", String(data.favorited));
        if (icon) icon.textContent = data.favorited ? "★" : "☆";
        if (label) {
          label.textContent = data.favorited ? "Na minha lista" : "Adicionar à minha lista";
        }
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
}
