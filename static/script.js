document.addEventListener("DOMContentLoaded", () => {
    const tablero = document.getElementById("tablero");
    const contador = document.getElementById("contador");
    const ultimo = document.getElementById("ultimo-numero");
    const ultimos = document.getElementById("ultimos-cinco");

    let marcados = [];
    
    for (let i = 1; i <= 75; i++) {
        const btn = document.createElement("button");
        btn.textContent = i;
        btn.className = "balota";
        btn.onclick = () => marcarNumero(i);
        tablero.appendChild(btn);
    }

    function marcarNumero(num) {
        fetch("/guardar", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "numero=" + num
        }).then(res => {
            if (res.ok) {
                marcados.push(num);
                if (marcados.length > 5) marcados.shift();
                contador.textContent = "Balotas marcadas: " + marcados.length;
                ultimo.textContent = "Último número: " + num;
                ultimos.textContent = "Últimos 5 números: " + marcados.slice(-5).reverse().join(" ");
            }
        });
    }

    window.resetearPanel = () => {
        location.reload();
    };
});
