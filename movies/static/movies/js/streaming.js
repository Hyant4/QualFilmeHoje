export function initStreaming() {
  const streamingLoader = document.querySelector("[data-streaming-loader]");
  if (!streamingLoader) return;

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
        if (
          !provider
          || typeof provider.web_url !== "string"
          || typeof provider.provider_name !== "string"
        ) return;
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
    } else {
      renderStreamingEmpty();
    }
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
