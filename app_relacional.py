import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import time

# ==========================================
# 1. CONFIGURACIÓN E INICIO
# ==========================================
st.set_page_config(page_title="SAP PM Relacional", layout="wide", page_icon="🏗️")

# Estilos CSS para diferenciar niveles y tablas
st.markdown("""
<style>
    .n2 { color: #b71c1c; font-weight: bold; font-size: 20px; border-bottom: 2px solid #b71c1c; margin-top: 15px;}
    .n3 { color: #0d47a1; font-weight: bold; margin-left: 20px; font-size: 18px; }
    .n4 { color: #1b5e20; font-weight: bold; margin-left: 40px; font-size: 16px; }
    .n5 { color: #e65100; margin-left: 60px; font-style: italic; }
    .n6 { color: #424242; margin-left: 80px; font-size: 14px; }
    .spec-tag { background-color: #eee; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 8px; font-family: monospace;}
    .stock-ok { color: green; font-weight: bold; }
    .stock-low { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN MULTI-ARCHIVO (RELACIONAL)
# ==========================================
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Intento Nube vs Local
    if "gcp_service_account" in st.secrets:
        creds_dict = {k:v for k,v in st.secrets["gcp_service_account"].items()}
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

# Función inteligente que abre cualquiera de los 3 libros
def get_data(libro_nombre, hoja_nombre):
    client = get_client()
    if not client: return pd.DataFrame()
    try:
        sh = client.open(libro_nombre) # Abre el Libro (Ej. 1_DATA_MAESTRA)
        ws = sh.worksheet(hoja_nombre) # Abre la Pestaña (Ej. ACTIVOS)
        return pd.DataFrame(ws.get_all_records())
    except Exception as e:
        # st.error(f"Error leyendo {libro_nombre}/{hoja_nombre}: {e}")
        return pd.DataFrame()

# ==========================================
# 3. CARGA DE DATOS EN CACHÉ (Optimización)
# ==========================================
def cargar_todo():
    # Libro 1: Data Maestra
    df_activos = get_data("1_DATA_MAESTRA", "ACTIVOS")
    df_materiales = get_data("1_DATA_MAESTRA", "MATERIALES")
    df_bom = get_data("1_DATA_MAESTRA", "BOM")
    
    # Libro 2: Gestión
    df_avisos = get_data("2_GESTION_TRABAJO", "AVISOS")
    df_ots = get_data("2_GESTION_TRABAJO", "ORDENES")
    
    # Conversiones de tipo seguras
    if not df_activos.empty:
        df_activos['TAG'] = df_activos['TAG'].astype(str)
    
    if not df_bom.empty:
        df_bom['TAG_Equipo'] = df_bom['TAG_Equipo'].astype(str)
        df_bom['SKU_Material'] = df_bom['SKU_Material'].astype(str)

    if not df_materiales.empty:
        df_materiales['SKU'] = df_materiales['SKU'].astype(str)
        
    return df_activos, df_materiales, df_bom, df_avisos, df_ots

# Cargamos datos al inicio
df_activos, df_mat, df_bom, df_avisos, df_ots = cargar_todo()

# ==========================================
# 4. LÓGICA RELACIONAL (CRUCES DE TABLAS)
# ==========================================

def obtener_bom_detallada(tag_equipo):
    """
    Cruza la tabla BOM con MATERIALES para decirte no solo el ID,
    sino el nombre, marca y stock del repuesto.
    """
    if df_bom.empty or df_mat.empty:
        return pd.DataFrame()
    
    # 1. Filtrar BOM por el equipo seleccionado
    bom_filtro = df_bom[df_bom['TAG_Equipo'] == tag_equipo].copy()
    
    if bom_filtro.empty:
        return pd.DataFrame()

    # 2. VLOOKUP (Merge) con Materiales para traer descripción y stock
    bom_completa = pd.merge(
        bom_filtro, 
        df_mat, 
        left_on='SKU_Material', 
        right_on='SKU', 
        how='left'
    )
    
    # Seleccionar solo columnas útiles
    cols_utiles = ['SKU_Material', 'Descripcion', 'Marca', 'Modelo_Medida', 'Cantidad', 'Stock_Actual', 'Ubicacion_Almacen']
    # Filtrar solo las columnas que existan (por si el excel está vacio)
    cols_existentes = [c for c in cols_utiles if c in bom_completa.columns]
    
    return bom_completa[cols_existentes]

# ==========================================
# 5. INTERFAZ DE USUARIO
# ==========================================

st.sidebar.title("SAP PM Relacional")
menu = st.sidebar.radio("Módulos:", ["🌳 Navegador Técnico", "🛠️ Gestión del Trabajo", "📦 Almacén"])

# --- MÓDULO 1: NAVEGADOR TÉCNICO (Árbol + Info Real) ---
if menu == "🌳 Navegador Técnico":
    st.header("Explorador de Planta y Especificaciones")
    
    col_tree, col_detail = st.columns([1, 2])
    
    # Variables de estado para selección
    if 'selected_tag' not in st.session_state: st.session_state.selected_tag = None
    if 'selected_name' not in st.session_state: st.session_state.selected_name = None

    with col_tree:
        st.subheader("Jerarquía")
        if df_activos.empty:
            st.warning("⚠️ Archivo '1_DATA_MAESTRA' vacío o no conectado.")
        else:
            # Lógica de Árbol (Simplificada para navegación)
            plantas = df_activos[df_activos['Nivel'] == 'L2-Planta']
            
            for _, p in plantas.iterrows():
                # Nivel 2: Planta
                with st.expander(f"🏢 {p['Nombre']}", expanded=True):
                    areas = df_activos[df_activos['TAG_Padre'] == p['TAG']]
                    for _, a in areas.iterrows():
                        # Nivel 3: Area
                        st.markdown(f"<div class='n3'>📍 {a['Nombre']}</div>", unsafe_allow_html=True)
                        
                        equipos = df_activos[df_activos['TAG_Padre'] == a['TAG']]
                        for _, e in equipos.iterrows():
                            # Nivel 4: Equipo (Botón para seleccionar)
                            if st.button(f"⚙️ {e['Nombre']}", key=e['TAG']):
                                st.session_state.selected_tag = e['TAG']
                                st.session_state.selected_name = e['Nombre']
                            
                            # Mostrar hijos (Sistemas/Componentes) solo visualmente debajo
                            hijos = df_activos[df_activos['TAG_Padre'] == e['TAG']]
                            for _, h in hijos.iterrows():
                                if st.button(f"↳ 🔧 {h['Nombre']}", key=h['TAG']):
                                    st.session_state.selected_tag = h['TAG']
                                    st.session_state.selected_name = h['Nombre']
                                    
                                nietos = df_activos[df_activos['TAG_Padre'] == h['TAG']]
                                for _, n in nietos.iterrows():
                                    if st.button(f"&nbsp;&nbsp;&nbsp;&nbsp;• 🔩 {n['Nombre']}", key=n['TAG']):
                                        st.session_state.selected_tag = n['TAG']
                                        st.session_state.selected_name = n['Nombre']

    with col_detail:
        if st.session_state.selected_tag:
            tag = st.session_state.selected_tag
            nombre = st.session_state.selected_name
            
            # Encabezado del Activo
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3;">
                <h2 style="margin:0; color: #1565c0;">{nombre}</h2>
                <p style="margin:0;"><strong>TAG:</strong> {tag} | <strong>Info:</strong> Ficha Técnica Activa</p>
            </div>
            """, unsafe_allow_html=True)
            
            tab_bom, tab_hist, tab_spec = st.tabs(["🧩 Repuestos (BOM)", "📜 Historial Fallas", "📝 Datos Maestros"])
            
            # --- PESTAÑA BOM (LO QUE PEDISTE) ---
            with tab_bom:
                st.subheader(f"Lista de Materiales para: {nombre}")
                bom_real = obtener_bom_detallada(tag)
                
                if not bom_real.empty:
                    # Mostrar tabla bonita
                    st.dataframe(bom_real, use_container_width=True, hide_index=True)
                    
                    # Alerta de Stock
                    for index, row in bom_real.iterrows():
                        stock = row.get('Stock_Actual', 0)
                        minimo = 1 # Default
                        if stock <= 0:
                            st.error(f"⚠️ ALERTA: Sin stock de **{row['Descripcion']}** ({row['SKU_Material']})")
                        elif stock < 2:
                             st.warning(f"⚠️ Stock bajo de **{row['Descripcion']}**")
                else:
                    st.info("Este activo no tiene repuestos vinculados en la hoja BOM.")
                    st.markdown("*Para agregar, edita el Excel '1_DATA_MAESTRA', hoja 'BOM'.*")

            # --- PESTAÑA HISTORIAL ---
            with tab_hist:
                st.subheader("Últimas Intervenciones")
                if not df_ots.empty:
                    # Filtramos OTs que coincidan con este TAG
                    historial = df_ots[df_ots['TAG_Equipo'] == tag]
                    if not historial.empty:
                        st.dataframe(historial[['Fecha_Programada', 'Descripcion_Trabajo', 'Estado_OT', 'Tipo_Proveedor']])
                    else:
                        st.caption("No hay OTs registradas para este equipo.")
                else:
                    st.caption("Base de datos de OTs vacía.")

            # --- PESTAÑA ESPECIFICACIONES ---
            with tab_spec:
                # Buscar datos del activo
                row_act = df_activos[df_activos['TAG'] == tag].iloc[0]
                spec_text = row_act.get('Especificacion_Tecnica', 'No definido')
                st.text_area("Especificación Técnica (Editable en Excel)", value=str(spec_text), disabled=True)
                
                col1, col2 = st.columns(2)
                col1.metric("Criticidad", row_act.get('Criticidad', '-'))
                col2.metric("Estado", row_act.get('Estado', '-'))

        else:
            st.info("👈 Selecciona un equipo del árbol para ver sus detalles, repuestos y fajas.")

# --- MÓDULO 2: GESTIÓN DEL TRABAJO ---
elif menu == "🛠️ Gestión del Trabajo":
    st.header("Control de Avisos y OTs")
    
    c1, c2 = st.columns(2)
    c1.metric("Avisos Abiertos", len(df_avisos))
    c2.metric("OTs en Proceso", len(df_ots[df_ots['Estado_OT'] != 'Cerrado']) if not df_ots.empty else 0)
    
    st.subheader("Listado de Avisos Recientes")
    st.dataframe(df_avisos, use_container_width=True)

# --- MÓDULO 3: ALMACÉN ---
elif menu == "📦 Almacén":
    st.header("Maestro de Materiales")
    
    search = st.text_input("Buscar Repuesto (SKU o Nombre):")
    
    if not df_mat.empty:
        if search:
            mask = df_mat.apply(lambda x: search.lower() in str(x).lower(), axis=1)
            st.dataframe(df_mat[mask])
        else:
            st.dataframe(df_mat)
    else:
        st.warning("Hoja MATERIALES vacía.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Conectado a: 1_DATA_MAESTRA, 2_GESTION...")
