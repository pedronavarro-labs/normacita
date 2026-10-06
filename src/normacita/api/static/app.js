// UI mínima sin frameworks. Todo el contenido dinámico se inserta con textContent
// (nunca innerHTML) para evitar XSS aunque la respuesta del modelo contenga HTML.
"use strict";

const form = document.getElementById("ask-form");
const button = form.querySelector("button");
const resultado = document.getElementById("resultado");
const respuesta = document.getElementById("respuesta");
const citas = document.getElementById("citas");
const errorBox = document.getElementById("error");

function el(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  button.disabled = true;
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pregunta: form.pregunta.value }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Pregunta no válida");

    respuesta.textContent = data.respuesta;
    respuesta.className = data.sin_base ? "sin-base" : "";
    citas.replaceChildren();
    for (const c of data.citas) {
      const li = el("li");
      li.value = c.numero;
      const apdo = !c.apartado || c.apartado === "único" ? ""
        : c.articulo.startsWith("Artículo") ? `.${c.apartado}` : `, apdo. ${c.apartado}`;
      const link = el("a", `${c.articulo}${apdo} · ${c.titulo}`);
      // Solo enlazamos a URLs https (defensa adicional ante datos manipulados).
      if (c.url.startsWith("https://")) { link.href = c.url; link.target = "_blank"; link.rel = "noopener noreferrer"; }
      li.append(link, el("blockquote", c.texto));
      citas.append(li);
    }
    resultado.hidden = false;
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  } finally {
    button.disabled = false;
  }
});
