
async function resetear() {
    await fetch('/resetear', { method: 'POST' });
    location.reload();
}
