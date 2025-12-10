import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA
# ==========================================
st.set_page_config(page_title="Gestor Integral Rendering", layout="wide", page_icon="🏭")

# 🔴 INTERRUPTOR MAESTRO:
# True = Genera los datos de los 9 digestores automáticamente (Lo que pediste).
# False = Intenta leer tus Excels de Google Drive.
MODO_DEMO = True 

# Estilos CSS Profesionales
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #0d47a1; margin-bottom: 20px; }
    .kpi-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #0d47a1; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .alert-card { background-color: #ffebee; padding: 15px; border-radius: 10px; border-left: 5px solid #c62828; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GENERADOR DE DATA INTEGRAL (TU EJEMPLO)
# ==========================================
def generar_data_completa():
    """
    Crea la estructura relacional completa para los 9 Digestores.
    Llena: Activos, Materiales, BOM, Avisos, OTs y Monitoreo.
    """
    # --- A. DATA MAESTRA (ACTIVOS) ---
    activos = [
        {"TAG": "PL-REND", "Nombre": "Planta Rendering", "Nivel": "L2-Planta", "TAG_Padre": "ROOT"},
        {"TAG": "AR-COCC", "Nombre": "Área de Cocción", "Nivel": "L3-Area", "TAG_Padre": "PL-REND"},
    ]
    
    # Generar 9 Digestores y sus componentes
    for i in range(1, 10):
        dig_tag = f"EQ-DIG-{i:02d}"
        activos.append({"TAG": dig_tag, "Nombre": f"Digestor Continuo #{i}", "Nivel": "L4-Equipo", "TAG_Padre": "AR-COCC"})
        
        # Componentes del Digestor
        activos.append({"TAG": f"{dig_tag}-MTR", "Nombre": "Motor Principal 75HP", "Nivel": "L5-Componente", "TAG_Padre": dig_tag})
        activos.append({"TAG": f"{dig_tag}-TRM", "Nombre": "Transmisión (Fajas)", "Nivel": "L5-Componente", "TAG_Padre": dig_tag})
        activos.append({"TAG": f"{dig_tag}-RED", "Nombre": "Reductor Velocidad", "Nivel": "L5-Componente", "TAG_Padre": dig_tag})
        activos.append({"TAG": f"{dig_tag}-EJE", "Nombre": "Eje Central y Paletas", "Nivel": "L5-Componente", "TAG_Padre": dig_tag})

    df_activos = pd.DataFrame(activos)

    # --- B. MATERIALES (ALMACÉN) ---
    materiales = [
        {"SKU": "FAJ-B86", "Descripcion": "Faja en V - Perfil B86", "Marca": "Gates", "Stock": 50, "Ubicacion": "A-12"},
        {"SKU": "ROD-222", "Descripcion": "Rodamiento Esférico", "Marca": "SKF", "Stock": 4, "Ubicacion": "B-05"},
        {"SKU": "ACE-680", "Descripcion": "Aceite Sintético ISO 680", "Marca": "Mobil", "Stock": 200, "Ubicacion": "C-01"},
    ]
    df_mat = pd.DataFrame(materiales)

    # --- C. BOM (LISTA DE MATERIALES) ---
    # Asignamos Fajas B86 a todas las transmisiones de los digestores
    bom = []
    transmisiones = df_activos[df_activos['TAG'].str.contains("-TRM")]
    for _, row in transmisiones.iterrows():
        bom.append({"TAG_Equipo": row['TAG'], "SKU_Material": "FAJ-B86", "Cantidad": 4})
    
    df_bom = pd.DataFrame(bom)

    # --- D. GESTIÓN (AVISOS Y OTs) ---
    avisos = [
        {"ID": 101, "Fecha": "2023-10-01", "TAG_Equipo": "EQ-DIG-01-TRM", "Descripcion": "Ruido excesivo en fajas", "Estado": "Cerrado"},
        {"ID": 102, "Fecha": "2023-10-05", "TAG_Equipo": "EQ-DIG-05-MTR", "Descripcion": "Alta temperatura carcasa", "Estado": "Abierto"},
    ]
    ots = [
        {"OT": 5001, "TAG_Equipo": "EQ-DIG-01-TRM", "Tarea": "Cambio de Fajas", "Fecha_Prog": "2023-10-02", "Estado": "Cerrada"},
    ]
    df_avisos = pd.DataFrame(avisos)
    df_ots = pd.DataFrame(ots)

    # --- E. MONITOREO (DATA SENSORICA) ---
    # Generamos datos aleatorios para los últimos 30 días para el Digestor 1
    fechas = pd.date_range(end=datetime.today(), periods=30)
    data_kpi = []
    for fecha in fechas:
        # Simulamos una subida de temperatura
        temp = 60 + (fecha.day / 2) + np.random.normal(0, 2) 
        amp = 45 + np.random.normal(0, 5)
        data_kpi.append({"Fecha": fecha, "TAG_Equipo": "EQ-DIG-01", "Parametro": "Temperatura", "Valor": temp, "Unidad": "°C"})
        data_kpi.append({"Fecha": fecha, "TAG_Equipo": "EQ-DIG-01", "Parametro": "Amperaje", "Valor": amp, "Unidad": "A"})
    
    df_kpi = pd.DataFrame(data_kpi)

    return df_activos, df_mat, df_bom, df_avisos, df_ots, df_kpi

