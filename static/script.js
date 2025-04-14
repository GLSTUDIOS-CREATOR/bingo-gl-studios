
let marcados = [];
let ultimo = "-";
let ultimos = [];

window.onload = function () {
  const tablero = document.getElementById("tablero");
  for (let i = 1; i <= 75; i++) {
    const btn = document.createElement("button");
    btn.className = "numero";
    btn.innerText = i;
    btn.onclick = () => marcar(i, btn);
    tablero.appendChild(btn);
  }
};

function marcar(numero, btn) {
  if (!marcados.includes(numero)) {
    marcados.push(numero);
    btn.classList.add("marcado");

    // actualizar últimos números
    ultimo = numero;
    ultimos.unshift(numero);
    if (ultimos.length > 5) ultimos.pop();

    actualizarVista();

    fetch('/guardar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ numero })
    }).catch(console.error);
  }
}

function resetear() {
  marcados = [];
  ultimo = "-";
  ultimos = [];
  document.querySelectorAll(".numero").forEach(b => b.classList.remove("marcado"));
  actualizarVista();

  fetch('/reset', { method: 'POST' }).catch(console.error);
}

function actualizarVista() {
  document.getElementById("contador").innerText = "Balotas marcadas: " + marcados.length;
  document.getElementById("ultimo").innerText = "Último número: " + ultimo;
  document.getElementById("ultimos").innerText = "Últimos 5 números: " + (ultimos.join(" ") || "-");
}
