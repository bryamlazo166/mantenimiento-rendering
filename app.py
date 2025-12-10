import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. CONEXIÓN Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Sistema Integral Rendering (Cloud)", layout="wide", page_icon="☁️")

# Estilos CSS
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .success-msg { color: #155724; background-color: #d4edda; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE CONEXIÓN SEGURA ---
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Intentar obtener credenciales de Secrets (Nube) o Local
    if "gcp_service_account" in st.secrets:
        creds_dict = {k:v for k,v in st.secrets["gcp_service_account"].items()}
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Fallback local
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        except:
            st.error("❌ No se encontraron credenciales (Secrets o JSON).")
            return None
    return gspread.authorize(creds)

# --- LECTURA DE DATOS (Con Caché inteligente) ---
@st.cache_data(ttl=60) # Recarga de Drive cada 60 segundos si no hay cambios manuales
def load_data_from_drive():
    client = get_client()
    if not client: return None, None, None, None, None, None

    def read_sheet(filename, sheetname):
        try:
            sh = client.open(filename)
            try:
                ws = sh.worksheet(sheetname)
            except:
                # Si no encuentra la hoja exacta, toma la primera
                ws = sh.get_worksheet(0)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error leyendo {filename}/{sheetname}: {e}")
            return pd.DataFrame()

    with st.spinner('☁️ Sincronizando con Google Drive...'):
        # 1. DATA MAESTRA
        df_activos = read_sheet("1_DATA_MAESTRA", "ACTIVOS")
        df_mat = read_sheet("1_DATA_MAESTRA", "MATERIALES")
        df_bom = read_sheet("1_DATA_MAESTRA", "BOM")
        
        # 2. GESTION
        df_ots = read_sheet("2_GESTION_TRABAJO", "ORDENES")
        
        # 3. MONITOREO
        df_lecturas = read_sheet("3_MONITOREO", "LECTURAS")
        
        # Conversión de tipos críticos
        if not df_activos.empty: df_activos['TAG'] = df_activos['TAG'].astype(str)
        
        return df_activos, df_mat, df_bom, df_ots, df_lecturas

# --- ESCRITURA DE DATOS (APPEND ROW) ---
def save_row_to_drive(filename, sheetname, row_dict):
    """Agrega una fila nueva al final del Excel en Drive"""
    client = get_client()
    try:
        sh = client.open(filename)
        try:
            ws = sh.worksheet(sheetname)
        except:
            ws = sh.get_worksheet(0)
            
        # Convertir diccionario a lista de valores respetando el orden de columnas si es posible,
        # o simplemente append de valores (gspread es inteligente)
        ws.append_row(list(row_dict.values()))
        
        st.cache_data.clear() # Limpiar caché para ver el dato nuevo inmediatamente
        return True
    except Exception as e:
        st.error(f"Error guardando en Drive: {e}")
        return False

# --- ESCRITURA MASIVA (UPDATE FULL SHEET) ---
def update_full_excel(filename, sheetname, df):
    """Sobreescribe toda la hoja (Usado para el editor masivo)"""
    client = get_client()
    try:
        sh = client.open(filename)
        try:
            ws = sh.worksheet(sheetname)
        except:
            ws = sh.get_worksheet(0)
            
        ws.clear()
        # gspread requiere lista de listas, incluyendo encabezados
        ws.update([df.columns.values.tolist()] + df.values.tolist())
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error actualizando Excel: {e}")
        return False

# CARGA INICIAL
df_activos, df_mat, df_bom, df_ots, df_lecturas = load_data_from_drive()

# Si falla la carga, detenemos
if df_activos is None:
    st.stop()

# ==========================================
# 2. LÓGICA DE FILTROS EN CASCADA (5 NIVELES)
# ==========================================
def filtro_cascada_5_niveles(key_prefix):
    """
    Navegación: Planta > Área > Equipo > Sistema > Componente
    """
    df = df_activos
    
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
    
    # Retornamos el TAG más profundo seleccionado y el contexto
    ultimo_tag = sel_comp if sel_comp else (sel_sistema if sel_sistema else (sel_equipo if sel_equipo else (sel_area if sel_area else sel_planta)))
    
    return {
        "planta": sel_planta, "area": sel_area, "equipo": sel_equipo, 
        "sistema": sel_sistema, "componente": sel_comp, "ultimo_tag": ultimo_tag
    }

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================
st.title("🏭 Sistema Integral Rendering (Conectado a Drive)")
st.caption("Los datos se guardan directamente en tus archivos Excel.")

menu = st.sidebar.radio("Módulos:", 
    ["1. Maestro de Activos", "2. Gestión Mantenimiento", "3. Monitoreo", "4. Almacén & BOM"])

# ------------------------------------------------------------------
# MÓDULO 1: MAESTRO DE ACTIVOS
# ------------------------------------------------------------------
if menu == "1. Maestro de Activos":
    tab_arbol, tab_nuevo, tab_edit = st.tabs(["🌳 Navegador", "➕ Crear Activo", "📝 Editar Excel"])
    
    # --- A. NAVEGADOR ---
    with tab_arbol:
        st.subheader("Explorador Jerárquico")
        ctx = filtro_cascada_5_niveles("nav")
        
        if ctx['ultimo_tag']:
            st.divider()
            tag = ctx['ultimo_tag']
            # Buscar info del activo seleccionado
            info_df = df_activos[df_activos['TAG'] == tag]
            
            if not info_df.empty:
                info = info_df.iloc[0]
                st.markdown(f"### {info.get('Nombre', 'Sin Nombre')} ({tag})")
                
                c1, c2 = st.columns(2)
                c1.info(f"**Nivel:** {info.get('Nivel','')}")
                c2.info(f"**Estado:** {info.get('Estado','Unknown')}")
                st.text_area("Especificaciones:", value=str(info.get('Especificacion_Tecnica','')), disabled=True)
                
                # Buscar Hijos
                hijos = df_activos[df_activos['TAG_Padre'] == tag]
                if not hijos.empty:
                    st.markdown("⬇️ **Componentes / Subsistemas:**")
                    st.dataframe(hijos[['TAG', 'Nombre', 'Nivel', 'Estado']], use_container_width=True)
                    
                else:
                    st.caption("No tiene elementos hijos registrados.")

    # --- B. CREAR ACTIVO ---
    with tab_nuevo:
        st.subheader("Alta de Activo en Google Drive")
        st.markdown("Selecciona la ubicación (Padre) donde crearás el nuevo elemento:")
        
        ctx_add = filtro_cascada_5_niveles("add")
        padre = ctx_add['ultimo_tag']
        
        # Determinar nivel sugerido
        nivel_padre = df_activos[df_activos['TAG'] == padre]['Nivel'].iloc[0] if padre else "ROOT"
        niveles_map = {"L2-Planta": "L3-Area", "L3-Area": "L4-Equipo", "L4-Equipo": "L5-Sistema", "L5-Sistema": "L6-Componente"}
        sugerencia = niveles_map.get(nivel_padre, "L2-Planta")
        
        if padre:
            st.success(f"Padre: **{padre}**. Se sugiere crear un: **{sugerencia}**")
        
        with st.form("frm_add_asset"):
            c1, c2 = st.columns(2)
            # Pre-generar TAG
            new_tag = c1.text_input("TAG (Único)", value=f"{padre}-NEW" if padre else "")
            new_name = c2.text_input("Nombre Descriptivo")
            
            opciones_niv = ["L2-Planta", "L3-Area", "L4-Equipo", "L5-Sistema", "L6-Componente"]
            idx = opciones_niv.index(sugerencia) if sugerencia in opciones_niv else 0
            new_lvl = c1.selectbox("Nivel Jerárquico", opciones_niv, index=idx)
            
            new_spec = c2.text_area("Especificaciones Técnicas")
            
            if st.form_submit_button("💾 Guardar en Excel"):
                if new_tag in df_activos['TAG'].values:
                    st.error("Error: El TAG ya existe en el Excel.")
                else:
                    # Crear diccionario con las columnas exactas de tu CSV
                    new_row = {
                        "TAG": new_tag,
                        "Nombre": new_name,
                        "Nivel": new_lvl,
                        "TAG_Padre": padre,
                        "Area": ctx_add['area'] if ctx_add['area'] else "General",
                        "Criticidad": "B", # Default
                        "Estado": "Operativo",
                        "Especificacion_Tecnica": new_spec,
                        "Centro_Costo": "",
                        "Fecha_Instalacion": str(datetime.today().date())
                    }
                    if save_row_to_drive("1_DATA_MAESTRA", "ACTIVOS", new_row):
                        st.success("✅ Guardado en Drive exitosamente!")
                        st.rerun()

    # --- C. EDITOR MASIVO ---
    with tab_edit:
        st.subheader("Editor Masivo (Cuidado)")
        st.warning("Esto sobreescribirá la hoja 'ACTIVOS' en tu Excel.")
        
        df_editado = st.data_editor(df_activos, num_rows="dynamic", use_container_width=True, height=500)
        
        if st.button("🔴 Guardar TODOS los cambios en Drive"):
            if update_full_excel("1_DATA_MAESTRA", "ACTIVOS", df_editado):
                st.success("Base de datos actualizada correctamente.")
                st.rerun()

# ------------------------------------------------------------------
# MÓDULO 2: GESTIÓN MANTENIMIENTO
# ------------------------------------------------------------------
if menu == "2. Gestión Mantenimiento":
    st.subheader("🛠️ Avisos y Órdenes de Trabajo")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### Crear Orden de Trabajo")
        # Selector simple
        all_tags = df_activos['TAG'].unique()
        
        with st.form("frm_ot"):
            tag_ot = st.selectbox("Equipo Afectado", all_tags)
            desc_ot = st.text_area("Descripción del Trabajo")
            tipo_ot = st.selectbox("Tipo", ["Correctivo", "Preventivo", "Predictivo"])
            fecha_ot = st.date_input("Fecha Programada")
            
            if st.form_submit_button("Generar OT"):
                # Calcular nuevo ID
                new_id = int(df_ots['ID_OT'].max()) + 1 if not df_ots.empty and 'ID_OT' in df_ots.columns else 5000
                
                row_ot = {
                    "ID_OT": new_id,
                    "ID_Aviso_Vinculado": "",
                    "TAG_Equipo": tag_ot,
                    "Descripcion_Trabajo": desc_ot,
                    "Tipo_Mtto": tipo_ot,
                    "Fecha_Programada": str(fecha_ot),
                    "Fecha_Inicio_Real": "",
                    "Fecha_Fin_Real": "",
                    "Estado_OT": "Abierta",
                    "Tipo_Proveedor": "Interno"
                }
                if save_row_to_drive("2_GESTION_TRABAJO", "ORDENES", row_ot):
                    st.success(f"OT #{new_id} creada en Drive.")
                    st.rerun()
                    
    with col2:
        st.markdown("#### Listado de OTs (Drive)")
        st.dataframe(df_ots, use_container_width=True)

# ------------------------------------------------------------------
# MÓDULO 3: MONITOREO
# ------------------------------------------------------------------
if menu == "3. Monitoreo":
    st.subheader("📈 Registro de Lecturas")
    
    # Filtro cascada para encontrar el punto exacto
    ctx_mon = filtro_cascada_5_niveles("mon")
    tag_mon = ctx_mon['ultimo_tag']
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown(f"**Registrar para: {tag_mon}**")
        if tag_mon:
            with st.form("frm_lectura"):
                var = st.selectbox("Variable", ["Temperatura", "Vibración", "Amperaje"])
                val = st.number_input("Valor", step=0.1)
                insp = st.text_input("Inspector", value="Operador")
                
                if st.form_submit_button("Grabar Lectura"):
                    row_lec = {
                        "Fecha_Lectura": str(datetime.now()),
                        "ID_Punto": f"PM-{tag_mon}-{var[:3].upper()}", # ID generado al vuelo
                        "Valor_Medido": val,
                        "Inspector": insp,
                        "Estado": "Registrado"
                    }
                    if save_row_to_drive("3_MONITOREO", "LECTURAS", row_lec):
                        st.success("Lectura guardada.")
                        st.rerun()
                        
    with c2:
        st.markdown("**Tendencias Históricas**")
        if not df_lecturas.empty and tag_mon:
            # Filtrar por aproximación de ID (ya que el ID_Punto contiene el TAG)
            mask = df_lecturas['ID_Punto'].str.contains(tag_mon, na=False)
            historia = df_lecturas[mask]
            
            if not historia.empty:
                fig = px.line(historia, x="Fecha_Lectura", y="Valor_Medido", color="ID_Punto", markers=True)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("No hay datos históricos para este equipo.")

# ------------------------------------------------------------------
# MÓDULO 4: ALMACÉN
# ------------------------------------------------------------------
if menu == "4. Almacén & BOM":
    t1, t2 = st.tabs(["Materiales", "BOM (Vinculación)"])
    
    with t1:
        st.subheader("Maestro de Materiales")
        df_mat_ed = st.data_editor(df_mat, num_rows="dynamic", use_container_width=True)
        if st.button("Guardar Cambios Materiales"):
            update_full_excel("1_DATA_MAESTRA", "MATERIALES", df_mat_ed)
            
    with t2:
        st.subheader("Asignar Repuestos a Equipos")
        c1, c2, c3 = st.columns(3)
        
        tags = df_activos['TAG'].unique()
        skus = df_mat['SKU'].unique() if not df_mat.empty else []
        
        with st.form("frm_bom"):
            s_tag = c1.selectbox("Activo", tags)
            s_sku = c2.selectbox("Repuesto", skus)
            s_cant = c3.number_input("Cantidad", min_value=1)
            s_obs = st.text_input("Observación")
            
            if st.form_submit_button("Vincular"):
                row_bom = {
                    "TAG_Equipo": s_tag,
                    "SKU_Material": s_sku,
                    "Cantidad": s_cant,
                    "Observacion": s_obs
                }
                if save_row_to_drive("1_DATA_MAESTRA", "BOM", row_bom):
                    st.success("Vinculación creada.")
                    st.rerun()
        
        st.dataframe(df_bom, use_container_width=True)
