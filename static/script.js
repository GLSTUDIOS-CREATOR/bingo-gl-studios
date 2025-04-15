
let ultimo = "";
let ultimos = [];

function marcar(numero) {
    fetch("/guardar", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "numero=" + numero
    }).then(() => location.reload());
}

function resetear() {
    fetch("/resetear", { method: "POST" }).then(() => location.reload());
}
