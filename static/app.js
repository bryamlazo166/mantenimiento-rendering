// URL base de la API
const API_BASE = window.location.origin;

// Datos simulados de jerarquía (en producción vendrían del backend)
const jerarquiaData = {
    'Procesamiento': {
        'Línea 1': {
            'Digestor Principal': {
                'Sistema de Cocción': ['Motor principal', 'Reductor', 'Eje principal', 'Chumaceras'],
                'Sistema de Vapor': ['Válvulas', 'Trampa de vapor', 'Tuberías']
            },
            'Transportador Helicoidal': {
                'Sistema de Transmisión': ['Motor eléctrico', 'Reductor', 'Cadena', 'Polea'],
                'Sistema de Tornillo': ['Tornillo helicoidal', 'Carcasa', 'Rodamientos']
            }
        },
        'Línea 2': {
            'Prensa': {
                'Sistema Hidráulico': ['Bomba hidráulica', 'Cilindros', 'Válvulas'],
                'Sistema Mecánico': ['Motor', 'Chumaceras', 'Eje']
            }
        }
    },
    'Deshidratación': {
        'Línea 3': {
            'Secador Rotatorio': {
                'Sistema de Rotación': ['Motor', 'Reductor', 'Piñón', 'Corona'],
                'Sistema de Calentamiento': ['Quemador', 'Ventilador', 'Ductos']
            }
        }
    },
    'Empaque': {
        'Línea 4': {
            'Envasadora': {
                'Sistema de Dosificación': ['Motor', 'Tornillo dosificador', 'Tolva'],
                'Sistema de Sellado': ['Resistencias', 'Cilindros', 'Sensores']
            }
        }
    }
};

// Variables globales
let equipoActual = null;

// ========== INICIALIZACIÓN ==========
document.addEventListener('DOMContentLoaded', () => {
    cargarAreas();
    configurarEventos();
    cargarEquipos();
});

// ========== LISTAS DESPLEGABLES DEPENDIENTES ==========
function cargarAreas() {
    const areaSelect = document.getElementById('area');
    areaSelect.innerHTML = '<option value="">Seleccione...</option>';
    
    Object.keys(jerarquiaData).forEach(area => {
        const option = document.createElement('option');
        option.value = area;
        option.textContent = area;
        areaSelect.appendChild(option);
    });
}

function cargarLineas(area) {
    const lineaSelect = document.getElementById('linea');
    lineaSelect.innerHTML = '<option value="">Seleccione...</option>';
    lineaSelect.disabled = false;
    
    if (jerarquiaData[area]) {
        Object.keys(jerarquiaData[area]).forEach(linea => {
            const option = document.createElement('option');
            option.value = linea;
            option.textContent = linea;
            lineaSelect.appendChild(option);
        });
    }
    
    resetearDesde('equipo');
}

function cargarEquipos_Desplegable(area, linea) {
    const equipoSelect = document.getElementById('equipo');
    equipoSelect.innerHTML = '<option value="">Seleccione...</option>';
    equipoSelect.disabled = false;
    
    if (jerarquiaData[area] && jerarquiaData[area][linea]) {
        Object.keys(jerarquiaData[area][linea]).forEach(equipo => {
            const option = document.createElement('option');
            option.value = equipo;
            option.textContent = equipo;
            equipoSelect.appendChild(option);
        });
    }
    
    resetearDesde('sistema');
}

function cargarSistemas(area, linea, equipo) {
    const sistemaSelect = document.getElementById('sistema');
    sistemaSelect.innerHTML = '<option value="">Seleccione...</option>';
    sistemaSelect.disabled = false;
    
    if (jerarquiaData[area] && jerarquiaData[area][linea] && jerarquiaData[area][linea][equipo]) {
        Object.keys(jerarquiaData[area][linea][equipo]).forEach(sistema => {
            const option = document.createElement('option');
            option.value = sistema;
            option.textContent = sistema;
            sistemaSelect.appendChild(option);
        });
    }
    
    resetearDesde('componente');
}

function cargarComponentes(area, linea, equipo, sistema) {
    const componenteSelect = document.getElementById('componente');
    componenteSelect.innerHTML = '<option value="">Seleccione...</option>';
    componenteSelect.disabled = false;
    
    if (jerarquiaData[area]?.[linea]?.[equipo]?.[sistema]) {
        jerarquiaData[area][linea][equipo][sistema].forEach(componente => {
            const option = document.createElement('option');
            option.value = componente;
            option.textContent = componente;
            componenteSelect.appendChild(option);
        });
    }
}

function resetearDesde(nivel) {
    const niveles = ['linea', 'equipo', 'sistema', 'componente'];
    const index = niveles.indexOf(nivel);
    
    for (let i = index; i < niveles.length; i++) {
        const select = document.getElementById(niveles[i]);
        select.innerHTML = `<option value="">Seleccione ${niveles[i - 1] || 'área'} primero</option>`;
        select.disabled = true;
    }
}

// ========== EVENTOS ==========
function configurarEventos() {
    document.getElementById('area').addEventListener('change', (e) => {
        cargarLineas(e.target.value);
    });
    
    document.getElementById('linea').addEventListener('change', (e) => {
        const area = document.getElementById('area').value;
        cargarEquipos_Desplegable(area, e.target.value);
    });
    
    document.getElementById('equipo').addEventListener('change', (e) => {
        const area = document.getElementById('area').value;
        const linea = document.getElementById('linea').value;
        cargarSistemas(area, linea, e.target.value);
    });
    
    document.getElementById('sistema').addEventListener('change', (e) => {
        const area = document.getElementById('area').value;
        const linea = document.getElementById('linea').value;
        const equipo = document.getElementById('equipo').value;
        cargarComponentes(area, linea, equipo, e.target.value);
    });
    
    document.getElementById('equipoForm').addEventListener('submit', guardarEquipo);
    document.getElementById('btnLimpiar').addEventListener('click', limpiarFormulario);
    document.getElementById('btnBuscar').addEventListener('click', buscarEquipos);
    document.getElementById('btnVerTodos').addEventListener('click', cargarEquipos);
}

