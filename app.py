import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import io

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Sistema Integral Rendering", layout="wide", page_icon="🏭")
st.title("🏭 Sistema Integral de Gestión de Activos (Rendering)")
st.markdown("---")

# ==========================================
# 2. GENERADOR DE DATA MAESTRA (TU ESTRUCTURA REAL)
# ==========================================
@st.cache_data
def generar_data_ejemplo():
    # --- A. ARCHIVO 1: DATA MAESTRA ---
    
    # 1. HOJA: ACTIVOS (Columnas exactas de tu CSV)
    activos_data = []
    # Jerarquía Superior
    activos_data.append(["PL-REND", "Planta Rendering Principal", "L2-Planta", "ROOT", "General", "A", "Operativo", "Planta Completa", "CC-01", "2010-01-01"])
    activos_data.append(["AR-DIG", "Área de Digestores", "L3-Area", "PL-REND", "Cocción", "A", "Operativo", "Zona de Cocción", "CC-02", "2010-01-01"])
    
    # BUCLE: Generar los 9 Digestores y sus componentes
    for i in range(1, 10):
        tag_dig = f"EQ-DIG-{i:02d}" # EQ-DIG-01...
        # Nivel 4: El Equipo
        activos_data.append([tag_dig, f"Digestor Continuo #{i}", "L4-Equipo", "AR-DIG", "Cocción", "A", "Operativo", "Capacidad 5T/h, Vapor Indirecto", "CC-02", "2015-06-01"])
        
        # Nivel 5: Sus Componentes (Cascada)
        activos_data.append([f"{tag_dig}-MTR", f"Motor Eléctrico Dig.{i}", "L5-Componente", tag_dig, "Cocción", "B", "Operativo", "75HP, 1800RPM, 440V, Frame 365T", "CC-02", "2015-06-01"])
        activos_data.append([f"{tag_dig}-TRM", f"Transmisión (Sistema Fajas) Dig.{i}", "L5-Componente", tag_dig, "Cocción", "A", "Operativo", "Poleas 4 canales, Buje QD", "CC-02", "2015-06-01"])
        activos_data.append([f"{tag_dig}-ROD-LA", f"Chumacera Lado Accionamiento Dig.{i}", "L5-Componente", tag_dig, "Cocción", "A", "Operativo", "Soporte Pie, Rodamiento Esférico", "CC-02", "2015-06-01"])
        activos_data.append([f"{tag_dig}-ROD-LL", f"Chumacera Lado Libre Dig.{i}", "L5-Componente", tag_dig, "Cocción", "A", "Operativo", "Soporte Pie, Rodamiento Esférico", "CC-02", "2015-06-01"])

    df_activos = pd.DataFrame(activos_data, columns=["TAG", "Nombre", "Nivel", "TAG_Padre", "Area", "Criticidad", "Estado", "Especificacion_Tecnica", "Centro_Costo", "Fecha_Instalacion"])

    # 2. HOJA: MATERIALES
    materiales_data = [
        ["SKU-FAJ-B86", "Faja en V - Perfil B86", "Gates", "Hi-Power II", 50, 10, "Estante A-01", 15.50, "UND", "http://foto.com/faja"],
        ["SKU-ROD-222", "Rodamiento Esférico", "SKF", "22220 EK", 8, 2, "Estante B-05", 250.00, "UND", "http://foto.com/rod"],
        ["SKU-ACE-680", "Aceite Sintético Engranajes", "Mobil", "SHC 634", 200, 20, "Patio Aceites", 1200.00, "CIL", "http://foto.com/oil"],
        ["SKU-RET-100", "Retén de Aceite", "National", "4x5x0.5", 10, 4, "Estante C-02", 5.00, "UND", "http://foto.com/ret"]
    ]
    df_materiales = pd.DataFrame(materiales_data, columns=["SKU", "Descripcion", "Marca", "Modelo_Medida", "Stock_Actual", "Stock_Minimo", "Ubicacion_Almacen", "Costo_Unitario", "Unidad_Medida", "Link_Foto"])

    # 3. HOJA: BOM (Vinculación Activo <-> Material)
    bom_data = []
    # A todas las Transmisiones de los 9 digestores les asignamos 4 Fajas B86
    for i in range(1, 10):
        tag_trm = f"EQ-DIG-{i:02d}-TRM"
        tag_mtr = f"EQ-DIG-{i:02d}-MTR"
        tag_rod = f"EQ-DIG-{i:02d}-ROD-LA"
        
        bom_data.append([tag_trm, "SKU-FAJ-B86", 4, "Juego completo emparejado"])
        bom_data.append([tag_rod, "SKU-ROD-222", 1, "Montaje con manguito"])
        # Al motor no le ponemos BOM por ahora para variar el ejemplo
        
    df_bom = pd.DataFrame(bom_data, columns=["TAG_Equipo", "SKU_Material", "Cantidad", "Observacion"])

    # --- B. ARCHIVO 2: GESTIÓN TRABAJO ---
    
    # 4. HOJA: AVISOS
    avisos_data = [
        [1001, "2023-12-01", "08:30", "EQ-DIG-01-TRM", "Juan Op.", "Ruido y olor a quemado", "Alta", "Cerrado"],
        [1002, "2023-12-05", "14:00", "EQ-DIG-05-MTR", "Pedro Mant.", "Alta vibración", "Media", "Abierto"],
        [1003, "2023-12-10", "09:15", "EQ-DIG-09-ROD-LA", "Juan Op.", "Temperatura alta en chumacera", "Alta", "En Proceso"]
    ]
    df_avisos = pd.DataFrame(avisos_data, columns=["ID_Aviso", "Fecha_Reporte", "Hora_Reporte", "TAG_Equipo", "Solicitante", "Sintoma_Falla", "Prioridad", "Estado_Aviso"])

    # 5. HOJA: ORDENES
    ot_data = [
        [5001, 1001, "EQ-DIG-01-TRM", "Cambio de Fajas B86 y alineamiento", "Correctivo", "2023-12-02", "2023-12-02", "2023-12-02", "Cerrado", "Interno"],
        [5002, 1003, "EQ-DIG-09-ROD-LA", "Inspección y Engrase", "Preventivo", "2023-12-11", "2023-12-11", "", "En Progreso", "Interno"]
    ]
    df_ots = pd.DataFrame(ot_data, columns=["ID_OT", "ID_Aviso_Vinculado", "TAG_Equipo", "Descripcion_Trabajo", "Tipo_Mtto", "Fecha_Programada", "Fecha_Inicio_Real", "Fecha_Fin_Real", "Estado_OT", "Tipo_Proveedor"])

    # --- C. ARCHIVO 3: MONITOREO ---

    # 6. HOJA: PUNTOS_MEDIDA (Configuración)
    puntos_data = []
    # Generamos puntos de monitoreo para los 9 digestores
    for i in range(1, 10):
        # Punto de temperatura en rodamiento lado accionamiento
        puntos_data.append([f"PM-DIG-{i:02d}-TMP", f"EQ-DIG-{i:02d}-ROD-LA", "Chumacera", "Temperatura", 0, 75, "°C"])
        # Punto de vibración en motor
        puntos_data.append([f"PM-DIG-{i:02d}-VIB", f"EQ-DIG-{i:02d}-MTR", "Motor", "Vibración", 0, 4.5, "mm/s"])
    
    df_puntos = pd.DataFrame(puntos_data, columns=["ID_Punto", "TAG_Equipo", "Componente", "Variable", "Valor_Alarma_Min", "Valor_Alarma_Max", "Unidad"])

    # 7. HOJA: LECTURAS (Historial)
    lecturas_data = []
    # Simulamos lecturas para el Digestor 01 y 09
    fecha_base = datetime.today() - timedelta(days=30)
    for d in range(30):
        fecha = (fecha_base + timedelta(days=d)).strftime("%Y-%m-%d")
        
        # Digestor 1 (Temperatura subiendo -> Falla)
        val_temp = 60 + (d * 0.8) + np.random.uniform(-1, 1) 
        estado = "Normal" if val_temp < 75 else "Alarma"
        lecturas_data.append([fecha, "PM-DIG-01-TMP", round(val_temp, 1), "Inspector A", estado])
        
        # Digestor 9 (Vibración estable)
        val_vib = 2.5 + np.random.uniform(-0.2, 0.2)
        lecturas_data.append([fecha, "PM-DIG-09-VIB", round(val_vib, 2), "Inspector B", "Normal"])

    df_lecturas = pd.DataFrame(lecturas_data, columns=["Fecha_Lectura", "ID_Punto", "Valor_Medido", "Inspector", "Estado"])

    return df_activos, df_materiales, df_bom, df_avisos, df_ots, df_puntos, df_lecturas

