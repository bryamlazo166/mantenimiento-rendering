import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y REPARACIÓN DE MEMORIA
# ==========================================
st.set_page_config(page_title="Sistema Integral Rendering", layout="wide", page_icon="🏭")

# Estilos CSS
st.markdown("""
<style>
    .main-header { font-size: 20px; font-weight: bold; color: #1e88e5; }
    .status-ok { background-color: #c8e6c9; padding: 5px; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN ROBUSTA (Evita KeyErrors) ---
# Verificamos CADA tabla individualmente. Si falta una (por actualización de código), la crea.

if 'df_activos' not in st.session_state:
    st.session_state.df_activos = pd.DataFrame(columns=["TAG", "Nombre", "Nivel", "TAG_Padre", "Area", "Estado", "Especificaciones"])
    
    # DATOS SEMILLA (SOLO SI ES LA PRIMERA VEZ)
    data_demo = []
    data_demo.append({"TAG": "PL-REND", "Nombre": "Planta Rendering", "Nivel": "L2-Planta", "TAG_Padre": "ROOT", "Area": "General"})
    data_demo.append({"TAG": "AR-COCC", "Nombre": "Área de Cocción", "Nivel": "L3-Area", "TAG_Padre": "PL-REND", "Area": "Cocción"})
    for i in range(1, 10):
        dig_tag = f"EQ-DIG-{i:02d}"
        data_demo.append({"TAG": dig_tag, "Nombre": f"Digestor #{i}", "Nivel": "L4-Equipo", "TAG_Padre": "AR-COCC", "Area": "Cocción", "Especificaciones": "5 Ton/h"})
        # Sistemas
        sis_mot = f"{dig_tag}-SIS-MOT"
        sis_trm = f"{dig_tag}-SIS-TRM"
        data_demo.append({"TAG": sis_mot, "Nombre": "Sistema Motriz", "Nivel": "L5-Sistema", "TAG_Padre": dig_tag, "Area": "Cocción", "Especificaciones": "Eléctrico"})
        data_demo.append({"TAG": sis_trm, "Nombre": "Sistema Transmisión", "Nivel": "L5-Sistema", "TAG_Padre": dig_tag, "Area": "Cocción", "Especificaciones": "Mecánico"})
        # Componentes
        data_demo.append({"TAG": f"{dig_tag}-MTR", "Nombre": "Motor 75HP", "Nivel": "L6-Componente", "TAG_Padre": sis_mot, "Area": "Cocción", "Especificaciones": "440V"})
        data_demo.append({"TAG": f"{dig_tag}-FAJ", "Nombre": "Juego Fajas B86", "Nivel": "L6-Componente", "TAG_Padre": sis_trm, "Area": "Cocción", "Especificaciones": "Perfil B"})
    
    st.session_state.df_activos = pd.DataFrame(data_demo)

if 'df_ots' not in st.session_state:
    st.session_state.df_ots = pd.DataFrame(columns=["ID_OT", "TAG_Equipo", "Descripcion", "Tipo", "Fecha_Prog", "Estado"])

if 'df_lecturas' not in st.session_state:
    st.session_state.df_lecturas = pd.DataFrame(columns=["Fecha", "TAG_Equipo", "Variable", "Valor", "Unidad", "Inspector"])

if 'df_materiales' not in st.session_state: # Aquí fallaba antes
    st.session_state.df_materiales = pd.DataFrame([
        {"SKU": "FAJ-B86", "Descripcion": "Faja en V B86", "Marca": "Gates", "Stock": 50, "Ubicacion": "A-1"},
        {"SKU": "ROD-22220", "Descripcion": "Rodamiento Esférico", "Marca": "SKF", "Stock": 4, "Ubicacion": "B-2"}
    ])

if 'df_bom' not in st.session_state: # Aquí fallaba antes
    st.session_state.df_bom = pd.DataFrame(columns=["TAG_Equipo", "SKU_Material", "Cantidad"])


# Atajos de acceso seguro
def get_df(key): 
    if key not in st.session_state: return pd.DataFrame() # Prevención extra
    return st.session_state[key]

def save_df(key, val): 
    st.session_state[key] = val

# ==========================================
# 2. FUNCIÓN MAESTRA: FILTRO EN CASCADA
# ==========================================
def filtro_cascada_universal(key_prefix):
    """Genera selectores dependientes y devuelve la selección más profunda"""
    df = get_df('df_activos')
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # 1. Planta
    plantas = df[df['Nivel'] == 'L2-Planta']['TAG'].unique()
    sel_planta = c1.selectbox("📍 Planta", plantas, key=f"{key_prefix}_p")
    
    # 2. Área
    areas = df[df['TAG_Padre'] == sel_planta]['TAG'].unique() if sel_planta else []
    sel_area = c2.selectbox("🏭 Área", areas, key=f"{key_prefix}_a")
    
    # 3. Equipo
    equipos = df[df['TAG_Padre'] == sel_area]['TAG'].unique() if sel_area else []
    sel_equipo = c3.selectbox("⚙️ Equipo", equipos, key=f"{key_prefix}_e")
    
    # 4. Sistema
    sistemas = df[df['TAG_Padre'] == sel_equipo]['TAG'].unique() if sel_equipo else []
    sel_sistema = c4.selectbox("🔄 Sistema", sistemas, key=f"{key_prefix}_s")
    
    # 5. Componente
    componentes = df[df['TAG_Padre'] == sel_sistema]['TAG'].unique() if sel_sistema else []
    sel_comp = c5.selectbox("🔩 Componente", componentes, key=f"{key_prefix}_c")
    
    return {
        "planta": sel_planta, "area": sel_area, "equipo": sel_equipo, 
        "sistema": sel_sistema, "componente": sel_comp,
        "ultimo_tag": sel_comp if sel_comp else (sel_sistema if sel_sistema else (sel_equipo if sel_equipo else (sel_area if sel_area else sel_planta)))
    }

# ==========================================
# 3. INTERFAZ PRINCIPAL
# ==========================================
st.title("🏭 Sistema Integral de Gestión de Activos")
st.markdown("Plataforma unificada: Activos, Mantenimiento, Monitoreo y Almacén.")

# Menú Principal
menu = st.sidebar.radio("Módulos del Sistema:", 
    ["1. Maestro de Activos (Jerarquía)", 
     "2. Gestión de Mantenimiento (OTs)", 
     "3. Monitoreo de Condición", 
     "4. Almacén y BOM"])

# -----------------------------------------------------------
# MÓDULO 1: MAESTRO DE ACTIVOS
# -----------------------------------------------------------
if menu == "1. Maestro de Activos (Jerarquía)":
    tab_nav, tab_add, tab_edit = st.tabs(["🌳 Navegador", "➕ Agregar Activo", "📝 Editor Masivo"])
    
    # --- A. NAVEGADOR ---
    with tab_nav:
        st.subheader("Explorador de Planta")
        ctx = filtro_cascada_universal("nav")
        
        if ctx['ultimo_tag']:
            st.divider()
            tag = ctx['ultimo_tag']
            # Filtro seguro para evitar errores si se borraron datos
            info_rows = get_df('df_activos')[get_df('df_activos')['TAG'] == tag]
            
            if not info_rows.empty:
                info = info_rows.iloc[0]
                st.markdown(f"### 🏷️ {info['Nombre']} ({info['TAG']})")
                st.info(f"**Especificaciones:** {info['Especificaciones']}")
                
                # Mostrar hijos directos
                hijos = get_df('df_activos')[get_df('df_activos')['TAG_Padre'] == tag]
                if not hijos.empty:
                    st.markdown(f"**Contenido de {info['Nivel']}:**")
                    st.dataframe(hijos[['TAG', 'Nombre', 'Nivel', 'Estado']], use_container_width=True)
                else:
                    st.caption("Este es el nivel más bajo (Componente).")

    # --- B. AGREGAR ACTIVO ---
    with tab_add:
        st.subheader("Alta de Nuevos Activos")
        st.markdown("Selecciona el **PADRE** donde se instalará el nuevo activo.")
        
        ctx_add = filtro_cascada_universal("add")
        padre = ctx_add['ultimo_tag']
        
        # Lógica automática de nivel sugerido (CORREGIDA PARA EVITAR VALUE ERROR)
        df = get_df('df_activos')
        nivel_padre = df[df['TAG'] == padre]['Nivel'].iloc[0] if padre else "ROOT"
        
        sugerencia = "L2-Planta" # Default seguro
        if nivel_padre == "L2-Planta": sugerencia = "L3-Area"
        elif nivel_padre == "L3-Area": sugerencia = "L4-Equipo"
        elif nivel_padre == "L4-Equipo": sugerencia = "L5-Sistema"
        elif nivel_padre == "L5-Sistema": sugerencia = "L6-Componente"
        
        if padre:
            st.success(f"Padre seleccionado: **{padre}** ({nivel_padre}) ➝ Se creará un: **{sugerencia}**")
        
        with st.form("form_alta"):
            c1, c2 = st.columns(2)
            new_tag = c1.text_input("TAG Nuevo", value=f"{padre}-NUEVO" if padre else "")
            new_nom = c2.text_input("Nombre")
            
            # Lista de opciones completa
            opciones_niv = ["L2-Planta", "L3-Area", "L4-Equipo", "L5-Sistema", "L6-Componente"]
            
            # Index seguro (Evita ValueError si la sugerencia no está en la lista)
            try:
                idx_sug = opciones_niv.index(sugerencia)
            except ValueError:
                idx_sug = 0
                
            new_niv = c1.selectbox("Nivel", opciones_niv, index=idx_sug)
            new_esp = c2.text_area("Especificaciones")
            
            if st.form_submit_button("💾 Guardar"):
                if new_tag in df['TAG'].values:
                    st.error("TAG Duplicado")
                else:
                    new_row = {"TAG": new_tag, "Nombre": new_nom, "Nivel": new_niv, "TAG_Padre": padre, "Area": "Manual", "Estado": "Operativo", "Especificaciones": new_esp}
                    save_df('df_activos', pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                    st.success("Activo Creado!")
                    st.rerun()

    # --- C. EDITOR MASIVO ---
    with tab_edit:
        st.subheader("Edición Directa")
        df_edited = st.data_editor(get_df('df_activos'), num_rows="dynamic", use_container_width=True, height=500)
        if st.button("💾 Guardar Cambios Tabla"):
            save_df('df_activos', df_edited)
            st.success("Guardado.")

# -----------------------------------------------------------
# MÓDULO 2: GESTIÓN DE MANTENIMIENTO
# -----------------------------------------------------------
if menu == "2. Gestión de Mantenimiento (OTs)":
    st.subheader("🛠️ Órdenes de Trabajo")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.markdown("#### Nueva OT")
        # Selector simple
        activos = get_df('df_activos')['TAG'].unique()
        with st.form("ot_form"):
            tag_ot = st.selectbox("Activo Afectado", activos)
            desc = st.text_area("Descripción Trabajo")
            tipo = st.selectbox("Tipo", ["Preventivo", "Correctivo", "Predictivo"])
            fecha = st.date_input("Fecha Programada")
            
            if st.form_submit_button("Crear OT"):
                new_ot = {
                    "ID_OT": len(get_df('df_ots')) + 1000,
                    "TAG_Equipo": tag_ot, "Descripcion": desc,
                    "Tipo": tipo, "Fecha_Prog": fecha, "Estado": "Abierta"
                }
                save_df('df_ots', pd.concat([get_df('df_ots'), pd.DataFrame([new_ot])], ignore_index=True))
                st.success("OT Generada")
                st.rerun()
                
    with col_der:
        st.markdown("#### Backlog (OTs Pendientes)")
        df_ots = get_df('df_ots')
        # Editor de OTs (para cerrar o cambiar estado)
        df_ots_edited = st.data_editor(df_ots, use_container_width=True)
        if not df_ots.equals(df_ots_edited):
            save_df('df_ots', df_ots_edited)

# -----------------------------------------------------------
# MÓDULO 3: MONITOREO DE CONDICIÓN
# -----------------------------------------------------------
if menu == "3. Monitoreo de Condición":
    st.subheader("📈 Registro de Variables (Temperatura/Vibración)")
    
    # 1. Filtro para encontrar el componente exacto
    st.markdown("Usa el filtro para hallar el componente a medir (ej: Motor):")
    ctx_mon = filtro_cascada_universal("mon")
    tag_medir = ctx_mon['ultimo_tag']
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"#### Registrar Lectura para: **{tag_medir}**")
        if tag_medir:
            with st.form("frm_lec"):
                var = st.selectbox("Variable", ["Temperatura", "Vibración Axial", "Vibración Radial", "Amperaje"])
                val = st.number_input("Valor", step=0.1)
                uni = st.selectbox("Unidad", ["°C", "mm/s", "Amperios"])
                insp = st.text_input("Inspector", value="Técnico 1")
                
                if st.form_submit_button("Grabar"):
                    new_lec = {
                        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "TAG_Equipo": tag_medir, "Variable": var, "Valor": val,
                        "Unidad": uni, "Inspector": insp
                    }
                    save_df('df_lecturas', pd.concat([get_df('df_lecturas'), pd.DataFrame([new_lec])], ignore_index=True))
                    st.success("Lectura OK")
                    st.rerun()
    
    with col2:
        st.markdown("#### Tendencias")
        df_l = get_df('df_lecturas')
        if not df_l.empty:
            # Filtramos lecturas del equipo seleccionado
            hist = df_l[df_l['TAG_Equipo'] == tag_medir]
            if not hist.empty:
                fig = px.line(hist, x="Fecha", y="Valor", color="Variable", title=f"Histórico {tag_medir}")
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("No hay lecturas previas para este TAG.")
        else:
            st.warning("Base de datos de lecturas vacía.")

# -----------------------------------------------------------
# MÓDULO 4: ALMACÉN Y BOM
# -----------------------------------------------------------
if menu == "4. Almacén y BOM":
    tab_mat, tab_bom = st.tabs(["📦 Maestro Materiales", "🔗 Asignar BOM"])
    
    with tab_mat:
        st.subheader("Inventario de Repuestos")
        # USAMOS GET_DF PARA EVITAR KEYERROR
        df_mat_ed = st.data_editor(get_df('df_materiales'), num_rows="dynamic", use_container_width=True)
        if st.button("Guardar Inventario"):
            save_df('df_materiales', df_mat_ed)
            
    with tab_bom:
        st.subheader("Vinculación Repuesto -> Equipo")
        
        c1, c2, c3 = st.columns(3)
        # Filtro de activos
        activos = get_df('df_activos')['TAG'].unique()
        mats = get_df('df_materiales')['SKU'].unique()
        
        with st.form("frm_bom"):
            sel_tag = c1.selectbox("Activo (Componente)", activos)
            # Validación por si no hay materiales creados
            sel_sku = c2.selectbox("Repuesto (SKU)", mats) if len(mats) > 0 else None
            cant = c3.number_input("Cantidad", min_value=1)
            
            if st.form_submit_button("Vincular BOM"):
                if sel_sku:
                    new_bom = {"TAG_Equipo": sel_tag, "SKU_Material": sel_sku, "Cantidad": cant}
                    save_df('df_bom', pd.concat([get_df('df_bom'), pd.DataFrame([new_bom])], ignore_index=True))
                    st.success("BOM Actualizada")
                else:
                    st.error("Crea materiales primero en la otra pestaña.")
        
        st.markdown("#### Lista de Materiales Actual")
        st.dataframe(get_df('df_bom'), use_container_width=True)
