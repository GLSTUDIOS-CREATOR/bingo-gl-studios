// =================== VARIABLES DE ESTADO ===================
let marcadas = [];
let ultimos5 = [];
let segundos = 0;
let timer;
let juegoIniciado = false;
let juegoFinalizado = false;
let balotaUltima = null;

// =================== INICIALIZACIÓN ===================
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
        fetch('/reset_juego', { method: 'POST' })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              location.reload();
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

  // ====== BOTÓN DE PRUEBA: MODAL GANADOR ======
  var btn = document.getElementById("verGanador");
  if (btn) {
    btn.onclick = function() {
      mostrarModalGanador(
        "B-100",
        "CRUZ DE ORO",
        500,
        [2, 17, 34, 54, 73],
        [
          7, 21, 31, 41, 65,
          13, 22, 35, 44, 68,
          2, 17, 0, 54, 73,
          8, 28, 39, 51, 66,
          12, 19, 34, 49, 75
        ],
        [2, 17, 34, 54, 73],
        73
      );
    }
  }
});

// ================= FUNCIONES DE JUEGO =================

function marcarBalota(bola, numero) {
  const num = parseInt(numero);

  if (bola.classList.contains("balota-cargando") || bola.classList.contains("marcada")) return;

  bola.classList.add("balota-cargando");

  fetch('/marcar_balota', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ numero: num })
  })
  .then(res => res.json())
  .then(data => {
    bola.classList.remove("balota-cargando");

    if (data.success) {
      if (data.balotas_marcadas) {
        document.querySelectorAll('.balota').forEach(b => {
          const n = parseInt(b.getAttribute('data-numero'));
          if (data.balotas_marcadas.includes(String(n)) || marcadas.includes(n)) {
            b.classList.add('marcada');
          } else {
            b.classList.remove('marcada');
          }
          b.classList.remove('ultima-marcada');
        });
      }

      if (balotaUltima) balotaUltima.classList.remove('ultima-marcada');
      bola.classList.remove('marcada');
      bola.classList.add('ultima-marcada');
      balotaUltima = bola;

      if (!marcadas.includes(num)) marcadas.push(num);
      ultimos5.unshift(num);
      if (ultimos5.length > 5) ultimos5.pop();

      actualizarContadores();
      resetContador();

      if (data.ganador) {
  mostrarModalGanador(
    data.ganador.boleto,                  // Boleto ganador
    data.ganador.figura,                  // Nombre de la figura (ej: "Cartón Lleno")
    data.ganador.valor,                   // Valor del premio
    data.ganador.numeros,                 // Números de la figura ganadora
    data.ganador.casillas_boleto,         // Cartón completo (array de 25)
    marcadas,                             // Números marcados actualmente
    data.ganador.ultimo_numero            // Último número marcado que completó la figura
  );
}


    } else {
      alert("Error al marcar la balota");
    }
  })
  .catch(() => {
    bola.classList.remove("balota-cargando");
    alert("Error al marcar la balota");
  });
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
  document.getElementById("contadorSegundos").textContent = segundos;
}

function mostrarUltimaBalota() {
  const ultima = ultimos5[0] || "–";
  const balotaFinal = document.getElementById("balotaFinal");
  if (balotaFinal) {
    balotaFinal.textContent = ultima;
  }
}

fetch('/resetear_numeros_marcados', {method: "POST"})
  .then(r => r.json())
  .then(data => {
      if(data.success) {
          // Limpia todos los estados visuales
          document.querySelectorAll(".balota").forEach(b => b.classList.remove("marcada"));
          document.getElementById("totalMarcadas").textContent = "0";
          document.getElementById("ultimos5").textContent = "–";
          document.getElementById("ultimaBalota").textContent = "–";
          // ... y cualquier otro contador o área...
      }
  });

// ========== MODAL GANADOR GL STUDIOS ==========

function svgEstrella() {
  return `<svg viewBox="0 0 50 50" class="estrella" xmlns="http://www.w3.org/2000/svg">
    <polygon fill="#ffc84a" stroke="#bb9013" stroke-width="2"
      points="25,4 31,19 47,19 34,29 39,44 25,35 11,44 16,29 3,19 19,19"/>
  </svg>`;
}

