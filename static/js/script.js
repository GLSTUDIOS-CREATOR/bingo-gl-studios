let marcadas = [];
let ultimos5 = [];
let segundos = 0;
let timer;
let juegoIniciado = false;
let juegoFinalizado = false;

document.addEventListener("DOMContentLoaded", () => {
  const tablero = document.getElementById("tablero");
  const btnIniciar = document.getElementById("btnIniciar");
  const btnFinalizar = document.getElementById("btnFinalizar");

  // Crear las 75 balotas
  for (let i = 1; i <= 75; i++) {
    const bola = document.createElement("div");
    bola.classList.add("balota");
    bola.textContent = i;
    bola.dataset.numero = i;

    bola.addEventListener("click", () => {
      if (!juegoIniciado || juegoFinalizado) {
        alert("Debes iniciar el juego primero.");
        return;
      }
      marcarBalota(bola, i);
    });

    tablero.appendChild(bola);
  }

  // INICIAR
  btnIniciar.addEventListener("click", () => {
    if (!juegoIniciado) {
      juegoIniciado = true;
      btnIniciar.textContent = "✅ JUEGO EN CURSO";
      btnIniciar.disabled = true;
      btnFinalizar.disabled = false;
      iniciarContador();
    }
  });

  // FINALIZAR
  btnFinalizar.addEventListener("click", () => {
    if (juegoIniciado) {
      clearInterval(timer);
      juegoFinalizado = true;
      btnFinalizar.textContent = "🛑 JUEGO FINALIZADO";
      btnFinalizar.disabled = true;
      mostrarUltimaBalota();
    }
  });

  // RESET
  const btnReset = document.getElementById("btnReset");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      if (confirm("¿Estás seguro de que deseas reiniciar el juego?")) {
        fetch('/reset_juego', {
          method: 'POST'
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            location.reload();  // Recarga el panel
          } else {
            alert("Error al resetear el juego");
          }
        });
      }
    });
  }

  // STINGER
  const ultimaBalotaEl = document.getElementById("ultimaBalota");
  if (ultimaBalotaEl) {
    ultimaBalotaEl.addEventListener("click", () => {
      const numero = ultimaBalotaEl.textContent;
      if (!isNaN(parseInt(numero))) {
        fetch('/activar_stinger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ numero: numero })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("✅ Stinger activado con número: " + numero);
          } else {
            alert("Error al activar stinger");
          }
        });
      }
    });
  }

  // AGREGAR FIGURA AL DÍA
  document.querySelectorAll('.boton-agregar-dia').forEach(btn => {
    btn.addEventListener('click', function() {
      const nombre = this.parentNode.querySelector('.nombre').textContent;
      fetch('/agregar_figura_dia', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: nombre })
      }).then(res => res.json()).then(data => {
        if (data.success) {
          alert("Figura agregada correctamente");
        }
      });
    });
  });

});

// ===== FUNCIONES =====

function marcarBalota(bola, numero) {
  const num = parseInt(numero);

  if (!marcadas.includes(num)) {
    fetch('/marcar_balota', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ numero: num })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        bola.classList.add("marcada");
        marcadas.push(num);
        ultimos5.unshift(num);
        if (ultimos5.length > 5) ultimos5.pop();

        actualizarContadores();
        resetContador();
      } else {
        alert("Error al marcar la balota");
      }
    });
  }
}

function actualizarContadores() {
  document.getElementById("totalMarcadas").textContent = marcadas.length;
  document.getElementById("ultimos5").textContent = ultimos5.join(", ");

  const ultima = ultimos5[0] || "–";
  document.getElementById("ultimaBalota").textContent = ultima;
}

function iniciarContador() {
  timer = setInterval(() => {
    segundos++;
    document.getElementById("contadorSegundos").textContent = segundos;
  }, 1000);
}

function resetContador() {
  segundos = 0;
}

function mostrarUltimaBalota() {
  const ultima = ultimos5[0] || "–";
  const balotaFinal = document.getElementById("balotaFinal");
  if (balotaFinal) {
    balotaFinal.textContent = ultima;
  }
}

// ==== ELIMINAR FIGURA DEL DÍA ====
function eliminarFiguraDelDia(nombre) {
  if (!confirm('¿Seguro que quieres quitar la figura "' + nombre + '"?')) return;
  fetch('/eliminar_figura_dia', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre: nombre })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      alert("No se pudo quitar la figura");
    }
  });
}

function eliminarFiguraDelDia(nombre) {
    if (!confirm('¿Eliminar la figura "' + nombre + '" del día?')) return;
    fetch('/eliminar_figura_dia', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: nombre })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Figura eliminada correctamente.");
            location.reload();
        } else {
            alert("Error: " + (data.error || ""));
        }
    });
}

function eliminarFiguraDelDia(nombre) {
  if (!confirm('¿Eliminar la figura "' + nombre + '" del día?')) return;
  fetch('/eliminar_figura_dia', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre: nombre })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("Figura eliminada correctamente.");
      location.reload();
    } else {
      alert("Error: " + (data.error || ""));
    }
  });
}

