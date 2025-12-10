import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import time

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="SAP PM Cloud - ISO 14224", layout="wide", page_icon="🏭")

# Estilos visuales mejorados
st.markdown("""
<style>
    .n2 { color: #b71c1c; font-size: 20px; font-weight: bold; border-bottom: 2px solid #b71c1c; margin-top: 15px; }
    .n3 { color: #0d47a1; font-size: 18px; font-weight: bold; margin-left: 20px; }
    .n4 { color: #1b5e20; font-size: 16px; font-weight: bold; margin-left: 40px; }
    .n5 { color: #e65100; font-size: 15px; margin-left: 60px; font-style: italic; }
    .n6 { color: #424242; font-size: 14px; margin-left: 80px; border-left: 2px solid #ddd; padding-left: 5px; }
    .existing-box { background-color: #e3f2fd; padding: 10px; border-radius: 5px; border-left: 5px solid #2196f3; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # 1. Intentar Secrets (Nube)
    if "gcp_service_account" in st.secrets:
        try:
            secrets = st.secrets["gcp_service_account"]
            creds_dict = {k: v for k, v in secrets.items()}
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"Error Secrets: {e}")
            return None
    # 2. Intentar Local (JSON)
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
            return pd.DataFrame(ws.get_all_records())
        except:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# ==========================================
# 2. FUNCIONES CRUD
# ==========================================
def guardar_activo(datos):
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    try:
        ws = sh.worksheet("Equipos")
    except:
        ws = sh.add_worksheet("Equipos", 100, 20)
        ws.append_row(["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado"])
    
    nuevo_id = int(time.time())
    # Aseguramos guardar como string para evitar errores de formato
    fila = [nuevo_id, datos['Nivel'], datos['TAG_Padre'], str(datos['TAG']), datos['Nombre'], datos['Area'], datos['Criticidad'], "Operativo"]
    ws.append_row(fila)

def modificar_activo(tag, campo, valor):
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    ws = sh.worksheet("Equipos")
    cell = ws.find(tag)
    if cell:
        headers = ws.row_values(1)
        if campo in headers:
            col_idx = headers.index(campo) + 1
            ws.update_cell(cell.row, col_idx, valor)
            return True
    return False

# ==========================================
# 3. INTERFAZ DE GESTIÓN
# ==========================================

def render_gestion_activos():
    st.header("🏭 Gestión de Activos (ISO 14224)")
    df = get_data("Equipos")
    if df.empty:
        df = pd.DataFrame(columns=["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado"])

    tab1, tab2, tab3 = st.tabs(["🌳 Árbol Visual", "➕ Crear (Cascada)", "✏️ Editar Rapido"])

    # --- TAB 1: ÁRBOL VISUAL ---
    with tab1:
        st.info("Estructura actual de la planta.")
        plantas = df[df['Nivel'] == 'L2-Planta']
        for _, p in plantas.iterrows():
            st.markdown(f"<div class='n2'>🏢 {p['Nombre']} ({p['TAG']})</div>", unsafe_allow_html=True)
            areas = df[df['TAG_Padre'] == p['TAG']]
            for _, a in areas.iterrows():
                with st.expander(f"📍 {a['Nombre']}"):
                    equipos = df[df['TAG_Padre'] == a['TAG']]
                    for _, e in equipos.iterrows():
                        st.markdown(f"<div class='n4'>⚙️ {e['Nombre']} [{e['TAG']}]</div>", unsafe_allow_html=True)
                        sistemas = df[df['TAG_Padre'] == e['TAG']]
                        for _, s in sistemas.iterrows():
                            st.markdown(f"<div class='n5'>↳ 🔧 {s['Nombre']}</div>", unsafe_allow_html=True)
                            componentes = df[df['TAG_Padre'] == s['TAG']]
                            for _, c in componentes.iterrows():
                                st.markdown(f"<div class='n6'>• 🔩 {c['Nombre']}</div>", unsafe_allow_html=True)

    # --- TAB 2: CREAR CON VISUALIZACIÓN DE EXISTENTES ---
    with tab2:
        st.subheader("Alta de Activo Asistida")
        
        # 1. Selección de Nivel
        niveles_map = {
            "L2-Planta": 1, "L3-Area": 2, "L4-Equipo": 3, "L5-Sistema": 4, "L6-Componente": 5
        }
        target_level = st.selectbox("1. ¿Qué nivel deseas crear?", list(niveles_map.keys()))
        
        padre_seleccionado_tag = ""
        nombre_padre_display = "Raíz"
        area_heredada = "General"
        
        # --- LÓGICA DE CASCADA PARA ENCONTRAR AL PADRE ---
        if target_level == "L2-Planta":
            padre_seleccionado_tag = "CORP"
            st.success("Creando una nueva Planta raíz.")
        
        else:
            st.markdown("⬇️ **Navega hasta la ubicación correcta:**")
            col_sel1, col_sel2 = st.columns(2)
            
            # PASO A: Seleccionar PLANTA
            plantas = df[df['Nivel'] == 'L2-Planta']
            if plantas.empty:
                st.error("Primero crea una Planta (L2).")
                st.stop()
                
            planta_sel = col_sel1.selectbox("🏢 Planta / Empresa:", plantas['TAG'] + " | " + plantas['Nombre'])
            tag_planta = planta_sel.split(" | ")[0]
            
            if target_level == "L3-Area":
                padre_seleccionado_tag = tag_planta
                nombre_padre_display = planta_sel.split(" | ")[1]

            # PASO B: Filtrar Áreas
            if niveles_map[target_level] > 2:
                areas = df[(df['Nivel'] == 'L3-Area') & (df['TAG_Padre'] == tag_planta)]
                if areas.empty:
                    st.warning(f"La planta {tag_planta} no tiene Áreas.")
                    st.stop()
                    
                area_sel = col_sel2.selectbox("📍 Área:", areas['TAG'] + " | " + areas['Nombre'])
                tag_area = area_sel.split(" | ")[0]
                area_heredada = areas[areas['TAG'] == tag_area].iloc[0]['Nombre']
                
                if target_level == "L4-Equipo":
                    padre_seleccionado_tag = tag_area
                    nombre_padre_display = area_sel.split(" | ")[1]
                
                # PASO C: Filtrar Equipos
                if niveles_map[target_level] > 3:
                    col_sel3, col_sel4 = st.columns(2)
                    equipos = df[(df['Nivel'] == 'L4-Equipo') & (df['TAG_Padre'] == tag_area)]
                    if equipos.empty:
                        st.warning(f"El área {tag_area} no tiene Equipos.")
                        st.stop()
                        
                    equipo_sel = col_sel3.selectbox("⚙️ Equipo:", equipos['TAG'] + " | " + equipos['Nombre'])
                    tag_equipo = equipo_sel.split(" | ")[0]
                    
                    if target_level == "L5-Sistema":
                        padre_seleccionado_tag = tag_equipo
                        nombre_padre_display = equipo_sel.split(" | ")[1]

                    # PASO D: Filtrar Sistemas
                    if niveles_map[target_level] > 4:
                        sistemas = df[(df['Nivel'] == 'L5-Sistema') & (df['TAG_Padre'] == tag_equipo)]
                        if sistemas.empty:
                            st.warning(f"El equipo {tag_equipo} no tiene Sistemas.")
                            st.stop()
                            
                        sistema_sel = col_sel4.selectbox("🔧 Sistema:", sistemas['TAG'] + " | " + sistemas['Nombre'])
                        tag_sistema = sistema_sel.split(" | ")[0]
                        
                        if target_level == "L6-Componente":
                            padre_seleccionado_tag = tag_sistema
                            nombre_padre_display = sistema_sel.split(" | ")[1]

        # --- AQUÍ ESTÁ LA ACTUALIZACIÓN: VISUALIZAR HERMANOS ---
        st.markdown("---")
        st.markdown(f"### 👁️ Elementos ya existentes en: *{nombre_padre_display}*")
        
        # Filtramos los items que ya existen bajo este mismo padre y mismo nivel
        # Para ver qué TAGs ya están ocupados
        hermanos = df[(df['Nivel'] == target_level) & (df['TAG_Padre'] == padre_seleccionado_tag)]
        
        if not hermanos.empty:
            st.info(f"Se encontraron {len(hermanos)} items creados. Revisa la lista para no repetir TAGs.")
            # Mostramos tabla limpia
            st.dataframe(
                hermanos[['TAG', 'Nombre', 'Criticidad', 'Estado']], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✨ No hay items creados en este nivel todavía. ¡Puedes empezar la serie!")

        # FORMULARIO FINAL
        st.markdown("---")
        with st.form("alta_final"):
            st.markdown(f"**Creando Nuevo: {target_level}**")
            c1, c2, c3 = st.columns(3)
            tag_new = c1.text_input("TAG Nuevo (Recomendado seguir secuencia)", placeholder="Ej. 001").upper()
            nom_new = c2.text_input("Nombre Técnico")
            crit = c3.select_slider("Criticidad", ["C", "B", "A"], value="B")
            
            if st.form_submit_button("💾 Crear Activo"):
                if tag_new and nom_new:
                    # Validar Duplicado Global
                    if not df.empty and tag_new in df['TAG'].values:
                        st.error(f"❌ Error: El TAG '{tag_new}' ya existe en la base de datos.")
                    else:
                        d = {
                            "Nivel": target_level, "TAG_Padre": padre_seleccionado_tag,
                            "TAG": tag_new, "Nombre": nom_new, 
                            "Area": area_heredada, "Criticidad": crit
                        }
                        guardar_activo(d)
                        st.success(f"✅ {nom_new} creado correctamente!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("⚠️ Debes completar TAG y Nombre.")

    # --- TAB 3: EDITAR ---
    with tab3:
        st.subheader("Edición Rápida")
        txt_search = st.text_input("Buscar Activo (TAG o Nombre):")
        if txt_search and not df.empty:
            mask = df.apply(lambda x: txt_search.lower() in str(x).lower(), axis=1)
            res = df[mask]
            if not res.empty:
                sel = st.selectbox("Seleccionar:", res['TAG'] + " - " + res['Nombre'])
                tag_e = sel.split(" - ")[0]
                curr = df[df['TAG'] == tag_e].iloc[0]
                
                c1, c2 = st.columns(2)
                n_nom = c1.text_input("Editar Nombre", value=curr['Nombre'])
                n_stat = c2.selectbox("Estado", ["Operativo", "Mantenimiento", "Baja"], index=0)
                
                if st.button("Actualizar"):
                    modificar_activo(tag_e, "Nombre", n_nom)
                    modificar_activo(tag_e, "Estado", n_stat)
                    st.success("Hecho")
                    time.sleep(1)
                    st.rerun()

# ==========================================
# 4. MAIN
# ==========================================
def main():
    if not get_google_sheet_client():
        st.error("Error credenciales.")
        return

    st.sidebar.title("SAP PM Lite")
    menu = st.sidebar.radio("Ir a:", ["Dashboard", "Gestión de Activos"])

    if menu == "Gestión de Activos":
        render_gestion_activos()
    
    elif menu == "Dashboard":
        st.title("KPIs")
        df = get_data("Equipos")
        if not df.empty:
            col1, col2 = st.columns(2)
            col1.metric("Activos Totales", len(df))
            col2.metric("Componentes", len(df[df['Nivel']=='L6-Componente']))

if __name__ == "__main__":
    main()
