import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y ESTADO (BASE DE DATOS EN MEMORIA)
# ==========================================
st.set_page_config(page_title="Sistema Integral Rendering", layout="wide", page_icon="🏭")

# Inicializamos las tablas en memoria si no existen
if 'df_activos' not in st.session_state:
    # Estructura base (Columnas de tus archivos reales)
    st.session_state.df_activos = pd.DataFrame(columns=["TAG", "Nombre", "Nivel", "TAG_Padre", "Area", "Estado", "Especificaciones"])
    st.session_state.df_mat = pd.DataFrame(columns=["SKU", "Descripcion", "Marca", "Stock", "Ubicacion"])
    st.session_state.df_bom = pd.DataFrame(columns=["TAG_Equipo", "SKU_Material", "Cantidad"])
    st.session_state.df_avisos = pd.DataFrame(columns=["ID", "Fecha", "TAG_Equipo", "Descripcion", "Estado"])
    st.session_state.df_ots = pd.DataFrame(columns=["ID_OT", "ID_Aviso", "TAG_Equipo", "Trabajo", "Fecha_Prog", "Estado"])
    st.session_state.df_lecturas = pd.DataFrame(columns=["Fecha", "TAG_Equipo", "Variable", "Valor", "Inspector"])

    # --- PRE-CARGA DE EJEMPLO (Tus 9 Digestores) ---
    # Solo se carga la primera vez para que no empieces desde cero
    activos_demo = [
        {"TAG": "PL-REND", "Nombre": "Planta Rendering", "Nivel": "L2-Planta", "TAG_Padre": "ROOT", "Area": "General"},
        {"TAG": "AR-COCC", "Nombre": "Área Cocción", "Nivel": "L3-Area", "TAG_Padre": "PL-REND", "Area": "Cocción"},
    ]
    for i in range(1, 10):
        tag = f"EQ-DIG-{i:02d}"
        activos_demo.append({"TAG": tag, "Nombre": f"Digestor #{i}", "Nivel": "L4-Equipo", "TAG_Padre": "AR-COCC", "Area": "Cocción"})
        activos_demo.append({"TAG": f"{tag}-TRM", "Nombre": f"Transmisión Dig.{i}", "Nivel": "L5-Componente", "TAG_Padre": tag, "Area": "Cocción"})
        
    st.session_state.df_activos = pd.DataFrame(activos_demo)

# Atajos para escribir menos
def get_df(key): return st.session_state[key]
def save_df(key, df): st.session_state[key] = df

# ==========================================
# 2. FUNCIONES DE FILTRO EN CASCADA
# ==========================================
def cascada_activos(key_suffix=""):
    """Genera selectores Planta -> Área -> Equipo y devuelve la selección final"""
    df = get_df('df_activos')
    
    col1, col2, col3 = st.columns(3)
    
    # 1. Planta
    plantas = df[df['Nivel'] == 'L2-Planta']['TAG'].unique()
    planta = col1.selectbox("📍 Planta", plantas, key=f"pl_{key_suffix}")
    
    # 2. Área (Filtrada)
    areas = df[df['TAG_Padre'] == planta]['TAG'].unique() if planta else []
    area = col2.selectbox("🏭 Área", areas, key=f"ar_{key_suffix}")
    
    # 3. Equipo (Filtrado)
    equipos = df[df['TAG_Padre'] == area]['TAG'].unique() if area else []
    equipo = col3.selectbox("⚙️ Equipo", equipos, key=f"eq_{key_suffix}")
    
    return planta, area, equipo

# ==========================================
# 3. INTERFAZ PRINCIPAL
# ==========================================
st.title("🏭 Gestión de Activos y Mantenimiento")
st.markdown("Sistema CRUD: Crear, Leer, Actualizar y Borrar datos en tiempo real.")

menu = st.sidebar.radio("Módulos Operativos:", 
    ["1. Maestro de Activos (Árbol)", 
     "2. Gestión del Trabajo (OTs)", 
     "3. Monitoreo (Lecturas)", 
     "4. Almacén & BOM"])

