import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Sistema Integral Rendering", layout="wide", page_icon="🏭")

# CSS para mejorar la estética
st.markdown("""
<style>
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; }
    .status-ok { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .status-err { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN SEGURA A GOOGLE DRIVE
# ==========================================
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Intenta leer Secrets de la Nube (Streamlit Cloud)
    if "gcp_service_account" in st.secrets:
        creds_dict = {k:v for k,v in st.secrets["gcp_service_account"].items()}
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # Intenta leer archivo local (para pruebas en tu PC)
    else:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        except:
            return None
    return gspread.authorize(creds)

def get_data(archivo_nombre, hoja_nombre):
    """
    Busca el archivo y la hoja específica.
    Devuelve DataFrame vacío si falla, para que la App no se caiga.
    """
    client = get_client()
    if not client:
        st.error("❌ Error de Credenciales. Configura los Secrets.")
        return pd.DataFrame()
    
    try:
        sh = client.open(archivo_nombre)
        ws = sh.worksheet(hoja_nombre)
        return pd.DataFrame(ws.get_all_records())
    except gspread.SpreadsheetNotFound:
        st.sidebar.error(f"❌ No encuentro: {archivo_nombre}")
        return pd.DataFrame()
    except gspread.WorksheetNotFound:
        st.sidebar.warning(f"⚠️ En '{archivo_nombre}' falta la hoja: {hoja_nombre}")
        return pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"Error en {archivo_nombre}: {e}")
        return pd.DataFrame()

# ==========================================
# 3. CARGA DE DATOS (NOMBRES CORREGIDOS)
# ==========================================
@st.cache_data(ttl=300) # Recarga cada 5 min automáticamente
def cargar_todo():
    with st.spinner('📡 Sincronizando con Google Drive...'):
        
        # --- ARCHIVO 1: 1_DATA_MAESTRA ---
        # Asumo que las pestañas (hojas de abajo) se llaman: ACTIVOS, MATERIALES, BOM
        df_activos = get_data("1_DATA_MAESTRA", "ACTIVOS")
        df_mat = get_data("1_DATA_MAESTRA", "MATERIALES")
        df_bom = get_data("1_DATA_MAESTRA", "BOM")
        
        # --- ARCHIVO 2: 2_GESTION_TRABAJO ---
        # Asumo pestañas: AVISOS, ORDENES
        df_avisos = get_data("2_GESTION_TRABAJO", "AVISOS")
        df_ots = get_data("2_GESTION_TRABAJO", "ORDENES")
        
        # --- ARCHIVO 3: 3_MONITOREO ---
        # Asumo pestaña: DATA (Si se llama "Hoja 1", cambia "DATA" por "Hoja 1" aquí abajo)
        df_kpi = get_data("3_MONITOREO", "DATA") 

        # Correcciones de formato (Convertir TAGs y SKUs a texto siempre)
        if not df_activos.empty and 'TAG' in df_activos.columns:
            df_activos['TAG'] = df_activos['TAG'].astype(str)
        if not df_mat.empty and 'SKU' in df_mat.columns:
            df_mat['SKU'] = df_mat['SKU'].astype(str)
            
        return df_activos, df_mat, df_bom, df_avisos, df_ots, df_kpi

# Ejecutamos la carga
df_activos, df_mat, df_bom, df_avisos, df_ots, df_kpi = cargar_todo()

# ==========================================
# 4. INTERFAZ DE USUARIO (DASHBOARD)
# ==========================================
st.sidebar.title("🏭 Planta Rendering")
menu = st.sidebar.radio("Módulos:", 
    ["1. Activos (Data Maestra)", "2. Gestión Mantenimiento", "3. Monitoreo (KPIs)", "4. Almacén"])

st.sidebar.markdown("---")
st.sidebar.caption("Estado de Conexión:")
if not df_activos.empty: st.sidebar.markdown('<div class="status-ok">✅ Maestra OK</div>', unsafe_allow_html=True)
if not df_avisos.empty: st.sidebar.markdown('<div class="status-ok">✅ Gestión OK</div>', unsafe_allow_html=True)
if not df_kpi.empty: st.sidebar.markdown('<div class="status-ok">✅ Monitoreo OK</div>', unsafe_allow_html=True)
else: st.sidebar.markdown('<div class="status-err">⚠️ Monitoreo Vacío</div>', unsafe_allow_html=True)

# --- VISTA 1: ACTIVOS ---
if menu == "1. Activos (Data Maestra)":
    st.title("🏗️ Navegador de Activos")
    if not df_activos.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            filtro = st.text_input("🔍 Buscar TAG o Nombre:")
        
        if filtro:
            mask = df_activos.astype(str).apply(lambda x: filtro.lower() in x.str.lower().values, axis=1)
            st.dataframe(df_activos[mask], use_container_width=True)
        else:
            st.dataframe(df_activos, use_container_width=True)
    else:
        st.warning("No se cargó '1_DATA_MAESTRA'. Revisa que la hoja interna se llame 'ACTIVOS'.")

# --- VISTA 2: GESTIÓN ---
elif menu == "2. Gestión Mantenimiento":
    st.title("🛠️ Gestión del Trabajo")
    tab_av, tab_ot = st.tabs(["📢 Avisos de Avería", "📋 Órdenes de Trabajo"])
    
    with tab_av:
        if not df_avisos.empty:
            st.dataframe(df_avisos, use_container_width=True)
        else:
            st.info("No hay datos en 'AVISOS' o no se pudo leer el archivo.")
            
    with tab_ot:
        if not df_ots.empty:
            st.dataframe(df_ots, use_container_width=True)
        else:
            st.info("No hay datos en 'ORDENES'.")

# --- VISTA 3: MONITOREO ---
elif menu == "3. Monitoreo (KPIs)":
    st.title("📈 Dashboard de Monitoreo")
    st.markdown("Datos provenientes de: `3_MONITOREO`")
    
    if not df_kpi.empty:
        st.dataframe(df_kpi, use_container_width=True)
        
        # Detección automática de columnas numéricas para graficar
        cols_num = df_kpi.select_dtypes(include=['float64', 'int64']).columns
        if len(cols_num) > 0:
            st.subheader("Tendencias")
            kpi_selec = st.multiselect("Selecciona variables a graficar:", cols_num, default=cols_num[0])
            if kpi_selec:
                st.line_chart(df_kpi[kpi_selec])
        else:
            st.info("La tabla no tiene columnas numéricas para graficar.")
    else:
        st.error("El archivo `3_MONITOREO` se encontró, pero la pestaña 'DATA' está vacía o no existe.")
        st.markdown("**Solución:** Abre tu Excel `3_MONITOREO` y asegúrate de que la pestaña inferior se llame **DATA**.")

# --- VISTA 4: ALMACÉN ---
elif menu == "4. Almacén":
    st.title("📦 Inventario de Repuestos")
    if not df_mat.empty:
        busq = st.text_input("Buscar SKU o Repuesto:")
        if busq:
             mask = df_mat.astype(str).apply(lambda x: busq.lower() in x.str.lower().values, axis=1)
             st.dataframe(df_mat[mask], use_container_width=True)
        else:
            st.dataframe(df_mat, use_container_width=True)
    else:
        st.warning("No se cargó la hoja 'MATERIALES' del archivo 1.")
