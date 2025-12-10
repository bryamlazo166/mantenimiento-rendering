import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# ==========================================
# 1. CONFIGURACIÓN E INICIO
# ==========================================
st.set_page_config(page_title="SAP PM Relacional", layout="wide", page_icon="🏗️")

# Estilos CSS
st.markdown("""
<style>
    .n2 { color: #b71c1c; font-weight: bold; font-size: 20px; border-bottom: 2px solid #b71c1c; margin-top: 15px;}
    .n3 { color: #0d47a1; font-weight: bold; margin-left: 20px; font-size: 18px; }
    .n4 { color: #1b5e20; font-weight: bold; margin-left: 40px; font-size: 16px; }
    .spec-tag { background-color: #eee; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 8px; font-family: monospace;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN A GOOGLE SHEETS
# ==========================================
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Caso 1: Streamlit Cloud (Secrets)
    if "gcp_service_account" in st.secrets:
        creds_dict = {k:v for k,v in st.secrets["gcp_service_account"].items()}
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # Caso 2: Local (credentials.json)
    else:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        except:
            st.error("❌ No se encontraron credenciales. Configura los Secrets en la nube o el archivo credentials.json local.")
            return None
            
    return gspread.authorize(creds)

def get_data(libro_nombre, hoja_nombre):
    """Conecta y descarga datos. Muestra error si falla."""
    client = get_client()
    if not client: return pd.DataFrame()
    
    try:
        # Abre el libro por nombre exacto
        sh = client.open(libro_nombre)
        # Abre la pestaña
        ws = sh.worksheet(hoja_nombre)
        # Descarga los registros
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except gspread.SpreadsheetNotFound:
        st.error(f"❌ ERROR CRÍTICO: No encuentro el archivo **'{libro_nombre}'** en Google Drive.")
        st.info("💡 Solución: Asegúrate de que el nombre sea EXACTO y que hayas compartido el archivo con el email del robot (Service Account).")
        return pd.DataFrame()
    except gspread.WorksheetNotFound:
        st.warning(f"⚠️ El libro '{libro_nombre}' existe, pero no tiene una hoja llamada **'{hoja_nombre}'**.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error inesperado leyendo {libro_nombre}/{hoja_nombre}: {e}")
        return pd.DataFrame()

# ==========================================
# 3. CARGA DE DATOS (LOS 3 ARCHIVOS)
# ==========================================
@st.cache_data(ttl=600) # Recarga cada 10 min
def cargar_todo():
    with st.spinner('📡 Conectando con la Base de Datos en Drive...'):
        # --- LIBRO 1: DATA MAESTRA ---
        df_activos = get_data("1_DATA_MAESTRA", "ACTIVOS")
        df_materiales = get_data("1_DATA_MAESTRA", "MATERIALES")
        df_bom = get_data("1_DATA_MAESTRA", "BOM")
        
        # --- LIBRO 2: GESTION TRABAJO ---
        df_avisos = get_data("2_GESTION_TRABAJO", "AVISOS")
        df_ots = get_data("2_GESTION_TRABAJO", "ORDENES")
        
        # --- LIBRO 3: INDICADORES (NUEVO) ---
        # Asegúrate que tu archivo se llame "3_INDICADORES" y la hoja "DATA" (o cambia el nombre aquí)
        df_kpi = get_data("3_INDICADORES", "DATA") 
        
        # --- LIMPIEZA DE TIPOS ---
        if not df_activos.empty:
            df_activos['TAG'] = df_activos['TAG'].astype(str)
            df_activos['TAG_Padre'] = df_activos['TAG_Padre'].astype(str)
        
        if not df_bom.empty:
            df_bom['TAG_Equipo'] = df_bom['TAG_Equipo'].astype(str)
            df_bom['SKU_Material'] = df_bom['SKU_Material'].astype(str)

        if not df_materiales.empty:
            df_materiales['SKU'] = df_materiales['SKU'].astype(str)
            
        return df_activos, df_materiales, df_bom, df_avisos, df_ots, df_kpi

# Ejecutamos la carga
df_activos, df_mat, df_bom, df_avisos, df_ots, df_kpi = cargar_todo()

# ==========================================
