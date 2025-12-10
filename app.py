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

# --- ESTILOS VISUALES JERARQUÍA ---
st.markdown("""
<style>
    .n2 { color: #b71c1c; font-size: 20px; font-weight: bold; border-bottom: 2px solid #b71c1c; margin-top: 15px; }
    .n3 { color: #0d47a1; font-size: 18px; font-weight: bold; margin-left: 20px; }
    .n4 { color: #1b5e20; font-size: 16px; font-weight: bold; margin-left: 40px; }
    .n5 { color: #e65100; font-size: 15px; margin-left: 60px; font-style: italic; }
    .n6 { color: #424242; font-size: 14px; margin-left: 80px; border-left: 2px solid #ddd; padding-left: 5px; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # 1. Intento Nube (Secrets)
    if "gcp_service_account" in st.secrets:
        try:
            secrets = st.secrets["gcp_service_account"]
            creds_dict = {k: v for k, v in secrets.items()}
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"Error Secrets: {e}")
            return None
    # 2. Intento Local (JSON)
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
# 2. FUNCIONES DE BASE DE DATOS (CRUD)
# ==========================================

def guardar_activo(datos):
    """Guarda una nueva fila en Google Sheets"""
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    try:
        ws = sh.worksheet("Equipos")
    except:
        ws = sh.add_worksheet("Equipos", 100, 20)
        # Encabezados obligatorios
        ws.append_row(["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado"])
    
    nuevo_id = int(time.time())
    # Orden estricto de columnas
    fila = [nuevo_id, datos['Nivel'], datos['TAG_Padre'], datos['TAG'], datos['Nombre'], datos['Area'], datos['Criticidad'], "Operativo"]
    ws.append_row(fila)

def modificar_activo(tag, campo, valor):
    """Busca un TAG y actualiza una columna específica"""
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    ws = sh.worksheet("Equipos")
    
    cell = ws.find(tag)
    if cell:
        # Mapeo de nombres de columna a índices (1-based en gspread)
        headers = ws.row_values(1)
        if campo in headers:
            col_idx = headers.index(campo) + 1
            ws.update_cell(cell.row, col_idx, valor)
            return True
    return False

# ==========================================
# 3. LÓGICA DE ÁRBOL Y GESTIÓN
# ==========================================

def render_gestion_activos():
    st.header("🏭 Gestión Integral de Activos (ISO 14224)")
    
    # Cargar datos frescos
    df = get_data("Equipos")
    if df.empty:
        # Inicializar estructura si está vacía
        df = pd.DataFrame(columns=["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado"])

    tab1, tab2, tab3 = st.tabs(["🌳 Árbol de Jerarquía", "➕ Crear (Alta)", "✏️ Modificar / Editar"])

    # --- TAB 1: VISUALIZACIÓN ---
    with tab1:
        st.subheader("Estructura de Planta")
        
        # Filtro de Plantas
        plantas = df[df['Nivel'] == 'L2-Planta']
        if plantas.empty:
            st.warning("No hay plantas definidas.")
        else:
            sel_planta = st.selectbox("Filtrar por Planta:", ["Todas"] + list(plantas['Nombre'].unique()))
            
            if sel_planta != "Todas":
                tag_planta = plantas[plantas['Nombre'] == sel_planta].iloc[0]['TAG']
                df_view = df # Filtrado visual en el bucle
                plantas_loop = plantas[plantas['TAG'] == tag_planta]
            else:
                plantas_loop = plantas
                df_view = df

            # BUCLE RECURSIVO (Nivel 2 -> Nivel 6)
            for _, p in plantas_loop.iterrows():
                st.markdown(f"<div class='n2'>🏢 {p['Nombre']} <small>({p['TAG']})</small></div>", unsafe_allow_html=True)
                
                # Nivel 3: Áreas
                areas = df[df['TAG_Padre'] == p['TAG']]
                for _, a in areas.iterrows():
                    with st.expander(f"📍 {a['Nombre']}", expanded=False):
                        
                        # Nivel 4: Equipos
                        equipos = df[df['TAG_Padre'] == a['TAG']]
                        for _, e in equipos.iterrows():
                            st.markdown(f"<div class='n4'>⚙️ {e['Nombre']} <small>[{e['TAG']}]</small></div>", unsafe_allow_html=True)
                            
                            # Nivel 5: Sistemas
                            sistemas = df[df['TAG_Padre'] == e['TAG']]
                            for _, s in sistemas.iterrows():
                                st.markdown(f"<div class='n5'>↳ 🔧 {s['Nombre']}</div>", unsafe_allow_html=True)
                                
                                # Nivel 6: Componentes (EL QUE PEDISTE)
                                componentes = df[df['TAG_Padre'] == s['TAG']]
                                for _, c in componentes.iterrows():
                                    estado_icon = "🟢" if c['Estado'] == 'Operativo' else "🔴"
                                    st.markdown(f"<div class='n6'>{estado_icon} 🔩 {c['Nombre']} <small>({c['TAG']})</small></div>", unsafe_allow_html=True)

    # --- TAB 2: CREAR (ALTA) ---
    with tab2:
        st.subheader("Alta de Nuevo Elemento")
        
        col_lvl, col_parent = st.columns([1,2])
        
        nivel_options = {
            "L2-Planta": "Raíz (Empresa)",
            "L3-Area": "Ubicación (Cocción, Recepción)",
            "L4-Equipo": "Unidad (Digestor, Prensa)",
            "L5-Sistema": "Función (Motriz, Hidráulico)",
            "L6-Componente": "Mantenible (Motor, Reductor, Sello)"
        }
        
        nivel_key = col_lvl.selectbox("1. Nivel Jerárquico", list(nivel_options.keys()), format_func=lambda x: f"{x} - {nivel_options[x]}")
        
        # Lógica de Padres
        padre_tag = ""
        valid_parent = False
        
        if nivel_key == "L2-Planta":
            padre_tag = "CORP"
            valid_parent = True
            st.info("Creando una nueva Planta/Empresa.")
        else:
            # Definir quién es el padre requerido
            parent_map = {
                "L3-Area": "L2-Planta",
                "L4-Equipo": "L3-Area",
                "L5-Sistema": "L4-Equipo",
                "L6-Componente": "L5-Sistema"
            }
            nivel_padre = parent_map[nivel_key]
            
            # Buscar candidatos en la DB
            candidatos = df[df['Nivel'] == nivel_padre]
            
            if candidatos.empty:
                st.error(f"⚠️ No existen elementos de nivel superior ({nivel_padre}) para asignar. Crea el padre primero.")
            else:
                seleccion = col_parent.selectbox(f"2. Pertenece a ({nivel_padre}):", 
                                                 candidatos['TAG'] + " | " + candidatos['Nombre'])
                padre_tag = seleccion.split(" | ")[0]
                valid_parent = True

        if valid_parent:
            st.markdown("---")
            with st.form("frm_alta"):
                c1, c2, c3 = st.columns(3)
                tag_input = c1.text_input("TAG (Código Único)", placeholder="Ej. RED-01").upper().strip()
                nombre_input = c2.text_input("Nombre Técnico", placeholder="Ej. Reductor Principal")
                
                # Criticidad solo relevante de Equipo hacia abajo
                crit = c3.select_slider("Criticidad", ["C", "B", "A"], value="B")
                
                if st.form_submit_button("💾 Guardar Activo"):
                    if not tag_input or not nombre_input:
                        st.warning("TAG y Nombre son obligatorios.")
                    elif not df.empty and tag_input in df['TAG'].values:
                        st.error("¡El TAG ya existe! Usa uno diferente.")
                    else:
                        # Area se hereda del padre o se define
                        area_val = "General"
                        # Intentar heredar área si no es Planta
                        if nivel_key != "L2-Planta" and not df.empty:
                            try:
                                parent_row = df[df['TAG'] == padre_tag].iloc[0]
                                area_val = parent_row['Area'] if nivel_key != "L3-Area" else nombre_input
                            except:
                                pass
                        
                        nuevo_dato = {
                            "Nivel": nivel_key, "TAG_Padre": padre_tag, "TAG": tag_input,
                            "Nombre": nombre_input, "Area": area_val, "Criticidad": crit
                        }
                        guardar_activo(nuevo_dato)
                        st.success(f"{nivel_key} creado correctamente.")
                        time.sleep(1)
                        st.rerun()

    # --- TAB 3: MODIFICAR ---
    with tab3:
        st.subheader("Edición de Datos Maestros")
        
        search_q = st.text_input("🔍 Buscar por TAG o Nombre:", "")
        
        if not df.empty:
            # Filtrar
            if search_q:
                mask = df.apply(lambda x: search_q.lower() in str(x['TAG']).lower() or search_q.lower() in str(x['Nombre']).lower(), axis=1)
                df_filt = df[mask]
            else:
                df_filt = df
            
            if df_filt.empty:
                st.warning("No se encontraron resultados.")
            else:
                # Selector de activo a editar
                obj_sel = st.selectbox("Seleccionar Item:", df_filt['TAG'] + " - " + df_filt['Nombre'])
                tag_edit = obj_sel.split(" - ")[0]
                
                # Obtener datos actuales
                row = df[df['TAG'] == tag_edit].iloc[0]
                
                st.markdown(f"**Editando:** `{row['Nivel']}` > **{row['Nombre']}**")
                
                with st.form("frm_edit"):
                    ec1, ec2, ec3 = st.columns(3)
                    new_name = ec1.text_input("Nombre", value=row['Nombre'])
                    new_crit = ec2.selectbox("Criticidad", ["A", "B", "C"], index=["A", "B", "C"].index(row['Criticidad']) if row['Criticidad'] in ["A","B","C"] else 1)
                    new_stat = ec3.selectbox("Estado", ["Operativo", "Fuera de Servicio", "En Mantenimiento"], index=0)
                    
                    if st.form_submit_button("Actualizar Datos"):
                        modificar_activo(tag_edit, "Nombre", new_name)
                        modificar_activo(tag_edit, "Criticidad", new_crit)
                        modificar_activo(tag_edit, "Estado", new_stat)
                        st.success("Registro actualizado en la Nube.")
                        time.sleep(1)
                        st.rerun()

# ==========================================
# 4. MAIN & MENÚ LATERAL
# ==========================================
def main():
    if not get_google_sheet_client():
        st.error("Error de conexión. Verifica credentials.json")
        return

    st.sidebar.title("SAP PM Lite")
    menu = st.sidebar.radio("Navegación", ["Dashboard", "Gestión de Activos (ISO)", "Órdenes de Trabajo"])

    if menu == "Gestión de Activos (ISO)":
        render_gestion_activos()
    
    elif menu == "Dashboard":
        st.title("Tablero de Mando")
        df = get_data("Equipos")
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Activos", len(df))
            c2.metric("Componentes Mantenibles", len(df[df['Nivel']=='L6-Componente']))
            c3.metric("Equipos Críticos", len(df[df['Criticidad']=='A']))
            
            st.markdown("### Composición de Activos")
            fig = px.bar(df, x='Nivel', color='Criticidad', title="Jerarquía vs Criticidad")
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
