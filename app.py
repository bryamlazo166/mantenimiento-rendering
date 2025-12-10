import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import time
import json

# ==========================================
# 1. CONEXIÓN SEGURA (CLOUD & LOCAL)
# ==========================================
st.set_page_config(page_title="SAP PM Cloud - Rendering", layout="wide", page_icon="🏭")

@st.cache_resource
def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # INTENTO 1: Conexión para Streamlit Cloud (Secretos)
    if "gcp_service_account" in st.secrets:
        try:
            # Opción A: Si el secreto es un diccionario directo
            # creds_dict = dict(st.secrets["gcp_service_account"])
            
            # Opción B (Más robusta): Reconstruir el JSON desde los campos
            secrets = st.secrets["gcp_service_account"]
            creds_dict = {
                "type": secrets["type"],
                "project_id": secrets["project_id"],
                "private_key_id": secrets["private_key_id"],
                "private_key": secrets["private_key"],
                "client_email": secrets["client_email"],
                "client_id": secrets["client_id"],
                "auth_uri": secrets["auth_uri"],
                "token_uri": secrets["token_uri"],
                "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": secrets["client_x509_cert_url"]
            }
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"Error leyendo Secrets: {e}")
            return None

    # INTENTO 2: Conexión Local (Archivo JSON en PC)
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.warning("⚠️ Modo Offline o Error de Credenciales. Configura 'secrets' en la nube o 'credentials.json' en local.")
        return None

def get_data(sheet_name):
    client = get_google_sheet_client()
    if not client: return pd.DataFrame()
    try:
        sh = client.open("SAP_MANTENIMIENTO_DB")
        try:
            ws = sh.worksheet(sheet_name)
            return pd.DataFrame(ws.get_all_records())
        except:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"No se encuentra la hoja en Drive: {e}")
        return pd.DataFrame()

def save_row(sheet_name, data_dict):
    client = get_google_sheet_client()
    if not client: return
    try:
        sh = client.open("SAP_MANTENIMIENTO_DB")
        try:
            ws = sh.worksheet(sheet_name)
        except:
            ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
            # Agregar encabezados si es nueva
            ws.append_row(list(data_dict.keys()))
        
        ws.append_row(list(data_dict.values()))
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

# ==========================================
# 2. INICIALIZACIÓN (DATA SEEDING)
# ==========================================
def check_and_seed():
    """Carga tus datos reales si el Excel está vacío"""
    df = get_data("Equipos")
    if df.empty:
        # AQUÍ ESTABA EL ERROR ANTES, AHORA ESTÁ CORREGIDO CON COMILLAS
        st.toast("🌱 Inicializando Base de Datos...", icon="⚙️")
        
        # Equipos Reales (Extraídos de tus archivos)
        equipos = [
            {"TAG": "DIG-07", "Nombre": "DIGESTOR N° 7", "Area": "Cocción", "Estado": "Operativo"},
            {"TAG": "TRIT-01", "Nombre": "TRITURADOR GRANDE", "Area": "Triturado", "Estado": "Operativo"},
            {"TAG": "SEC-01", "Nombre": "SECADOR CONTINUO", "Area": "Secado", "Estado": "Operativo"},
            {"TAG": "PLAT-05", "Nombre": "PLATAFORMA N°5 (Tina)", "Area": "Recepción", "Estado": "Operativo"}
        ]
        for e in equipos: save_row("Equipos", e)

        # Repuestos Reales
        repuestos = [
            {"SKU": "1001", "Desc": "BOQUILLA DE CORTE N.0 VICTOR", "Stock": 2, "Min": 1, "Ubic": "A1"},
            {"SKU": "1002", "Desc": "RODAMIENTO 6308-2Z-C3", "Stock": 4, "Min": 2, "Ubic": "B2"},
            {"SKU": "1003", "Desc": "CADENA BS 16B-2 (1 PULG)", "Stock": 0, "Min": 5, "Ubic": "C3"},
            {"SKU": "1004", "Desc": "CORDON TEFLON GRAFITADO 3/8", "Stock": 1, "Min": 2, "Ubic": "D4"}
        ]
        for r in repuestos: save_row("Repuestos", r)

        # Ordenes Pendientes Reales
        ordenes = [
            {"ID": 1, "Equipo": "TRITURADOR GRANDE", "Tarea": "Fuga de aceite reten", "Fecha": "2025-11-23", "Estado": "Pendiente", "Tecnico": "JOSE PAREDES"},
            {"ID": 2, "Equipo": "DIGESTOR N° 7", "Tarea": "Faja suelta transmisión", "Fecha": "2025-11-23", "Estado": "Pendiente", "Tecnico": "CARLOS LUQUE"}
        ]
        for o in ordenes: save_row("Ordenes", o)

