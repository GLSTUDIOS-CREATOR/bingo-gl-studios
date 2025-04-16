
async function resetear() {
    const response = await fetch('/reset', { method: 'POST' });
    if (response.ok) {
        alert("Reset completo.");
        location.reload();
    }
}
