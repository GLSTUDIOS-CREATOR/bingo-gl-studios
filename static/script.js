
window.onload = () => {
  const container = document.getElementById("numeros-container");
  for (let i = 1; i <= 75; i++) {
    const boton = document.createElement("button");
    boton.textContent = i;
    boton.className = "balota";
    boton.onclick = () => marcarNumero(i);
    container.appendChild(boton);
  }
};

function marcarNumero(numero) {
  fetch('/guardar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `numero=${numero}`
  }).then(() => location.reload());
}

function resetear() {
  fetch('/resetear', { method: 'POST' }).then(() => location.reload());
}