# Cargamos la data
df_activos, df_mat, df_bom, df_avisos, df_ots, df_puntos, df_lecturas = generar_data_ejemplo()

# ==========================================
# 3. LÓGICA DE INTEGRACIÓN (CRUCES)
# ==========================================

def get_full_asset_info(tag_seleccionado):
    """
    Esta función es el CORAZÓN del sistema. Une toda la info dispersa.
    """
    # 1. Info Básica
    info = df_activos[df_activos['TAG'] == tag_seleccionado].iloc[0].to_dict()
    
    # 2. BOM (Repuestos) - Cruzando BOM con MATERIALES
    bom_raw = df_bom[df_bom['TAG_Equipo'] == tag_seleccionado]
    if not bom_raw.empty:
        bom_full = pd.merge(bom_raw, df_mat, left_on="SKU_Material", right_on="SKU", how="left")
        info['BOM'] = bom_full[['SKU', 'Descripcion', 'Cantidad', 'Stock_Actual', 'Ubicacion_Almacen']]
    else:
        info['BOM'] = pd.DataFrame()

    # 3. Mantenimiento (OTs)
    ots = df_ots[df_ots['TAG_Equipo'] == tag_seleccionado]
    info['OTs'] = ots
    
    # 4. Monitoreo (Puntos y Última Lectura)
    puntos = df_puntos[df_puntos['TAG_Equipo'] == tag_seleccionado]
    # Cruzar puntos con la última lectura disponible
    if not puntos.empty and not df_lecturas.empty:
        lecturas_recientes = df_lecturas.sort_values('Fecha_Lectura').drop_duplicates('ID_Punto', keep='last')
        monitoreo_full = pd.merge(puntos, lecturas_recientes, on="ID_Punto", how="left")
        info['Monitoreo'] = monitoreo_full
    else:
        info['Monitoreo'] = pd.DataFrame()
        
    return info

