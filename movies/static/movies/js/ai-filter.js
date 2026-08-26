class FilterRequestError extends Error {}

function setStatus(status, message, state) {
  if (!status) return;
  status.textContent = message;
  status.dataset.state = state;
}

function setMessage(element, message) {
  if (!element) return;
  element.textContent = message;
  element.hidden = !message;
}

async function responsePayload(response) {
  try {
    return await response.json();
  } catch (_error) {
    return {};
  }
}

export function initAiFilter() {
  const root = document.querySelector("[data-ai-filter]");
  if (!root) return;

  const form = root.querySelector("[data-ai-filter-form]");
  const input = root.querySelector("[data-ai-filter-input]");
  const button = root.querySelector("[data-ai-filter-submit]");
  const label = root.querySelector("[data-ai-filter-label]");
  const status = root.querySelector("[data-ai-filter-status]");
  const userMessage = root.querySelector("[data-ai-filter-user-message]");
  const reply = root.querySelector("[data-ai-filter-reply]");
  const promptButtons = [...root.querySelectorAll("[data-ai-filter-prompt]")];
  const initialLabel = label?.textContent || "Aplicar ao filtro";

  function submitPrompt(prompt) {
    if (!input || !form) return;
    input.value = prompt;
    form.requestSubmit();
  }

  promptButtons.forEach((promptButton) => {
    promptButton.addEventListener("click", () => {
      submitPrompt(promptButton.dataset.aiFilterPrompt || "");
    });
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input?.value.trim() || "";
    if (!text) {
      setStatus(status, "Escreva uma preferência antes de enviar.", "error");
      input?.focus();
      return;
    }

    const csrfToken = document.querySelector(
      '[data-generator-form] input[name="csrfmiddlewaretoken"]',
    )?.value;
    if (!csrfToken || !root.dataset.aiFilterUrl) {
      setStatus(status, "O filtro por IA não está disponível agora.", "error");
      return;
    }

    setMessage(userMessage, text);
    setMessage(reply, "");
    button.disabled = true;
    promptButtons.forEach((promptButton) => {
      promptButton.disabled = true;
    });
    root.classList.add("is-busy");
    if (label) label.textContent = "Lendo o clima";
    setStatus(status, "Gemini está preparando seus critérios…", "loading");

    try {
      const response = await fetch(root.dataset.aiFilterUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ texto: text }),
      });
      const payload = await responsePayload(response);
      if (!response.ok) {
        throw new FilterRequestError(
          typeof payload.error === "string"
            ? payload.error
            : "Não foi possível analisar suas preferências.",
        );
      }
      if (
        !payload
        || typeof payload.filters !== "object"
        || Array.isArray(payload.filters)
      ) {
        throw new FilterRequestError("A resposta do filtro não pôde ser usada.");
      }

      document.dispatchEvent(
        new CustomEvent("qualfilmehoje:apply-ai-filter", {
          detail: { filters: payload.filters },
        }),
      );
      const count = Array.isArray(payload.applied_fields)
        ? payload.applied_fields.length
        : 0;
      const message = count
        ? `Pronto. Atualizei ${count} critério${count === 1 ? "" : "s"} para você revisar.`
        : "Não encontrei critérios específicos. Você pode ajustar manualmente.";
      setMessage(reply, message);
      setStatus(status, "Critérios atualizados nos controles abaixo.", "success");
      if (input) input.value = "";
    } catch (error) {
      const message = error instanceof FilterRequestError
        ? error.message
        : "Não foi possível analisar agora. Ajuste os filtros manualmente.";
      setMessage(reply, message);
      setStatus(status, message, "error");
    } finally {
      button.disabled = false;
      promptButtons.forEach((promptButton) => {
        promptButton.disabled = false;
      });
      root.classList.remove("is-busy");
      if (label) label.textContent = initialLabel;
    }
  });
}
