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
    .bom-tag { background-color: #e8f5e9; color: #2e7d32; padding: 3px 6px; border-radius: 4px; font-size: 12px; margin-left: 5px; border: 1px solid #c8e6c9; font-weight: bold;}
    .target-box { background-color: #fff3e0; padding: 15px; border-radius: 8px; border: 1px solid #ffb74d; margin-bottom: 15px; }
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

def asignar_repuesto_bom(tag_equipo, sku_repuesto, cantidad, notas):
    client = get_google_sheet_client()
    sh = client.open("SAP_MANTENIMIENTO_DB")
    try:
        ws = sh.worksheet("BOM")
    except:
        ws = sh.add_worksheet("BOM", 100, 5)
        ws.append_row(["TAG_Equipo", "SKU_Repuesto", "Cantidad", "Observacion"])
    
    # Validar si ya existe para sumar cantidad o avisar (Simplificado: Agregamos fila)
    ws.append_row([tag_equipo, sku_repuesto, cantidad, notas])

# ==========================================
# 3. INTERFAZ DE GESTIÓN
# ==========================================

def render_gestion_activos():
    st.header("🏭 Gestión de Activos y Materiales")
    
    df_eq = get_data("Equipos")
    df_rep = get_data("Repuestos")
    df_bom = get_data("BOM")

    if df_eq.empty:
        df_eq = pd.DataFrame(columns=["ID", "Nivel", "TAG_Padre", "TAG", "Nombre", "Area", "Criticidad", "Estado", "Especificacion"])
    if 'Especificacion' not in df_eq.columns: df_eq['Especificacion'] = ""

    tab1, tab2, tab3, tab4 = st.tabs(["🌳 Árbol Técnico", "➕ Crear Activo", "✏️ Editar", "🧩 Asignar Repuestos (BOM)"])

    # --- TAB 1: ÁRBOL VISUAL ---
    with tab1:
        st.info("Estructura Jerárquica Completa.")
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
                                # Conteo de BOM
                                bom_count = 0
                                if not df_bom.empty:
                                    bom_count = len(df_bom[df_bom['TAG_Equipo'] == c['TAG']])
                                
                                bom_tag = f"<span class='bom-tag'>🧩 {bom_count} Items</span>" if bom_count > 0 else ""
                                st.markdown(f"<div class='n6'>• 🔩 {c['Nombre']} {spec_comp} {bom_tag}</div>", unsafe_allow_html=True)

    # --- TAB 2: CREAR ---
    with tab2:
        st.subheader("Alta de Activo (Cascada)")
        # ... (Código de cascada idéntico al anterior para no alargar innecesariamente) ...
        # Copia aquí la lógica de cascada del mensaje anterior si la necesitas completa.
        # Para que funcione este ejemplo, pondré un placeholder funcional.
        niveles_map = {"L2-Planta": 1, "L3-Area": 2, "L4-Equipo": 3, "L5-Sistema": 4, "L6-Componente": 5}
        target_level = st.selectbox("1. Nivel a crear", list(niveles_map.keys()))
        
        # Simulación de cascada para el ejemplo (INTEGRAR TU LÓGICA DE CASCADA AQUÍ)
        st.info("ℹ️ Utiliza la lógica de cascada (Planta > Área > Equipo...) para seleccionar el padre correcto.")
        padre_seleccionado_tag = "DEMO" # Reemplazar con lógica real
        
        with st.form("alta_final"):
            c1, c2 = st.columns(2)
            tag_new = c1.text_input("TAG").upper()
            nom_new = c2.text_input("Nombre")
            c3, c4 = st.columns(2)
            spec_new = c3.text_input("Especificación", placeholder="Ej. Faja B86")
            crit = c4.select_slider("Criticidad", ["C", "B", "A"], value="B")
            if st.form_submit_button("Guardar"):
                d = {"Nivel": target_level, "TAG_Padre": padre_seleccionado_tag, "TAG": tag_new, "Nombre": nom_new, "Area": "General", "Criticidad": crit, "Especificacion": spec_new}
                guardar_activo(d)
                st.success("Creado"); time.sleep(1); st.rerun()

    # --- TAB 3: EDITAR ---
    with tab3:
        st.write("Módulo de Edición Rápida")
        # ... (Código de edición anterior) ...

    # --- TAB 4: BOM CON CASCADA (LO NUEVO) ---
    with tab4:
        st.subheader("🧩 Asignación de Materiales (BOM)")
        st.markdown("Selecciona el componente específico navegando por la jerarquía.")
        
        col_nav, col_assign = st.columns([1, 1])
        
        tag_objetivo = None
        nombre_objetivo = None
        spec_objetivo = None

        # --- LADO IZQUIERDO: NAVEGADOR EN CASCADA ---
        with col_nav:
            st.markdown("### 1. Buscar Componente")
            
            # 1. Planta
            plantas = df_eq[df_eq['Nivel'] == 'L2-Planta']
            if plantas.empty: st.stop()
            pl_sel = st.selectbox("🏢 Planta", plantas['TAG'] + " | " + plantas['Nombre'], key="bom_l2")
            tag_pl = pl_sel.split(" | ")[0]
            
            # 2. Área
            areas = df_eq[(df_eq['Nivel'] == 'L3-Area') & (df_eq['TAG_Padre'] == tag_pl)]
            if not areas.empty:
                ar_sel = st.selectbox("📍 Área", areas['TAG'] + " | " + areas['Nombre'], key="bom_l3")
                tag_ar = ar_sel.split(" | ")[0]
                
                # 3. Equipo
                equipos = df_eq[(df_eq['Nivel'] == 'L4-Equipo') & (df_eq['TAG_Padre'] == tag_ar)]
                if not equipos.empty:
                    eq_sel = st.selectbox("⚙️ Equipo", equipos['TAG'] + " | " + equipos['Nombre'], key="bom_l4")
                    tag_eq = eq_sel.split(" | ")[0]
                    
                    # 4. Sistema
                    sistemas = df_eq[(df_eq['Nivel'] == 'L5-Sistema') & (df_eq['TAG_Padre'] == tag_eq)]
                    if not sistemas.empty:
                        sis_sel = st.selectbox("🔧 Sistema", sistemas['TAG'] + " | " + sistemas['Nombre'], key="bom_l5")
                        tag_sis = sis_sel.split(" | ")[0]
                        
                        # 5. Componente (Target Final)
                        componentes = df_eq[(df_eq['Nivel'] == 'L6-Componente') & (df_eq['TAG_Padre'] == tag_sis)]
                        if not componentes.empty:
                            comp_sel = st.selectbox("🔩 Componente (Objetivo)", componentes['TAG'] + " | " + componentes['Nombre'], key="bom_l6")
                            tag_objetivo = comp_sel.split(" | ")[0]
                            nombre_objetivo = comp_sel.split(" | ")[1]
                            # Obtener spec
                            row_c = componentes[componentes['TAG'] == tag_objetivo].iloc[0]
                            spec_objetivo = row_c.get('Especificacion', 'Sin especificación')
                        else:
                            st.info(f"El sistema {tag_sis} no tiene componentes creados.")
                            # Permitir asignar al sistema si no hay componentes (opcional)
                            tag_objetivo = tag_sis
                            nombre_objetivo = sis_sel.split(" | ")[1]
                            spec_objetivo = "Nivel Sistema"
                    else:
                        st.info("Equipo sin sistemas.")
                        tag_objetivo = tag_eq
                        nombre_objetivo = eq_sel.split(" | ")[1]
                else:
                    st.warning("Área sin equipos.")
            else:
                st.warning("Planta sin áreas.")

        # --- LADO DERECHO: ASIGNACIÓN ---
        with col_assign:
            if tag_objetivo:
                st.markdown(f"""
                <div class='target-box'>
                    <strong>🎯 OBJETIVO SELECCIONADO:</strong><br>
                    {nombre_objetivo} <br>
                    <small>TAG: {tag_objetivo}</small><br>
                    <small>Spec: <em>{spec_objetivo}</em></small>
                </div>
                """, unsafe_allow_html=True)
                
                # Mostrar BOM Actual
                st.write("**📋 Lista de Materiales Actual:**")
                if not df_bom.empty:
                    bom_actual = df_bom[df_bom['TAG_Equipo'] == tag_objetivo]
                    if not bom_actual.empty:
                        # Cruzar datos
                        if not df_rep.empty:
                            df_rep['SKU'] = df_rep['SKU'].astype(str)
                            bom_actual['SKU_Repuesto'] = bom_actual['SKU_Repuesto'].astype(str)
                            merged = pd.merge(bom_actual, df_rep, left_on='SKU_Repuesto', right_on='SKU', how='left')
                            st.dataframe(merged[['SKU', 'Desc', 'Cantidad', 'Observacion']], hide_index=True)
                        else:
                            st.dataframe(bom_actual)
                    else:
                        st.caption("No hay repuestos asignados.")
                
                st.markdown("---")
                st.write("**➕ Agregar Repuesto**")
                
                # Buscador de Repuestos
                if df_rep.empty:
                    st.error("Almacén vacío.")
                else:
                    filtro_rep = st.text_input("🔍 Buscar en Almacén (Nombre o SKU):")
                    if filtro_rep:
                        mask = df_rep.apply(lambda x: filtro_rep.lower() in str(x).lower(), axis=1)
                        rep_opts = df_rep[mask]
                    else:
                        rep_opts = df_rep
                    
                    if not rep_opts.empty:
                        rep_sel = st.selectbox("Seleccionar Item:", rep_opts['SKU'].astype(str) + " | " + rep_opts['Desc'])
                        sku_final = rep_sel.split(" | ")[0]
                        desc_final = rep_sel.split(" | ")[1]
                        
                        c_cant, c_btn = st.columns([1, 1])
                        cant = c_cant.number_input("Cantidad", min_value=1.0, step=1.0)
                        notas = st.text_input("Nota (Opcional)", placeholder="Ej. Solo marca SKF")
                        
                        if c_btn.button("🔗 Vincular al Componente"):
                            asignar_repuesto_bom(tag_objetivo, sku_final, cant, notas)
                            st.success(f"Asignado: {desc_final} -> {nombre_objetivo}")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("No se encontraron repuestos con ese nombre.")

# ==========================================
# 4. MAIN
# ==========================================
def main():
    if not get_google_sheet_client(): return
    st.sidebar.title("SAP PM Lite")
    menu = st.sidebar.radio("Ir a:", ["Dashboard", "Gestión de Activos"])
    if menu == "Gestión de Activos": render_gestion_activos()
    elif menu == "Dashboard": st.title("KPIs - En construcción")

if __name__ == "__main__":
    main()