# ==========================================
# 3. CONEXIÓN A GOOGLE DRIVE (MODO REAL)
# ==========================================
def conectar_drive():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        # Helper para leer primera hoja si falla nombre
        def read_safe(filename, sheetname):
            try:
                return pd.DataFrame(client.open(filename).worksheet(sheetname).get_all_records())
            except:
                try:
                    return pd.DataFrame(client.open(filename).get_worksheet(0).get_all_records())
                except:
                    return pd.DataFrame()

        # Leemos los 3 archivos
        df_a = read_safe("1_DATA_MAESTRA", "ACTIVOS")
        df_m = read_safe("1_DATA_MAESTRA", "MATERIALES")
        df_b = read_safe("1_DATA_MAESTRA", "BOM")
        df_av = read_safe("2_GESTION_TRABAJO", "AVISOS")
        df_ot = read_safe("2_GESTION_TRABAJO", "ORDENES")
        df_k = read_safe("3_MONITOREO", "DATA")
        
        return df_a, df_m, df_b, df_av, df_ot, df_k
    except Exception as e:
        st.error(f"Error conexión: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ==========================================
# 4. CARGA DE DATOS (SELECTOR DEMO/REAL)
# ==========================================
@st.cache_data
def load_data():
    if MODO_DEMO:
        return generar_data_completa()
    else:
        return conectar_drive()

df_activos, df_mat, df_bom, df_avisos, df_ots, df_kpi = load_data()

# ==========================================
# 5. LOGICA RELACIONAL (CEREBRO)
# ==========================================
def obtener_jerarquia(padre):
    return df_activos[df_activos['TAG_Padre'] == padre]

def obtener_bom_equipo(tag):
    """Cruza Activos -> BOM -> Materiales"""
    if df_bom.empty or df_mat.empty: return pd.DataFrame()
    
    # 1. Filtra la BOM del equipo
    bom_eq = df_bom[df_bom['TAG_Equipo'] == tag]
    
    # 2. Cruza con materiales para tener descripciones
    merged = pd.merge(bom_eq, df_mat, left_on="SKU_Material", right_on="SKU", how="left")
    return merged

# ==========================================
# 6. INTERFAZ VISUAL INTEGRAL
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=50)
st.sidebar.title("Rendering Manager")
modo = st.sidebar.radio("Módulo:", ["🔍 Visión 360° (Integral)", "🌳 Árbol de Activos", "🛠️ Mantenimiento", "📈 Monitoreo"])

if MODO_DEMO:
    st.sidebar.warning("⚠️ MODO DEMO ACTIVO: Datos generados automáticamente (9 Digestores).")

