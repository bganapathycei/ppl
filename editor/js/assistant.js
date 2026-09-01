const STORAGE_PROVIDER = "ppl-assistant-provider";
const STORAGE_MODEL = "ppl-assistant-model";

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatReply(text) {
  const escaped = escapeHtml(text);
  return escaped.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
    const label = lang ? `<span class="code-lang">${escapeHtml(lang)}</span>` : "";
    return `<pre class="chat-code">${label}<code>${escapeHtml(code.trim())}</code></pre>`;
  });
}

export function initAssistant(root, { getSource, applySource, onStatus }) {
  root.innerHTML = `
    <div class="assistant-head">
      <h2>AI Assistant</h2>
      <p class="assistant-hint">Describe changes in natural language. The assistant returns PPL you can apply to the editor.</p>
    </div>
    <div class="assistant-controls">
      <label class="assistant-field">
        <span>Provider</span>
        <select id="assistant-provider"></select>
      </label>
      <label class="assistant-field">
        <span>Model</span>
        <select id="assistant-model"></select>
      </label>
    </div>
    <div id="assistant-config-note" class="assistant-note" hidden></div>
    <div id="assistant-messages" class="assistant-messages" role="log" aria-live="polite"></div>
    <div id="assistant-apply" class="assistant-apply" hidden>
      <button type="button" id="assistant-apply-btn" class="primary">Apply to editor</button>
      <span id="assistant-apply-note" class="assistant-apply-note"></span>
    </div>
    <form id="assistant-form" class="assistant-form">
      <textarea id="assistant-input" rows="3" placeholder="Ask to create or edit a PPL program…" spellcheck="true"></textarea>
      <div class="assistant-form-actions">
        <button type="submit" id="assistant-send" class="primary">Send</button>
        <button type="button" id="assistant-clear">Clear chat</button>
      </div>
    </form>
  `;

  const providerSelect = root.querySelector("#assistant-provider");
  const modelSelect = root.querySelector("#assistant-model");
  const configNote = root.querySelector("#assistant-config-note");
  const messagesEl = root.querySelector("#assistant-messages");
  const applyBar = root.querySelector("#assistant-apply");
  const applyBtn = root.querySelector("#assistant-apply-btn");
  const applyNote = root.querySelector("#assistant-apply-note");
  const form = root.querySelector("#assistant-form");
  const input = root.querySelector("#assistant-input");
  const clearBtn = root.querySelector("#assistant-clear");

  let config = null;
  let chatHistory = [];
  let pendingPpl = null;
  let pendingValid = false;

  function setStatus(text, level = "") {
    if (onStatus) onStatus(text, level);
  }

  function loadPrefs() {
    try {
      return {
        provider: localStorage.getItem(STORAGE_PROVIDER) || "",
        model: localStorage.getItem(STORAGE_MODEL) || "",
      };
    } catch {
      return { provider: "", model: "" };
    }
  }

  function savePrefs(provider, model) {
    try {
      localStorage.setItem(STORAGE_PROVIDER, provider);
      localStorage.setItem(STORAGE_MODEL, model);
    } catch {
      // quota / private mode
    }
  }

  function selectedProvider() {
    return config?.providers?.find((item) => item.id === providerSelect.value);
  }

  function populateModels(providerId) {
    const provider = config?.providers?.find((item) => item.id === providerId);
    modelSelect.innerHTML = "";
    if (!provider) return;
    for (const model of provider.models) {
      const option = document.createElement("option");
      option.value = model.id;
      option.textContent = model.label;
      modelSelect.appendChild(option);
    }
    const prefs = loadPrefs();
    if (prefs.model && provider.models.some((item) => item.id === prefs.model)) {
      modelSelect.value = prefs.model;
    } else {
      modelSelect.value = provider.default_model || provider.models[0]?.id || "";
    }
  }

  function updateConfigNote() {
    const provider = selectedProvider();
    if (!provider) {
      configNote.hidden = true;
      return;
    }
    if (provider.configured) {
      configNote.hidden = true;
      return;
    }
    configNote.hidden = false;
    configNote.textContent =
      `${provider.label} is not configured. Set API keys in your environment (see editor README).`;
  }

  function renderMessages() {
    messagesEl.innerHTML = chatHistory
      .map(
        (item) => `
          <div class="chat-msg chat-${item.role}">
            <div class="chat-role">${item.role === "user" ? "You" : "Assistant"}</div>
            <div class="chat-body">${item.role === "assistant" ? formatReply(item.content) : escapeHtml(item.content)}</div>
          </div>`
      )
      .join("");
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showApply(pplSource, valid, error) {
    pendingPpl = pplSource;
    pendingValid = valid;
    if (!pplSource) {
      applyBar.hidden = true;
      return;
    }
    applyBar.hidden = false;
    applyBtn.disabled = !valid;
    applyNote.textContent = valid ? "Valid PPL — safe to apply" : error || "Invalid PPL";
    applyNote.className = "assistant-apply-note" + (valid ? " ok" : " err");
  }

  async function loadConfig() {
    try {
      const res = await fetch("/api/assistant/config");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      config = await res.json();
    } catch {
      config = null;
      providerSelect.innerHTML = `<option value="">Server required</option>`;
      modelSelect.innerHTML = "";
      configNote.hidden = false;
      configNote.textContent = "Start python editor/serve.py to use the AI assistant.";
      return;
    }

    providerSelect.innerHTML = "";
    for (const provider of config.providers) {
      const option = document.createElement("option");
      option.value = provider.id;
      const suffix = provider.configured ? "" : " (not configured)";
      option.textContent = `${provider.label}${suffix}`;
      providerSelect.appendChild(option);
    }

    const prefs = loadPrefs();
    const defaultProvider = prefs.provider || config.default_provider;
    if (config.providers.some((item) => item.id === defaultProvider)) {
      providerSelect.value = defaultProvider;
    }
    populateModels(providerSelect.value);
    updateConfigNote();
  }

  providerSelect.addEventListener("change", () => {
    populateModels(providerSelect.value);
    savePrefs(providerSelect.value, modelSelect.value);
    updateConfigNote();
  });

  modelSelect.addEventListener("change", () => {
    savePrefs(providerSelect.value, modelSelect.value);
  });

  applyBtn.addEventListener("click", () => {
    if (!pendingPpl || !pendingValid) return;
    try {
      applySource(pendingPpl);
      setStatus("Applied assistant program to editor", "ok");
      showApply(null, false, null);
    } catch (err) {
      setStatus(String(err.message || err), "err");
    }
  });

  clearBtn.addEventListener("click", () => {
    chatHistory = [];
    pendingPpl = null;
    showApply(null, false, null);
    renderMessages();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    if (!config?.ok) {
      setStatus("AI assistant requires python editor/serve.py", "err");
      return;
    }

    chatHistory.push({ role: "user", content: text });
    input.value = "";
    renderMessages();
    showApply(null, false, null);

    const sendBtn = root.querySelector("#assistant-send");
    sendBtn.disabled = true;
    sendBtn.textContent = "Thinking…";

    try {
      const res = await fetch("/api/assistant/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: chatHistory,
          provider: providerSelect.value,
          model: modelSelect.value,
          current_source: getSource(),
        }),
      });
      const body = await res.json();
      if (!body.ok) {
        chatHistory.push({ role: "assistant", content: body.error || "Request failed" });
        setStatus(body.error || "Assistant request failed", "err");
      } else {
        chatHistory.push({ role: "assistant", content: body.reply || "" });
        savePrefs(providerSelect.value, modelSelect.value);
        showApply(body.ppl_source, body.ppl_valid, body.ppl_error);
        if (body.ppl_source && body.ppl_valid) {
          setStatus("Assistant proposed valid PPL — click Apply to editor", "ok");
        } else {
          setStatus("Assistant replied", "ok");
        }
      }
      renderMessages();
    } catch (err) {
      chatHistory.push({ role: "assistant", content: String(err.message || err) });
      renderMessages();
      setStatus(String(err.message || err), "err");
    } finally {
      sendBtn.disabled = false;
      sendBtn.textContent = "Send";
    }
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  loadConfig();
}