# -----------------------------------------------------------------------------
# MÓDULO 1: MAESTRO DE ACTIVOS (ALTA Y EDICIÓN)
# -----------------------------------------------------------------------------
if menu == "1. Maestro de Activos (Árbol)":
    tab_ver, tab_crear, tab_edit = st.tabs(["👁️ Explorador Jerárquico", "➕ Agregar Nuevo Activo", "✏️ Edición Masiva"])
    
    # --- TAB: VER ---
    with tab_ver:
        st.subheader("Navegación en Cascada")
        planta, area, equipo = cascada_activos("view")
        
        if equipo:
            st.divider()
            # Mostrar Equipo y sus Hijos (Componentes)
            info_equipo = get_df('df_activos')[get_df('df_activos')['TAG'] == equipo]
            hijos = get_df('df_activos')[get_df('df_activos')['TAG_Padre'] == equipo]
            
            st.info(f"Visualizando: **{equipo}**")
            st.dataframe(pd.concat([info_equipo, hijos]), use_container_width=True)
            

    # --- TAB: CREAR (TU REQUERIMIENTO PRINCIPAL) ---
    with tab_crear:
        st.subheader("Alta de Activos en Cascada")
        st.markdown("Para agregar un componente (ej. Motor), selecciona primero a qué equipo pertenece.")
        
        # 1. Seleccionar Padre con Cascada
        st.markdown("##### 1. Ubicación del Activo (Padre)")
        p, a, e = cascada_activos("add")
        
        # Lógica: ¿Quién es el padre?
        padre_sugerido = "ROOT"
        nivel_sugerido = "L2-Planta"
        
        if e: 
            padre_sugerido = e
            nivel_sugerido = "L5-Componente"
            st.success(f"El nuevo activo será hijo de: **{e}**")
        elif a: 
            padre_sugerido = a
            nivel_sugerido = "L4-Equipo"
            st.success(f"El nuevo activo será hijo de: **{a}**")
        elif p: 
            padre_sugerido = p
            nivel_sugerido = "L3-Area"
            st.success(f"El nuevo activo será hijo de: **{p}**")

        # 2. Formulario de Datos
        st.markdown("##### 2. Datos del Nuevo Activo")
        with st.form("new_asset_form"):
            col_a, col_b = st.columns(2)
            new_tag = col_a.text_input("TAG Nuevo", value=f"{padre_sugerido}-NUEVO")
            new_name = col_b.text_input("Nombre Descriptivo")
            new_level = col_a.selectbox("Nivel Jerárquico", ["L2-Planta", "L3-Area", "L4-Equipo", "L5-Componente"], index=["L2-Planta", "L3-Area", "L4-Equipo", "L5-Componente"].index(nivel_sugerido))
            new_spec = st.text_area("Especificaciones Técnicas")
            
            if st.form_submit_button("💾 Guardar Activo"):
                if new_tag in get_df('df_activos')['TAG'].values:
                    st.error("¡Ese TAG ya existe!")
                else:
                    new_row = {"TAG": new_tag, "Nombre": new_name, "Nivel": new_level, "TAG_Padre": padre_sugerido, "Area": "Manual", "Especificaciones": new_spec}
                    save_df('df_activos', pd.concat([get_df('df_activos'), pd.DataFrame([new_row])], ignore_index=True))
                    st.success(f"Activo {new_tag} creado correctamente.")
                    st.rerun()

    # --- TAB: EDITAR ---
    with tab_edit:
        st.subheader("Edición Tipo Excel")
        st.markdown("Edita directamente las celdas y presiona guardar.")
        
        df_editado = st.data_editor(get_df('df_activos'), num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 Guardar Cambios Masivos (Activos)"):
            save_df('df_activos', df_editado)
            st.success("Base de datos actualizada.")

# -----------------------------------------------------------------------------
# MÓDULO 2: GESTIÓN DEL TRABAJO (OTs)
# -----------------------------------------------------------------------------
if menu == "2. Gestión del Trabajo (OTs)":
    st.subheader("🛠️ Generación de Avisos y OTs")
    
    col_form, col_data = st.columns([1, 2])
    
    with col_form:
        st.markdown("### Nueva OT")
        # Filtro Cascada Mini
        df = get_df('df_activos')
        eqs = df[df['Nivel'].isin(['L4-Equipo', 'L5-Componente'])]['TAG'].unique()
        
        with st.form("ot_form"):
            sel_eq_ot = st.selectbox("Equipo Afectado", eqs)
            desc_ot = st.text_area("Descripción del Trabajo")
            fecha_ot = st.date_input("Fecha Programada")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            
            if st.form_submit_button("🚀 Crear OT"):
                new_ot = {
                    "ID_OT": len(get_df('df_ots')) + 5000,
                    "ID_Aviso": "N/A",
                    "TAG_Equipo": sel_eq_ot,
                    "Trabajo": desc_ot,
                    "Fecha_Prog": str(fecha_ot),
                    "Estado": "Abierta"
                }
                save_df('df_ots', pd.concat([get_df('df_ots'), pd.DataFrame([new_ot])], ignore_index=True))
                st.success("OT Creada")
                
    with col_data:
        st.markdown("### Backlog de Mantenimiento")
        # Edición directa de estados de OT
        edited_ots = st.data_editor(get_df('df_ots'), key="ot_editor", use_container_width=True)
        if len(edited_ots) != len(get_df('df_ots')): # Detectar si borraron filas
             save_df('df_ots', edited_ots)

# -----------------------------------------------------------------------------
# MÓDULO 3: MONITOREO
# -----------------------------------------------------------------------------
if menu == "3. Monitoreo (Lecturas)":
    st.subheader("📈 Registro de Lecturas de Campo")
    
    # Cascada para seleccionar qué medir
    planta, area, equipo = cascada_activos("mon")
    
    if equipo:
        # Buscar componentes hijos del equipo seleccionado
        hijos = get_df('df_activos')[get_df('df_activos')['TAG_Padre'] == equipo]['TAG'].tolist()
        lista_medibles = [equipo] + hijos
        
        with st.form("lectura_form"):
            col1, col2, col3 = st.columns(3)
            tag_medido = col1.selectbox("Punto de Medida", lista_medibles)
            variable = col2.selectbox("Variable", ["Temperatura (°C)", "Vibración (mm/s)", "Amperaje (A)", "Nivel (%)"])
            valor = col3.number_input("Valor", step=0.1)
            inspector = st.text_input("Inspector", value="Operador Turno")
            
            if st.form_submit_button("Grabar Lectura"):
                new_lec = {
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "TAG_Equipo": tag_medido,
                    "Variable": variable,
                    "Valor": valor,
                    "Inspector": inspector
                }
                save_df('df_lecturas', pd.concat([get_df('df_lecturas'), pd.DataFrame([new_lec])], ignore_index=True))
                st.success("Lectura registrada.")
    
    st.divider()
    st.subheader("Historial Reciente")
    st.dataframe(get_df('df_lecturas').sort_values("Fecha", ascending=False).head(10), use_container_width=True)
    
    # Gráfico rápido
    if not get_df('df_lecturas').empty:
        df_l = get_df('df_lecturas')
        fig = px.line(df_l, x="Fecha", y="Valor", color="TAG_Equipo", symbol="Variable", title="Tendencias")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MÓDULO 4: ALMACÉN
# -----------------------------------------------------------------------------
if menu == "4. Almacén & BOM":
    tab_inv, tab_bom = st.tabs(["📦 Inventario Materiales", "🔗 Asignar Repuesto (BOM)"])
    
    with tab_inv:
        st.markdown("### Maestro de Materiales")
        # Tabla editable para inventario
        df_mat_edit = st.data_editor(get_df('df_mat'), num_rows="dynamic", use_container_width=True)
        save_df('df_mat', df_mat_edit)
        
    with tab_bom:
        st.markdown("### Vincular Repuesto a Equipo")
        
        c1, c2 = st.columns(2)
        # Filtramos solo equipos y componentes para asignar BOM
        assets = get_df('df_activos')[get_df('df_activos')['Nivel'].isin(['L4-Equipo', 'L5-Componente'])]['TAG'].unique()
        mats = get_df('df_mat')['SKU'].unique()
        
        with st.form("bom_form"):
            sel_asset = c1.selectbox("Equipo / Componente", assets)
            sel_sku = c2.selectbox("Repuesto (SKU)", mats) if len(mats) > 0 else c2.warning("Crea materiales primero")
            cant = st.number_input("Cantidad", min_value=1, value=1)
            
            if st.form_submit_button("Vincular"):
                new_bom = {"TAG_Equipo": sel_asset, "SKU_Material": sel_sku, "Cantidad": cant}
                save_df('df_bom', pd.concat([get_df('df_bom'), pd.DataFrame([new_bom])], ignore_index=True))
                st.success(f"Vinculado: {sel_sku} -> {sel_asset}")
        
        st.dataframe(get_df('df_bom'), use_container_width=True)

# Footer con instrucciones
st.sidebar.markdown("---")
st.sidebar.info("💡 **Nota:** Los datos se guardan en la memoria temporal. Si recargas la página (F5), volverán al estado inicial.")
