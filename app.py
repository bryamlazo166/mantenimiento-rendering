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

st.markdown("""
<style>
    .n2 { color: #b71c1c; font-size: 20px; font-weight: bold; border-bottom: 2px solid #b71c1c; margin-top: 15px; }
    .n3 { color: #0d47a1; font-size: 18px; font-weight: bold; margin-left: 20px; }
    .n4 { color: #1b5e20; font-size: 16px; font-weight: bold; margin-left: 40px; }
    .n5 { color: #e65100; font-size: 15px; margin-left: 60px; font-style: italic; }
    .n6 { color: #424242; font-size: 14px; margin-left: 80px; border-left: 2px solid #ddd; padding-left: 5px; }
    .spec { color: #555; font-size: 12px; background-color: #f0f0f0; padding: 2px 6px; border-radius: 4px; margin-left: 10px; font-family: monospace; }
    .bom-tag { background-color: #fff3e0; color: #e65100; padding: 2px 5px; border-radius: 3px; font-size: 11px; margin-left: 5px; border: 1px solid #ffe0b2; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        try:
            secrets = st.secrets["gcp_service_account"]
            creds_dict = {k: v for k, v in secrets.items()}
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"Error Secrets: {e}")
            return None
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
# 2. CRUD
# ==========================================
def guardar_activo(datos):
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    try:
        ws = sh.worksheet("Equipos")
    except:
        ws = sh.add_worksheet("Equipos", 100, 20)
        ws.append_row(["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado", "Especificacion"])
    
    nuevo_id = int(time.time())
    fila = [nuevo_id, datos['Nivel'], datos['TAG_Padre'], str(datos['TAG']), datos['Nombre'], datos['Area'], datos['Criticidad'], "Operativo", datos.get('Especificacion', '')]
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

def asignar_repuesto_bom(tag_equipo, sku_repuesto, cantidad):
    """Vincula un repuesto a un equipo (BOM)"""
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    try:
        ws = sh.worksheet("BOM")
    except:
        ws = sh.add_worksheet("BOM", 100, 5)
        ws.append_row(["TAG_Equipo", "SKU_Repuesto", "Cantidad", "Observacion"])
    
    ws.append_row([tag_equipo, sku_repuesto, cantidad, "Asignado desde App"])

# ==========================================
# 3. INTERFAZ DE GESTIÓN
# ==========================================

def render_gestion_activos():
    st.header("🏭 Gestión de Activos y Repuestos (BOM)")
    
    # Cargar DataFrames
    df_eq = get_data("Equipos")
    df_rep = get_data("Repuestos")
    df_bom = get_data("BOM")

    if df_eq.empty:
        df_eq = pd.DataFrame(columns=["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado", "Especificacion"])
    if 'Especificacion' not in df_eq.columns: df_eq['Especificacion'] = ""

    tab1, tab2, tab3, tab4 = st.tabs(["🌳 Árbol Técnico", "➕ Crear Activo", "✏️ Editar", "🧩 Repuestos por Equipo (BOM)"])

    # --- TAB 1: ÁRBOL VISUAL MEJORADO ---
    with tab1:
        st.info("Visualización técnica de planta.")
        plantas = df_eq[df_eq['Nivel'] == 'L2-Planta']
        for _, p in plantas.iterrows():
            st.markdown(f"<div class='n2'>🏢 {p['Nombre']} ({p['TAG']})</div>", unsafe_allow_html=True)
            areas = df_eq[df_eq['TAG_Padre'] == p['TAG']]
            for _, a in areas.iterrows():
                with st.expander(f"📍 {a['Nombre']}"):
                    equipos = df_eq[df_eq['TAG_Padre'] == a['TAG']]
                    for _, e in equipos.iterrows():
                        spec_eq = f"<span class='spec'>{e['Especificacion']}</span>" if e['Especificacion'] else ""
                        st.markdown(f"<div class='n4'>⚙️ {e['Nombre']} {spec_eq}</div>", unsafe_allow_html=True)
                        
                        sistemas = df_eq[df_eq['TAG_Padre'] == e['TAG']]
                        for _, s in sistemas.iterrows():
                            st.markdown(f"<div class='n5'>↳ 🔧 {s['Nombre']}</div>", unsafe_allow_html=True)
                            
                            componentes = df_eq[df_eq['TAG_Padre'] == s['TAG']]
                            for _, c in componentes.iterrows():
                                spec_comp = f"<span class='spec'>{c['Especificacion']}</span>" if c['Especificacion'] else ""
                                
                                # Buscar si tiene repuestos asociados en el BOM
                                tiene_bom = ""
                                if not df_bom.empty:
                                    bom_count = len(df_bom[df_bom['TAG_Equipo'] == c['TAG']])
                                    if bom_count > 0:
                                        tiene_bom = f"<span class='bom-tag'>🧩 {bom_count} Repuestos vinculados</span>"

                                st.markdown(f"<div class='n6'>• 🔩 {c['Nombre']} {spec_comp} {tiene_bom}</div>", unsafe_allow_html=True)

    # --- TAB 2: CREAR (Igual que antes) ---
    with tab2:
        st.subheader("Alta de Activo Asistida")
        niveles_map = {"L2-Planta": 1, "L3-Area": 2, "L4-Equipo": 3, "L5-Sistema": 4, "L6-Componente": 5}
        target_level = st.selectbox("1. ¿Qué nivel deseas crear?", list(niveles_map.keys()))
        padre_seleccionado_tag = ""
        nombre_padre_display = "Raíz"
        area_heredada = "General"
        
        # ... (LÓGICA DE CASCADA EXISTENTE - RESUMIDA PARA EL EJEMPLO) ...
        # Copia aquí la misma lógica de cascada del mensaje anterior
        # Para que el código no sea infinito, asumo que mantienes la lógica de selección de padres aquí.
        # ...
        
        # Mockup rapido de la parte final del form para que funcione el copy-paste
        if target_level == "L2-Planta":
            padre_seleccionado_tag = "CORP"
        else:
             # Aquí iría el código completo de cascada del mensaje anterior
             # Por brevedad en esta respuesta, asegúrate de no borrar esa parte si copias/pegas.
             # Si necesitas el bloque completo dímelo, pero asumo que lo integras.
             st.info("⚠️ (Lógica de selección de padres mantenida del código anterior)")
             # Simulación para que no falle el ejemplo si no seleccionas nada
             padre_seleccionado_tag = "DEMO" 

        with st.form("alta_final"):
            c1, c2 = st.columns(2)
            tag_new = c1.text_input("TAG Nuevo").upper()
            nom_new = c2.text_input("Nombre Técnico")
            c3, c4 = st.columns(2)
            spec_new = c3.text_input("📝 Especificación (Texto Rápido)", placeholder="Ej. Faja B86")
            crit = c4.select_slider("Criticidad", ["C", "B", "A"], value="B")
            
            if st.form_submit_button("💾 Crear Activo"):
                d = {"Nivel": target_level, "TAG_Padre": padre_seleccionado_tag, "TAG": tag_new, "Nombre": nom_new, "Area": area_heredada, "Criticidad": crit, "Especificacion": spec_new}
                guardar_activo(d)
                st.success("Creado"); time.sleep(1); st.rerun()

    # --- TAB 3: EDITAR ---
    with tab3:
        st.write("Módulo de edición (código anterior)...")

    # --- TAB 4: BOM (LA NUEVA JOYA) ---
    with tab4:
        st.subheader("🧩 Asignación de Repuestos (BOM)")
        st.markdown("Vincula items del almacén a tus equipos para generar listas automáticas.")
        
        col_eq, col_rep = st.columns(2)
        
        # 1. Seleccionar Componente/Equipo
        # Filtramos para mostrar solo nivel 5 y 6 que son los que usan repuestos usualmente
        activos_mantenibles = df_eq[df_eq['Nivel'].isin(['L4-Equipo', 'L5-Sistema', 'L6-Componente'])]
        
        if activos_mantenibles.empty:
            st.warning("No hay equipos creados.")
        else:
            eq_sel = col_eq.selectbox("1. Seleccionar Equipo/Componente:", 
                                      activos_mantenibles['TAG'] + " | " + activos_mantenibles['Nombre'])
            tag_target = eq_sel.split(" | ")[0]
            
            # Mostrar BOM Actual
            st.markdown(f"**Repuestos asignados a: {tag_target}**")
            if not df_bom.empty:
                bom_actual = df_bom[df_bom['TAG_Equipo'] == tag_target]
                if not bom_actual.empty:
                    # Cruzar con tabla de repuestos para ver nombres
                    if not df_rep.empty:
                        # Asegurar tipos de datos str para el merge
                        bom_actual['SKU_Repuesto'] = bom_actual['SKU_Repuesto'].astype(str)
                        df_rep['SKU'] = df_rep['SKU'].astype(str)
                        
                        bom_view = pd.merge(bom_actual, df_rep, left_on='SKU_Repuesto', right_on='SKU', how='left')
                        st.dataframe(bom_view[['SKU', 'Desc', 'Cantidad', 'Stock']], use_container_width=True)
                    else:
                        st.dataframe(bom_actual)
                else:
                    st.info("No tiene repuestos vinculados aún.")

            # 2. Asignar Nuevo Repuesto
            st.markdown("---")
            st.write("➕ **Agregar del Almacén**")
            
            if df_rep.empty:
                st.error("Tu almacén de repuestos está vacío. Ve al módulo de Repuestos.")
            else:
                rep_sel = col_rep.selectbox("2. Buscar Repuesto en Stock:", 
                                         df_rep['SKU'].astype(str) + " | " + df_rep['Desc'])
                sku_target = rep_sel.split(" | ")[0]
                
                cant = st.number_input("Cantidad Utilizada (Unidades):", min_value=1, value=1)
                
                if st.button("🔗 Vincular Repuesto"):
                    asignar_repuesto_bom(tag_target, sku_target, cant)
                    st.success(f"Repuesto {sku_target} vinculado a {tag_target}")
                    time.sleep(1)
                    st.rerun()

# ==========================================
# 4. MAIN
# ==========================================
def main():
    if not get_google_sheet_client(): return
    st.sidebar.title("SAP PM Lite")
    menu = st.sidebar.radio("Ir a:", ["Dashboard", "Gestión de Activos"])
    if menu == "Gestión de Activos": render_gestion_activos()

if __name__ == "__main__":
    main()