# ==========================================
# 4. INTERFAZ DE USUARIO (INTEGRAL)
# ==========================================

# Sidebar
menu = st.sidebar.radio("Navegación", ["1. Navegador Técnico (Árbol)", "2. Gestión del Trabajo", "3. Descargar Data Ejemplo"])

if menu == "1. Navegador Técnico (Árbol)":
    col_tree, col_detail = st.columns([1, 2])
    
    # --- ÁRBOL DE EQUIPOS (CASCADA) ---
    with col_tree:
        st.subheader("Jerarquía de Activos")
        
        # Nivel 2: Planta
        plantas = df_activos[df_activos['Nivel'] == 'L2-Planta']
        planta_sel = st.selectbox("Planta", plantas['TAG'].unique())
        
        # Nivel 3: Area
        areas = df_activos[df_activos['TAG_Padre'] == planta_sel]
        area_sel = st.selectbox("Área", areas['TAG'].unique()) # Debería salir AR-DIG
        
        # Nivel 4: Equipos (Los 9 Digestores)
        equipos = df_activos[df_activos['TAG_Padre'] == area_sel]
        equipo_sel = st.selectbox("Equipo", equipos['TAG'].unique()) # EQ-DIG-01...
        
        # Nivel 5: Componentes
        componentes = df_activos[df_activos['TAG_Padre'] == equipo_sel]
        
        st.markdown(f"**Componentes de {equipo_sel}:**")
        comp_sel = None
        # Botones para seleccionar componente específico
        if not componentes.empty:
            for _, row in componentes.iterrows():
                if st.button(f"🔩 {row['Nombre']}", key=row['TAG']):
                    st.session_state['selected_tag'] = row['TAG']
        
        if st.button(f"🏭 Ver Equipo Completo ({equipo_sel})"):
            st.session_state['selected_tag'] = equipo_sel

    # --- DETALLE INTEGRAL ---
    with col_detail:
        if 'selected_tag' in st.session_state:
            tag_actual = st.session_state['selected_tag']
            data_integral = get_full_asset_info(tag_actual)
            
            st.header(f"{data_integral['Nombre']}")
            st.caption(f"TAG: {tag_actual} | Estado: {data_integral['Estado']} | Criticidad: {data_integral['Criticidad']}")
            
            st.info(f"📋 **Especificación:** {data_integral['Especificacion_Tecnica']}")
            
            # TABS PARA VER TODO UNIDO
            tab1, tab2, tab3 = st.tabs(["📦 Repuestos (BOM)", "🛠️ Historial Mantenimiento", "📈 Monitoreo Condición"])
            
            with tab1:
                st.subheader("Lista de Materiales Vinculada")
                if not data_integral['BOM'].empty:
                    st.dataframe(data_integral['BOM'], use_container_width=True)
                    
                else:
                    st.warning("No hay repuestos asociados directamente a este nivel.")
                    st.markdown("*Tip: Si estás viendo el Digestor, selecciona la 'Transmisión' para ver las fajas.*")

            with tab2:
                st.subheader("Órdenes de Trabajo")
                if not data_integral['OTs'].empty:
                    st.dataframe(data_integral['OTs'][['ID_OT', 'Descripcion_Trabajo', 'Fecha_Programada', 'Estado_OT']], use_container_width=True)
                else:
                    st.success("No hay OTs registradas.")

            with tab3:
                st.subheader("Sensores Asociados")
                if not data_integral['Monitoreo'].empty:
                    # Tabla resumen
                    st.dataframe(data_integral['Monitoreo'][['Componente', 'Variable', 'Valor_Medido', 'Unidad', 'Estado']], use_container_width=True)
                    
                    # Graficar historia si existe en general
                    puntos_ids = data_integral['Monitoreo']['ID_Punto'].tolist()
                    historia = df_lecturas[df_lecturas['ID_Punto'].isin(puntos_ids)]
                    
                    if not historia.empty:
                        fig = px.line(historia, x="Fecha_Lectura", y="Valor_Medido", color="ID_Punto", title="Tendencia Histórica")
                        st.plotly_chart(fig, use_container_width=True)
                        
                else:
                    st.info("No hay puntos de medida configurados para este activo.")

