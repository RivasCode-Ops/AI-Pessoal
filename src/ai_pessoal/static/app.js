async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function el(id) {
  return document.getElementById(id);
}

function addBubble(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = text;
  el("chatLog").appendChild(div);
  el("chatLog").scrollTop = el("chatLog").scrollHeight;
}

async function loadStatus() {
  try {
    const h = await api("/api/health");
    const ollama = h.ollama ? "Ollama OK" : "Ollama offline";
    const proj = h.active_project ? ` · projeto: ${h.active_project}` : "";
    el("status").textContent = `${ollama} · ${h.model}${proj}`;
    if (h.active_project) el("activeProject").value = h.active_project;
  } catch {
    el("status").textContent = "API indisponível — rode python -m ai_pessoal.web";
  }
}

el("btnActiveProject").onclick = async () => {
  const name = el("activeProject").value.trim();
  if (!name) return;
  await api("/api/active-project", {
    method: "PUT",
    body: JSON.stringify({ name }),
  });
  loadStatus();
};

el("btnClearProject").onclick = async () => {
  await api("/api/active-project", {
    method: "PUT",
    body: JSON.stringify({ name: null }),
  });
  el("activeProject").value = "";
  loadStatus();
};

async function loadRecent() {
  const items = await api("/api/captures?limit=15");
  const ul = el("recentList");
  ul.innerHTML = "";
  items.forEach((it) => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${it.type_label}</strong> ${it.body.slice(0, 80)}`;
    ul.appendChild(li);
  });
}

el("btnCapture").onclick = async () => {
  const text = el("captureInput").value.trim();
  if (!text) return;
  try {
    const r = await api("/api/capture", { method: "POST", body: JSON.stringify({ text }) });
    el("captureMsg").textContent = `✓ ${r.type} gravado`;
    el("captureInput").value = "";
    loadRecent();
  } catch (e) {
    el("captureMsg").textContent = e.message;
  }
};

el("btnChat").onclick = async () => {
  const message = el("chatInput").value.trim();
  if (!message) return;
  el("chatInput").value = "";
  addBubble("user", message);
  try {
    const r = await api("/api/chat", { method: "POST", body: JSON.stringify({ message }) });
    let text = r.reply;
    if (r.sources?.length) {
      const refs = r.sources
        .slice(0, 4)
        .map((s) => `[${s.type}] ${s.body.slice(0, 50)}…`)
        .join(" · ");
      text += `\n\n— Baseado em: ${refs}`;
    }
    addBubble("assistant", text);
  } catch (e) {
    addBubble("assistant", `Erro: ${e.message}`);
  }
};

el("chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") el("btnChat").click();
});

el("btnSearch").onclick = async () => {
  const raw = el("searchInput").value.trim();
  let q = raw;
  let project = "";
  if (raw.toLowerCase().startsWith("projeto:")) {
    project = raw.split(":").slice(1).join(":").trim();
    q = "";
  }
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (project) params.set("project", project);
  const items = await api(`/api/search?${params}`);
  const ul = el("searchResults");
  ul.innerHTML = "";
  items.forEach((it) => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${it.type}</strong> ${it.body.slice(0, 100)}`;
    ul.appendChild(li);
  });
};

el("btnProfile").onclick = async () => {
  const r = await api("/api/profile");
  el("profileOut").textContent = r.markdown.replace(/^# /gm, "").replace(/\*\*/g, "");
};

el("btnRelated").onclick = async () => {
  const raw = el("relatedInput").value.trim();
  if (!raw) return;
  const params = new URLSearchParams();
  if (raw.includes("-") && /\d{8}-/.test(raw)) params.set("id", raw);
  else params.set("project", raw);
  const r = await api(`/api/related?${params}`);
  el("relatedOut").textContent = r.markdown.replace(/\*\*/g, "");
};

el("btnRefresh").onclick = loadRecent;

loadStatus();
loadRecent();