// ========== CRUD ==========
async function guardarEquipo(e) {
    e.preventDefault();
    
    const data = {
        area: document.getElementById('area').value,
        linea: document.getElementById('linea').value,
        equipo: document.getElementById('equipo').value,
        sistema: document.getElementById('sistema').value,
        componente: document.getElementById('componente').value,
        codigo_interno: document.getElementById('codigo').value,
        descripcion: document.getElementById('descripcion').value,
        ubicacion: document.getElementById('ubicacion').value,
        criticidad: document.getElementById('criticidad').value,
        estado: document.getElementById('estado').value,
        fecha_alta: document.getElementById('fechaAlta').value || null,
        atributos: []
    };
    
    try {
        const response = await fetch(`${API_BASE}/equipos/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            mostrarMensaje('✅ Equipo guardado exitosamente', 'success');
            limpiarFormulario();
            cargarEquipos();
        } else {
            const error = await response.json();
            mostrarMensaje(`❌ Error: ${error.detail}`, 'error');
        }
    } catch (error) {
        mostrarMensaje('❌ Error de conexión con el servidor', 'error');
    }
}

async function cargarEquipos() {
    try {
        const response = await fetch(`${API_BASE}/equipos/`);
        const equipos = await response.json();
        
        actualizarEstadisticas(equipos);
        renderizarTabla(equipos);
    } catch (error) {
        console.error('Error al cargar equipos:', error);
    }
}

async function buscarEquipos() {
    const texto = document.getElementById('searchText').value;
    // Por ahora solo filtra localmente, luego se puede hacer búsqueda por API
    cargarEquipos();
}

function renderizarTabla(equipos) {
    const tbody = document.querySelector('#equiposTable tbody');
    
    if (equipos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="no-data">No hay equipos registrados</td></tr>';
        return;
    }
    
    tbody.innerHTML = equipos.map(eq => `
        <tr onclick="editarEquipo(${eq.id})">
            <td><strong>${eq.codigo_interno}</strong></td>
            <td>${eq.area}</td>
            <td>${eq.linea}</td>
            <td>${eq.equipo}</td>
            <td>${eq.sistema}</td>
            <td>${eq.componente}</td>
            <td>${eq.descripcion || '-'}</td>
            <td><span class="badge badge-${eq.criticidad?.toLowerCase() || 'media'}">${eq.criticidad}</span></td>
            <td>${eq.estado}</td>
            <td><button class="btn-editar" onclick="event.stopPropagation(); editarEquipo(${eq.id})">✏️ Editar</button></td>
        </tr>
    `).join('');
}

async function editarEquipo(id) {
    try {
        const response = await fetch(`${API_BASE}/equipos/${id}`);
        const equipo = await response.json();
        
        // Cargar cascada de desplegables
        document.getElementById('area').value = equipo.area;
        cargarLineas(equipo.area);
        
        setTimeout(() => {
            document.getElementById('linea').value = equipo.linea;
            cargarEquipos_Desplegable(equipo.area, equipo.linea);
            
            setTimeout(() => {
                document.getElementById('equipo').value = equipo.equipo;
                cargarSistemas(equipo.area, equipo.linea, equipo.equipo);
                
                setTimeout(() => {
                    document.getElementById('sistema').value = equipo.sistema;
                    cargarComponentes(equipo.area, equipo.linea, equipo.equipo, equipo.sistema);
                    
                    setTimeout(() => {
                        document.getElementById('componente').value = equipo.componente;
                    }, 100);
                }, 100);
            }, 100);
        }, 100);
        
        // Cargar otros campos
        document.getElementById('codigo').value = equipo.codigo_interno;
        document.getElementById('descripcion').value = equipo.descripcion || '';
        document.getElementById('ubicacion').value = equipo.ubicacion || '';
        document.getElementById('criticidad').value = equipo.criticidad;
        document.getElementById('estado').value = equipo.estado;
        document.getElementById('fechaAlta').value = equipo.fecha_alta || '';
        
        equipoActual = equipo.id;
        document.getElementById('btnActualizar').disabled = false;
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
        console.error('Error al cargar equipo:', error);
    }
}

function actualizarEstadisticas(equipos) {
    const total = equipos.length;
    const criticos = equipos.filter(e => e.criticidad === 'Alta').length;
    
    document.getElementById('totalEquipos').textContent = `Total: ${total} equipos`;
    document.getElementById('equiposCriticos').textContent = `Críticos: ${criticos}`;
}

function limpiarFormulario() {
    document.getElementById('equipoForm').reset();
    resetearDesde('linea');
    equipoActual = null;
    document.getElementById('btnActualizar').disabled = true;
    document.getElementById('mensaje').style.display = 'none';
}

function mostrarMensaje(texto, tipo) {
    const mensaje = document.getElementById('mensaje');
    mensaje.textContent = texto;
    mensaje.className = `mensaje ${tipo}`;
    mensaje.style.display = 'block';
    
    setTimeout(() => {
        mensaje.style.display = 'none';
    }, 5000);
}