function armarCartonHTML(carton, marcados = [], figura = [], ultimaBalota = null) {
  let html = '<div class="carton-ganador">';
  for (let fila = 0; fila < 5; fila++) {
    html += '<div class="carton-fila">';
    for (let col = 0; col < 5; col++) {
      const idx = fila * 5 + col;
      const num = carton[idx];
      const isFigura = figura.includes(idx);
      const isMarcado = marcados.includes(num);
      const isUltima = num === ultimaBalota;
      let celdaClass = 'carton-celda';
      if (fila === 2 && col === 2) {
        celdaClass += ' celda-central';
      }
      if (isFigura) celdaClass += ' celda-figura';
      if (isMarcado) celdaClass += ' celda-marcada';
      if (isUltima) celdaClass += ' celda-ultima';
      html += `<div class="${celdaClass}">`;
      if (fila === 2 && col === 2) {
        html += `<span class="estrella">${svgEstrella()}</span>`;
      } else {
        html += num;
      }
      html += `</div>`;
    }
    html += '</div>';
  }
  html += '</div>';
  return html;
}

function mostrarModalGanador(boleto, figura, valor, numeros, carton, marcados = [], ultimaBalota = null) {
  document.getElementById("ganadorBoleto").textContent = boleto;
  document.getElementById("ganadorFigura").textContent = figura;
  document.getElementById("ganadorValor").textContent = valor;
  document.getElementById("ganadorNumeros").textContent = Array.isArray(numeros) ? numeros.join(", ") : numeros;
  if (document.getElementById("contadorBalotasGanador"))
    document.getElementById("contadorBalotasGanador").textContent = marcados.length;
  if (document.getElementById("ultimaBalotaModal"))
    document.getElementById("ultimaBalotaModal").textContent = ultimaBalota !== null ? ultimaBalota : "";
  document.getElementById("figuraVisual").innerHTML = armarCartonHTML(carton, marcados, figura, ultimaBalota);
  document.getElementById("modalGanador").style.display = "flex";
}

// ================== FUNCIONES DE USUARIOS (para MODAL) ==================

function abrirModalUsuarios() {
  document.getElementById('modalUsuarios').style.display = 'flex';
  cargarUsuarios();
}
function cerrarModalUsuarios() {
  document.getElementById('modalUsuarios').style.display = 'none';
}

document.addEventListener("DOMContentLoaded", () => {
  const formAgregarUsuario = document.getElementById('formAgregarUsuario');
  if (formAgregarUsuario) {
    formAgregarUsuario.onsubmit = async function (e) {
      e.preventDefault();
      const form = new FormData(this);
      const res = await fetch('/usuarios/agregar', {
        method: 'POST',
        body: form
      });
      if (res.ok) {
        this.reset();
        cargarUsuarios();
      } else {
        alert('Error al agregar usuario');
      }
    };
  }
});

async function cargarUsuarios() {
  const res = await fetch('/usuarios/lista');
  const data = await res.json();
  let html = `<b style="color:#ffd803;">Usuarios registrados:</b><ul style="margin-top:10px;">`;
  data.usuarios.forEach(u => {
    html += `<li style="margin-bottom:8px;color:#fff;">${u.usuario} <button style="background:#e53935;padding:2px 10px;border:none;border-radius:6px;color:#fff;cursor:pointer;margin-left:14px;" onclick="eliminarUsuario('${u.usuario}')">Eliminar</button></li>`;
  });
  html += `</ul>`;
  document.getElementById('listaUsuarios').innerHTML = html;
}

async function eliminarUsuario(usuario) {
  if (confirm('¿Eliminar usuario ' + usuario + '?')) {
    await fetch('/usuarios/eliminar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usuario })
    });
    cargarUsuarios();
  }

}

// ================== asignar planillas ) ==================

