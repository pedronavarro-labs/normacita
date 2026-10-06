// NormaCita · UI sin frameworks.
// Seguridad: TODO el contenido que llega del servidor (respuesta del modelo, textos del BOE)
// se inserta con textContent / createElement, nunca con innerHTML, para evitar XSS.
// Sin scripts ni estilos en línea: compatible con la CSP "default-src 'self'".
"use strict";

const MIN = 3;
const MAX = 500;
const $ = (id) => document.getElementById(id);

const form = $("ask-form");
const textarea = $("pregunta");
const submitBtn = $("enviar");
const counter = $("contador");
const status = $("estado");
const panels = {
  cargando: $("cargando"),
  resultado: $("resultado"),
  sinBase: $("sin-base"),
  error: $("error"),
};
let lastQuestion = "";

function el(tag, { text, className, attrs } = {}) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  if (attrs) for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

/** "Artículo 4.2", "ITC-BT-25, apdo. 2.3.1" o "ITC-BT-01 · Aislamiento reforzado". */
function referencia(c) {
  if (!c.apartado || c.apartado === "único") return c.articulo;
  if (c.articulo.startsWith("Artículo")) return `${c.articulo}.${c.apartado}`;
  return /^\d/.test(c.apartado) ? `${c.articulo}, apdo. ${c.apartado}` : `${c.articulo} · ${c.apartado}`;
}

function safeUrl(url) {
  // Solo enlazamos a https (defensa adicional ante datos manipulados).
  try {
    const u = new URL(url);
    return u.protocol === "https:" ? u.href : null;
  } catch {
    return null;
  }
}

function showOnly(name) {
  for (const [key, node] of Object.entries(panels)) node.hidden = key !== name;
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  submitBtn.classList.toggle("is-loading", loading);
  submitBtn.querySelector(".btn-label").textContent = loading ? "Buscando…" : "Preguntar";
  form.setAttribute("aria-busy", String(loading));
}

function setFieldError(msg) {
  const box = $("pregunta-error");
  box.textContent = msg;
  box.hidden = !msg;
  if (msg) textarea.setAttribute("aria-invalid", "true");
  else textarea.removeAttribute("aria-invalid");
}

function updateCounter() {
  counter.textContent = `${textarea.value.length}/${MAX}`;
}

// ---------- Citas ----------

function toggleCita(n, forceOpen = false) {
  const chip = document.querySelector(`.chip-cita[data-n="${n}"]`);
  const detail = $(`cita-${n}`);
  if (!chip || !detail) return;
  const open = forceOpen || chip.getAttribute("aria-expanded") !== "true";
  chip.setAttribute("aria-expanded", String(open));
  detail.hidden = !open;
  if (open && forceOpen) detail.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderAnswer(texto, numeros) {
  const p = $("respuesta");
  p.replaceChildren();
  // Divide por marcadores [n]; solo los que corresponden a una cita real se convierten en botón.
  for (const part of texto.split(/(\[\d+\])/)) {
    const m = part.match(/^\[(\d+)\]$/);
    if (m && numeros.has(Number(m[1]))) {
      const n = Number(m[1]);
      const btn = el("button", {
        text: String(n),
        className: "cite-ref",
        attrs: { type: "button", "aria-controls": `cita-${n}`, "aria-label": `Ver cita ${n}` },
      });
      btn.addEventListener("click", () => toggleCita(n, true));
      p.append(btn);
    } else if (part) {
      p.append(document.createTextNode(part));
    }
  }
}

function renderCitas(citas) {
  const lista = $("citas");
  const detalles = $("detalles");
  lista.replaceChildren();
  detalles.replaceChildren();
  for (const c of citas) {
    const ref = referencia(c);
    const chip = el("button", {
      className: "chip chip-cita",
      attrs: { type: "button", "data-n": String(c.numero), "aria-expanded": "false", "aria-controls": `cita-${c.numero}` },
    });
    chip.append(el("span", { text: `Cita ${c.numero}: `, className: "sr-only" }));
    chip.append(el("span", { text: String(c.numero), className: "chip-num", attrs: { "aria-hidden": "true" } }));
    chip.append(el("span", { text: ref }));
    chip.addEventListener("click", () => toggleCita(c.numero));
    const li = el("li");
    li.append(chip);
    lista.append(li);

    const detail = el("article", {
      className: "source-detail",
      attrs: { id: `cita-${c.numero}`, "aria-label": `Cita ${c.numero}: ${ref}` },
    });
    detail.hidden = true;
    detail.append(el("h4", { text: `[${c.numero}] ${ref} — ${c.titulo}` }));
    detail.append(el("p", { text: c.norma, className: "source-norma" }));
    detail.append(el("blockquote", { text: c.texto }));
    const url = safeUrl(c.url);
    if (url) {
      const a = el("a", {
        text: "Ver en el BOE (texto consolidado) ↗",
        className: "source-link",
        attrs: { href: url, target: "_blank", rel: "noopener noreferrer" },
      });
      detail.append(a);
    }
    detalles.append(detail);
  }
  $("fuentes").hidden = citas.length === 0;
}

// ---------- Envío ----------

async function ask(pregunta) {
  lastQuestion = pregunta;
  showOnly("cargando");
  setLoading(true);
  status.textContent = "Buscando en el REBT…";
  try {
    let res;
    try {
      res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pregunta }),
      });
    } catch {
      throw new Error("No se ha podido conectar con el servidor. Comprueba tu conexión e inténtalo de nuevo.");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 422) throw new Error(`La pregunta debe tener entre ${MIN} y ${MAX} caracteres.`);
      throw new Error(typeof data.detail === "string" ? data.detail : "Error inesperado del servidor.");
    }

    if (data.sin_base) {
      $("sin-base-pregunta").textContent = pregunta;
      showOnly("sinBase");
      status.textContent = "Sin base en la norma para esta pregunta.";
      panels.sinBase.focus();
      return;
    }
    $("pregunta-eco").textContent = `«${pregunta}»`;
    renderAnswer(data.respuesta, new Set(data.citas.map((c) => c.numero)));
    renderCitas(data.citas);
    showOnly("resultado");
    status.textContent = `Respuesta lista con ${data.citas.length} cita(s).`;
    panels.resultado.focus();
  } catch (err) {
    $("error-msg").textContent = err.message;
    showOnly("error");
    status.textContent = "";
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const pregunta = textarea.value.trim();
  if (pregunta.length < MIN || pregunta.length > MAX) {
    setFieldError(`Escribe una pregunta de entre ${MIN} y ${MAX} caracteres.`);
    textarea.focus();
    return;
  }
  setFieldError("");
  ask(pregunta);
});

textarea.addEventListener("input", () => {
  updateCounter();
  if (textarea.hasAttribute("aria-invalid")) setFieldError("");
});
textarea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    form.requestSubmit();
  }
});

for (const chip of document.querySelectorAll(".chip-example")) {
  chip.addEventListener("click", () => {
    textarea.value = chip.textContent.trim();
    updateCounter();
    form.requestSubmit();
  });
}

$("reintentar").addEventListener("click", () => {
  if (lastQuestion) ask(lastQuestion);
  else textarea.focus();
});

// Insignia "Modo demo" si el backend usa el proveedor fake (sin LLM).
fetch("/health")
  .then((r) => (r.ok ? r.json() : null))
  .then((h) => {
    if (h && h.proveedor === "fake") $("demo-badge").hidden = false;
  })
  .catch(() => {});

updateCounter();
