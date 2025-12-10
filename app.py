import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import time

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="SAP PM Cloud - MultiPlanta", layout="wide", page_icon="🏭")

# --- ESTILOS CSS PARA JERARQUÍA (NUEVO NIVEL 2) ---
st.markdown("""
<style>
    .nivel-2 { font-weight: bold; color: #d62728; font-size: 22px; margin-top: 10px; border-bottom: 2px solid #d62728; }
    .nivel-3 { font-weight: bold; color: #1f77b4; font-size: 18px; margin-left: 20px; }
    .nivel-4 { font-weight: bold; color: #2ca02c; margin-left: 40px; }
    .nivel-5 { color: #ff7f0e; margin-left: 60px; font-style: italic;}
    .nivel-6 { color: #555; margin-left: 80px; font-size: 14px;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # INTENTO 1: Secretos (Nube)
    if "gcp_service_account" in st.secrets:
        try:
            secrets = st.secrets["gcp_service_account"]
            creds_dict = {k: v for k, v in secrets.items()}
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"Error Secrets: {e}")
            return None
    # INTENTO 2: Local
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        return gspread.authorize(creds)
    except:
        return None

def get_data(sheet_name):
    client = get_google_sheet_client()
    if not client: return pd.DataFrame()
    try:
        sh = client.open("SAP_MANTENIMIENTO_DB")
        try:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# ==========================================
# 2. FUNCIONES CRUD
# ==========================================

def guardar_activo(datos):
    """Guarda un nuevo activo en la hoja Equipos"""
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    try:
        ws = sh.worksheet("Equipos")
    except:
        ws = sh.add_worksheet("Equipos", 100, 20)
        ws.append_row(["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado"])
    
    nuevo_id = int(time.time())
    # Asegurar que todos los campos se guarden como texto para evitar errores
    fila = [nuevo_id, datos['Nivel'], datos['TAG_Padre'], datos['TAG'], datos['Nombre'], datos['Area'], datos['Criticidad'], "Operativo"]
    ws.append_row(fila)

def actualizar_activo(tag_objetivo, columna, nuevo_valor):
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    ws = sh.worksheet("Equipos")
    cell = ws.find(tag_objetivo)
    if cell:
        headers = ws.row_values(1)
        try:
            col_index = headers.index(columna) + 1
            ws.update_cell(cell.row, col_index, nuevo_valor)
            return True
        except:
            return False
    return False

# ==========================================
# 3. MÓDULO DE ACTIVOS (LÓGICA ACTUALIZADA)
# ==========================================

def render_activos_iso():
    st.header("🏭 Gestión de Activos Multi-Planta")
    
    df = get_data("Equipos")
    if df.empty:
        st.warning("Base de datos vacía. Crea primero tus PLANTAS en la pestaña 'Nuevo Activo'.")
        df = pd.DataFrame(columns=["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado"])

    tab_ver, tab_nuevo, tab_edit = st.tabs(["🌳 Árbol Jerárquico", "➕ Nuevo Activo", "✏️ Modificar"])

    # --- TAB 1: VISUALIZACIÓN ---
    with tab_ver:
        st.subheader("Estructura Corporativa")
        
        # Filtro Global por Planta
        plantas_disponibles = df[df['Nivel'] == 'L2-Planta']['Nombre'].unique()
        filtro_planta = st.selectbox("Seleccionar Planta / Empresa:", ["Todas"] + list(plantas_disponibles))
        
        # Lógica de Filtrado
        if filtro_planta != "Todas":
            # Buscar el TAG de la planta seleccionada
            tag_planta = df[df['Nombre'] == filtro_planta].iloc[0]['TAG']
            # Filtrar solo esa planta (L2) y sus hijos recursivamente es complejo en pandas simple, 
            # así que filtraremos visualmente en el bucle.
            df_plantas = df[(df['Nivel'] == 'L2-Planta') & (df['TAG'] == tag_planta)]
        else:
            df_plantas = df[df['Nivel'] == 'L2-Planta']

        # BUCLE PRINCIPAL DE JERARQUÍA
        for _, n2 in df_plantas.iterrows():
            st.markdown(f"<div class='nivel-2'>🏢 {n2['Nombre']} <small>({n2['TAG']})</small></div>", unsafe_allow_html=True)
            
            # Buscar hijos Nivel 3 (Áreas)
            niveles_3 = df[(df['Nivel'] == 'L3-Area') & (df['TAG_Padre'] == n2['TAG'])]
            
            for _, n3 in niveles_3.iterrows():
                with st.expander(f"📍 {n3['Nombre']}", expanded=False):
                    
                    # Buscar hijos Nivel 4 (Equipos)
                    niveles_4 = df[(df['Nivel'] == 'L4-Equipo') & (df['TAG_Padre'] == n3['TAG'])]
                    
                    for _, n4 in niveles_4.iterrows():
                        st.markdown(f"<div class='nivel-4'>⚙️ {n4['Nombre']} <small>[{n4['TAG']}]</small></div>", unsafe_allow_html=True)
                        
                        # Buscar hijos Nivel 5 (Sistemas)
                        niveles_5 = df[(df['Nivel'] == 'L5-Sistema') & (df['TAG_Padre'] == n4['TAG'])]
                        for _, n5 in niveles_5.iterrows():
                            st.markdown(f"<div class='nivel-5'>↳ 🔧 {n5['Nombre']}</div>", unsafe_allow_html=True)
                            
                            # Buscar hijos Nivel 6 (Componentes)
                            niveles_6 = df[(df['Nivel'] == 'L6-Componente') & (df['TAG_Padre'] == n5['TAG'])]
                            for _, n6 in niveles_6.iterrows():
                                st.markdown(f"<div class='nivel-6'>&nbsp;&nbsp;&nbsp;• 🔩 {n6['Nombre']}</div>", unsafe_allow_html=True)

    # --- TAB 2: CREAR NUEVO (Lógica Padres) ---
    with tab_nuevo:
        st.subheader("Alta de Activo")
        
        col_niv, col_pad = st.columns([1, 2])
        
        # 1. Seleccionar Nivel
        nivel = col_niv.selectbox("1. Nivel Jerárquico", 
                               ["L2-Planta", "L3-Area", "L4-Equipo", "L5-Sistema", "L6-Componente"])
        
        # 2. Lógica de Padre
        padre_tag = ""
        
        if nivel == "L2-Planta":
            padre_tag = "GRUPO-CORP" # Raíz absoluta
            st.info("ℹ️ Estás creando una Empresa o Planta Principal.")
            st.markdown("**Ejemplo:** Planta Rendering 1, Planta Harinas 2.")
        
        else:
            # Mapa de quién es padre de quién
            mapa_padres = {
                "L3-Area": "L2-Planta",
                "L4-Equipo": "L3-Area",
                "L5-Sistema": "L4-Equipo",
                "L6-Componente": "L5-Sistema"
            }
            nivel_requerido = mapa_padres[nivel]
            
            # Buscar posibles padres en la base de datos
            posibles_padres = df[df['Nivel'] == nivel_requerido]
            
            if posibles_padres.empty:
                st.error(f"⛔ No puedes crear un '{nivel}' porque no existen padres de nivel '{nivel_requerido}'.")
                st.stop()
            
            padre_sel = col_pad.selectbox(f"2. Seleccionar {nivel_requerido} Superior:", 
                                       posibles_padres['TAG'] + " | " + posibles_padres['Nombre'])
            padre_tag = padre_sel.split(" | ")[0]

        st.markdown("---")
        with st.form("form_alta"):
            c1, c2, c3 = st.columns(3)
            tag = c1.text_input("TAG (Código Único)", placeholder="Ej. PLANTA-01").upper()
            nombre = c2.text_input("Nombre", placeholder="Ej. Rendering Norte")
            
            # El área funcional solo aplica a Equipos/Sistemas, para Planta ponemos "General"
            if nivel == "L2-Planta":
                area = "Corporativo"
            else:
                area = c3.selectbox("Área Funcional", ["Producción", "Mantenimiento", "Calidad", "Logística", "Servicios"])
                
            criticidad = st.select_slider("Criticidad", options=["C", "B", "A"])
            
            if st.form_submit_button("💾 Guardar en Nube"):
                if tag and nombre:
                    if not df.empty and tag in df['TAG'].values:
                        st.error("¡Ese TAG ya existe!")
                    else:
                        datos = {"Nivel": nivel, "TAG_Padre": padre_tag, "TAG": tag, "Nombre": nombre, "Area": area, "Criticidad": criticidad}
                        guardar_activo(datos)
                        st.success("Guardado! Recarga la página.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Nombre y TAG son obligatorios")

    # --- TAB 3: EDITAR ---
    with tab_edit:
        st.subheader("Editar Datos Maestros")
        if df.empty: return
        
        activo = st.selectbox("Buscar Activo:", df['TAG'] + " - " + df['Nombre'])
        tag_e = activo.split(" - ")[0]
        curr = df[df['TAG'] == tag_e].iloc[0]
        
        c1, c2 = st.columns(2)
        new_name = c1.text_input("Nombre", value=curr['Nombre'])
        
        if st.button("Actualizar"):
            actualizar_activo(tag_e, "Nombre", new_name)
            st.success("Actualizado")
            time.sleep(1)
            st.rerun()

# ==========================================
# 4. MAIN LOOP
# ==========================================

def main():
    client = get_google_sheet_client()
    if not client:
        st.error("Error de conexión. Verifica secretos.")
        return

    st.sidebar.title("SAP PM Lite")
    menu = st.sidebar.radio("Menú", ["Dashboard", "Gestión de Activos (ISO)", "Órdenes de Trabajo"])

    if menu == "Gestión de Activos (ISO)":
        render_activos_iso()
    
    elif menu == "Dashboard":
        st.title("📊 Dashboard Corporativo")
        df = get_data("Equipos")
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Activos", len(df))
            
            # Contar plantas
            plantas = len(df[df['Nivel'] == 'L2-Planta'])
            c2.metric("Plantas / Empresas", plantas)
            
            criticos = len(df[df['Criticidad'].str.contains("A", na=False)])
            c3.metric("Equipos Críticos", criticos)
            
            st.markdown("### Activos por Planta")
            # Unir tabla consigo misma para obtener nombre de planta para cada equipo (avanzado)
            # Para simplificar en el dashboard, mostramos por Nivel
            fig = px.bar(df, x='Nivel', title="Distribución Jerárquica")
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