# Ejecutar inicialización solo si hay cliente
client = get_google_sheet_client()
if client: check_and_seed()

# ==========================================
# 3. INTERFAZ GRÁFICA (APP)
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/900/900782.png", width=50)
st.sidebar.title("SAP PM Lite")
menu = st.sidebar.radio("Ir a:", ["Dashboard", "Equipos", "Crear Aviso", "Órdenes (OTs)", "Repuestos"])

if client:
    # Cargar datos
    df_eq = get_data("Equipos")
    df_rep = get_data("Repuestos")
    df_ot = get_data("Ordenes")

    if menu == "Dashboard":
        st.title("📊 Tablero de Control")
        col1, col2, col3 = st.columns(3)
        col1.metric("Equipos Activos", len(df_eq))
        
        # Validación segura para pendientes
        pendientes = 0
        if not df_ot.empty and 'Estado' in df_ot.columns:
            pendientes = len(df_ot[df_ot['Estado'] == 'Pendiente'])
        col2.metric("OTs Pendientes", pendientes, delta="Prioridad")
        
        # Validación segura para repuestos
        criticos = 0
        if not df_rep.empty and 'Stock' in df_rep.columns and 'Min' in df_rep.columns:
             # Convertir a número forzoso para evitar errores de texto en Excel
             df_rep['Stock'] = pd.to_numeric(df_rep['Stock'], errors='coerce').fillna(0)
             df_rep['Min'] = pd.to_numeric(df_rep['Min'], errors='coerce').fillna(0)
             criticos = len(df_rep[df_rep['Stock'] <= df_rep['Min']])
             
        col3.metric("Repuestos Bajos", criticos, delta="- Comprar", delta_color="inverse")
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if not df_ot.empty and 'Estado' in df_ot.columns:
                fig = px.pie(df_ot, names='Estado', title="Estado de Órdenes")
                st.plotly_chart(fig, use_container_width=True)

    elif menu == "Equipos":
        st.header("🏭 Listado de Equipos")
        st.dataframe(df_eq, use_container_width=True)
        with st.expander("➕ Nuevo Equipo"):
            with st.form("add_eq"):
                tag = st.text_input("Nombre")
                area = st.selectbox("Área", ["Cocción", "Recepción", "Molienda"])
                if st.form_submit_button("Guardar"):
                    save_row("Equipos", {"TAG": tag[:3], "Nombre": tag, "Area": area, "Estado": "Operativo"})
                    st.success("Guardado! Recarga la página.")
                    time.sleep(1)
                    st.rerun()

    elif menu == "Órdenes (OTs)":
        st.header("🛠️ Gestión de Órdenes")
        st.dataframe(df_ot)
        
        with st.expander("✅ Cerrar Orden"):
            if not df_ot.empty and 'Estado' in df_ot.columns:
                ots_p = df_ot[df_ot['Estado']=='Pendiente']
                if not ots_p.empty:
                    id_close = st.selectbox("Seleccionar OT", ots_p['ID'])
                    if st.button("Finalizar Tarea"):
                        st.info("Para cerrar OTs en esta versión, cambia el estado en Google Sheets a 'Completado'.")
                else:
                    st.write("No hay pendientes.")

    elif menu == "Repuestos":
        st.header("📦 Inventario")
        st.dataframe(df_rep)
        
        st.subheader("⚠️ Pedido Sugerido")
        if not df_rep.empty and 'Stock' in df_rep.columns:
            bajo_stock = df_rep[df_rep['Stock'] <= df_rep['Min']]
            st.dataframe(bajo_stock)
else:
    st.info("Esperando conexión... Verifica tus credenciales.")
