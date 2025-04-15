
document.addEventListener("DOMContentLoaded", () => {
    const panel = document.getElementById("panel-numeros");
    const contador = document.getElementById("contador");
    const ultimo = document.getElementById("ultimo");
    const ultimos5 = document.getElementById("ultimos5");
    let marcados = [];

    for (let i = 1; i <= 75; i++) {
        const btn = document.createElement("button");
        btn.className = "numero";
        btn.textContent = i;
        btn.onclick = () => marcarNumero(i, btn);
        panel.appendChild(btn);
    }

    function marcarNumero(num, btn) {
        if (!marcados.includes(num)) {
            marcados.push(num);
            btn.classList.add("activo");
            fetch("/guardar", {
                method: "POST",
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `numero=${num}`
            });
        }
        actualizarVista();
    }

    function actualizarVista() {
        contador.textContent = "Balotas marcadas: " + marcados.length;
        ultimo.textContent = "Último número: " + (marcados.at(-1) || 0);
        ultimos5.textContent = "Últimos 5 números: " + marcados.slice(-5).reverse().join(" ");
    }

    window.resetear = function () {
        marcados = [];
        document.querySelectorAll(".numero").forEach(b => b.classList.remove("activo"));
        fetch("/resetear").then(() => {
            contador.textContent = "Balotas marcadas: 0";
            ultimo.textContent = "Último número: 0";
            ultimos5.textContent = "Últimos 5 números: -";
        });
    }
});