# --- MODULO 1: VISION 360 (INTEGRAL) ---
if modo == "🔍 Visión 360° (Integral)":
    st.header("Visión Integral del Activo")
    st.markdown("Selecciona un equipo para ver **toda** su información (Técnica, Repuestos, Fallas y Gráficos) en una sola pantalla.")
    
    # Selectores en Cascada
    col1, col2, col3 = st.columns(3)
    plantas = df_activos[df_activos['Nivel'] == 'L2-Planta']['TAG'].unique()
    sel_planta = col1.selectbox("Planta", plantas)
    
    areas = df_activos[df_activos['TAG_Padre'] == sel_planta]['TAG'].unique()
    sel_area = col2.selectbox("Área", areas)
    
    equipos = df_activos[df_activos['TAG_Padre'] == sel_area]['TAG'].unique()
    sel_equipo = col3.selectbox("Equipo", equipos)
    
    if sel_equipo:
        st.divider()
        # BUSCAMOS TODA LA INFO DEL EQUIPO SELECCIONADO
        
        # 1. Componentes
        componentes = obtener_jerarquia(sel_equipo)
        
        # 2. Historial de OTs (Del equipo o sus componentes)
        tags_familia = [sel_equipo] + componentes['TAG'].tolist()
        ots_hist = df_ots[df_ots['TAG_Equipo'].isin(tags_familia)]
        
        # 3. Estado de Salud (KPIs)
        kpi_hist = df_kpi[df_kpi['TAG_Equipo'].isin(tags_familia)]
        
        # --- DASHBOARD VISUAL ---
        
        # Fila Superior: Datos Maestros y Componentes
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("🔩 Estructura & Componentes")
            st.dataframe(componentes[['TAG', 'Nombre', 'Nivel']], use_container_width=True)
            
            st.subheader("📦 Repuestos Críticos (BOM)")
            # Buscamos BOM de los componentes (ej: fajas de la transmisión)
            bom_total = pd.DataFrame()
            for comp in tags_familia:
                b = obtener_bom_equipo(comp)
                if not b.empty:
                    bom_total = pd.concat([bom_total, b])
            
            if not bom_total.empty:
                st.dataframe(bom_total[['TAG_Equipo', 'Descripcion', 'Cantidad', 'Stock']], use_container_width=True)
            else:
                st.info("No hay repuestos asignados.")

        with c2:
            st.subheader("🌡️ Tendencias de Monitoreo")
            if not kpi_hist.empty:
                param = st.selectbox("Parámetro", kpi_hist['Parametro'].unique())
                data_graf = kpi_hist[kpi_hist['Parametro'] == param]
                fig = px.line(data_graf, x='Fecha', y='Valor', color='TAG_Equipo', title=f"Evolución {param}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Sin datos de sensores para este equipo.")

        # Fila Inferior: Gestión
        st.subheader("📋 Gestión de Trabajo")
        col_ots, col_av = st.columns(2)
        with col_ots:
            st.caption("Órdenes de Trabajo")
            st.dataframe(ots_hist, use_container_width=True)
        with col_av:
            st.caption("Avisos Recientes")
            avisos_hist = df_avisos[df_avisos['TAG_Equipo'].isin(tags_familia)]
            st.dataframe(avisos_hist, use_container_width=True)

# --- MODULO 2: ARBOL DE ACTIVOS (CASCADA) ---
elif modo == "🌳 Árbol de Activos":
    st.header("Explorador Jerárquico")
    
    # Filtro Rápido
    filtro = st.text_input("🔍 Buscar TAG o Nombre:")
    if filtro:
        res = df_activos[df_activos['TAG'].str.contains(filtro, case=False) | df_activos['Nombre'].str.contains(filtro, case=False)]
        st.dataframe(res)
    else:
        st.dataframe(df_activos)

    st.markdown("---")
    st.write("**Estructura de Datos Actual (Ejemplo):**")
    st.json(df_activos.head().to_dict(orient='records'))

# --- MODULO 3: MANTENIMIENTO ---
elif modo == "🛠️ Mantenimiento":
    st.header("Backlog de Mantenimiento")
    st.metric("OTs Abiertas", len(df_ots[df_ots['Estado'] != 'Cerrada']))
    
    tab1, tab2 = st.tabs(["Avisos", "Ordenes"])
    with tab1: st.dataframe(df_avisos)
    with tab2: st.dataframe(df_ots)

# --- MODULO 4: MONITOREO ---
elif modo == "📈 Monitoreo":
    st.header("Análisis de Condición")
    if not df_kpi.empty:
        var = st.selectbox("Variable", df_kpi['Parametro'].unique())
        df_filt = df_kpi[df_kpi['Parametro'] == var]
        
        # Gráfico avanzado con Plotly
        fig = px.line(df_filt, x='Fecha', y='Valor', color='TAG_Equipo', markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_filt)
    else:
        st.info("No hay datos de monitoreo.")