elif menu == "3. Descargar Data Ejemplo":
    st.header("📥 Descargar Archivos para tu Drive")
    st.markdown("Descarga estos Excel y súbelos a tu Google Drive reemplazando los vacíos. ¡Ya tienen los 9 digestores!")
    
    # Función para convertir DF a Excel en memoria
    def to_excel(df_dict):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, df in df_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        return output.getvalue()

    # 1. DATA MAESTRA
    xls_maestra = to_excel({"ACTIVOS": df_activos, "MATERIALES": df_mat, "BOM": df_bom})
    st.download_button("Descargar 1_DATA_MAESTRA.xlsx", data=xls_maestra, file_name="1_DATA_MAESTRA.xlsx")
    
    # 2. GESTION
    xls_gestion = to_excel({"AVISOS": df_avisos, "ORDENES": df_ots})
    st.download_button("Descargar 2_GESTION_TRABAJO.xlsx", data=xls_gestion, file_name="2_GESTION_TRABAJO.xlsx")
    
    # 3. MONITOREO
    xls_monitoreo = to_excel({"PUNTOS_MEDIDA": df_puntos, "LECTURAS": df_lecturas})
    st.download_button("Descargar 3_MONITOREO.xlsx", data=xls_monitoreo, file_name="3_MONITOREO.xlsx")