// Actualiza resumen cuando agregas/quitas
// Resumen contable en vivo
function actualizarResumenContable() {
  let html = `<table style="background:#2a335c;color:#fff;border-radius:8px;width:100%;max-width:460px;">
    <tr><th style="text-align:left;padding:6px 8px;">Vendedor</th>
        <th>Planillas</th>
        <th>Boletos</th>
    </tr>`;
  let totalPlanillas = 0;
  for (let nombre in planillasAsignadas) {
    let n = planillasAsignadas[nombre].length;
    html += `<tr>
      <td style="padding:6px 8px;">${nombre}</td>
      <td style="text-align:center;">${n}</td>
      <td style="text-align:center;">${n * 40}</td>
    </tr>`;
    totalPlanillas += n;
  }
  html += `<tr style="font-weight:bold;background:#232946;"><td style="padding:6px 8px;">TOTAL</td>
    <td style="text-align:center;">${totalPlanillas}</td>
    <td style="text-align:center;">${totalPlanillas * 40}</td>
  </tr></table>`;
  document.getElementById('tablaResumen').innerHTML = html;
}

// === Actualizar cada vez que agregas/quitas planillas
function recargarResumenes() {
  actualizarResumenContable();
  cargarAsignacionesPorFecha();
}

// Agrega evento después de agregar/quitar planillas
document.querySelectorAll('.vendedor-card').forEach((card, idx) => {
  card.querySelector('.scan-btn').addEventListener('click', ()=>{
    setTimeout(recargarResumenes, 100);
  });
  card.querySelector('.input-planilla').addEventListener('keydown', (e)=>{
    if(e.key==='Enter') setTimeout(recargarResumenes, 100);
  });
});

function quitarPlanilla(idx, i) {
  const card = document.querySelectorAll('.vendedor-card')[idx];
  const nombre = card.dataset.nombre;
  planillasAsignadas[nombre].splice(i, 1);
  mostrarPlanillas(idx);
  recargarResumenes();
}
// Mostrar el resumen vacío al cargar
actualizarResumenContable();


// ----------- HISTÓRICO DE ASIGNACIONES -------------
function cargarAsignacionesPorFecha() {
  const fecha = document.getElementById('fecha').value;
  if (!fecha) return;
  fetch(`/asignaciones/${fecha}.xml`)
    .then(r => r.ok ? r.text() : Promise.reject("No hay asignaciones para esta fecha"))
    .then(xmlText => mostrarHistorico(xmlText))
    .catch(()=>document.getElementById('historicoPlanillas').innerHTML="No hay asignaciones guardadas en el sistema para esa fecha.");
}

function mostrarHistorico(xmlText) {
  planillasUsadas = new Set();
  const parser = new DOMParser();
  const xml = parser.parseFromString(xmlText, "application/xml");
  const vendedores = xml.querySelectorAll("vendedor");
  let html = `<div style="color:#ffd803;font-size:1.09em;margin-bottom:7px;">Resumen Guardado</div>
  <table style="background:#232946;color:#fff;border-radius:8px;width:100%;max-width:700px;">
    <tr><th>Vendedor</th><th>Alias</th><th>Planillas</th><th>Boletos</th><th>Códigos</th></tr>`;
  let totalPlanillas=0;
  vendedores.forEach(v => {
    const nombre = v.getAttribute("nombre");
    const alias = v.getAttribute("alias") || '';
    const planillas = Array.from(v.querySelectorAll("planilla")).map(p=>p.getAttribute("codigo"));
    planillas.forEach(codigo=>planillasUsadas.add(codigo)); // <-- AGREGA AQUÍ
    html += `<tr>
      <td>${nombre}</td>
      <td>${alias}</td>
      <td style="text-align:center;">${planillas.length}</td>
      <td style="text-align:center;">${planillas.length*40}</td>
      <td style="font-size:0.99em;">${planillas.join(", ")}</td>
    </tr>`;
    totalPlanillas += planillas.length;
  });
  html += `<tr style="font-weight:bold;background:#1d2239;">
    <td colspan="2">TOTAL</td>
    <td style="text-align:center;">${totalPlanillas}</td>
    <td style="text-align:center;">${totalPlanillas*40}</td>
    <td></td>
  </tr></table>`;
  document.getElementById('historicoPlanillas').innerHTML = html;
}
