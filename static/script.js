let marcadas = [];
function marcar(numero) {
    if (!marcadas.includes(numero)) {
        marcadas.push(numero);
        document.getElementById("marcadas").textContent = marcadas.length;
        document.getElementById("ultimo").textContent = numero;
        document.getElementById("ultimos").textContent = marcadas.slice(-5).reverse().join(" ");
        document.getElementById("boton-" + numero).classList.add("marcado");

        fetch('/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'numero=' + numero
        });
    }
}

function resetear() {
    marcadas = [];
    document.getElementById("marcadas").textContent = "0";
    document.getElementById("ultimo").textContent = "0";
    document.getElementById("ultimos").textContent = "0";
    document.querySelectorAll(".marcado").forEach(el => el.classList.remove("marcado"));

    fetch('/reset', { method: 'POST' });
}

window.onload = function() {
    const tablero = document.getElementById("tablero");
    for (let i = 1; i <= 75; i++) {
        const btn = document.createElement("button");
        btn.textContent = i;
        btn.id = "boton-" + i;
        btn.className = "numero";
        btn.onclick = () => marcar(i);
        tablero.appendChild(btn);
    }
};