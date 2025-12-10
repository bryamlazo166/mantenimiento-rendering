import streamlit as st
import pandas as pd
import random

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
st.set_page_config(page_title="Gestor Activos Rendering", layout="wide", page_icon="🏭")

# --- FUNCIÓN GENERADORA DE EJEMPLO (TU SOLICITUD DE LOS 9 DIGESTORES) ---
def inicializar_data_ejemplo():
    """
    Si no hay datos, crea la estructura completa para la Planta de Rendering,
    específicamente el Área de Digestores con sus 9 equipos y componentes.
    """
    if 'df_activos' not in st.session_state:
        # 1. Niveles Superiores
        data = [
            {"ID": 1, "TAG": "PL-01", "Nombre": "Planta Rendering Principal", "Nivel": "L2-Planta", "TAG_Padre": "ROOT"},
            {"ID": 2, "TAG": "AR-DIG", "Nombre": "Área de Cocción (Digestores)", "Nivel": "L3-Area", "TAG_Padre": "PL-01"},
            {"ID": 3, "TAG": "AR-PREN", "Nombre": "Área de Prensado", "Nivel": "L3-Area", "TAG_Padre": "PL-01"},
        ]
        
        # 2. Generación Automática de los 9 Digestores y sus Sistemas
        id_counter = 4
        for i in range(1, 10): # Del 1 al 9
            num_dig = f"{i:02d}" # 01, 02...
            tag_dig = f"EQ-DIG-{num_dig}"
            
            # El Equipo Principal (Padre de los componentes)
            data.append({
                "ID": id_counter,
                "TAG": tag_dig,
                "Nombre": f"Digestor Continuo #{i}",
                "Nivel": "L4-Equipo",
                "TAG_Padre": "AR-DIG",
                "Categoria": "Cocción",
                "Especificaciones": "Capacidad 5 Ton/h, Vapor Indirecto"
            })
            id_counter += 1
            
            # --- COMPONENTES (HIJOS DEL DIGESTOR) ---
            # Sistema Motriz
            data.append({"ID": id_counter, "TAG": f"{tag_dig}-MTR", "Nombre": f"Motor Eléctrico Digestor {i}", "Nivel": "L5-Componente", "TAG_Padre": tag_dig, "Categoria": "Eléctrico", "Especificaciones": "75HP, 1800RPM, 440V"}); id_counter += 1
            
            # Transmisión (Aquí van tus fajas)
            data.append({"ID": id_counter, "TAG": f"{tag_dig}-TRM", "Nombre": f"Transmisión Digestor {i}", "Nivel": "L5-Componente", "TAG_Padre": tag_dig, "Categoria": "Mecánico", "Especificaciones": "Poleas C/Buje"}); id_counter += 1
            
            # Rodamientos/Chumaceras
            data.append({"ID": id_counter, "TAG": f"{tag_dig}-ROD-A", "Nombre": f"Chumacera Lado Carga {i}", "Nivel": "L5-Componente", "TAG_Padre": tag_dig, "Categoria": "Rodamiento", "Especificaciones": "SAF 22522"}); id_counter += 1
            data.append({"ID": id_counter, "TAG": f"{tag_dig}-ROD-B", "Nombre": f"Chumacera Lado Libre {i}", "Nivel": "L5-Componente", "TAG_Padre": tag_dig, "Categoria": "Rodamiento", "Especificaciones": "SAF 22522"}); id_counter += 1

        # Guardamos en Session State (Simulando tu Excel)
        st.session_state.df_activos = pd.DataFrame(data)

    # --- DATAFRAME DE BOM (Repuestos asignados) ---
    if 'df_bom' not in st.session_state:
        # Asignamos Fajas B86 automáticamente a los sistemas de transmisión creados
        bom_data = []
        df = st.session_state.df_activos
        transmisiones = df[df['TAG'].str.contains("-TRM")]
        
        for _, row in transmisiones.iterrows():
            bom_data.append({
                "TAG_Equipo": row['TAG'], # Se asigna al componente "Transmisión"
                "Tipo_Repuesto": "Faja en V",
                "Modelo": "B86",
                "Cantidad": 4,
                "Observacion": "Cambio cada 6 meses"
            })
            
        st.session_state.df_bom = pd.DataFrame(bom_data)

# Ejecutamos la carga inicial
inicializar_data_ejemplo()

# Atajos para facilitar código
df = st.session_state.df_activos
df_bom = st.session_state.df_bom

# ==========================================
# 2. FUNCIONES DE UTILIDAD (LÓGICA)
# ==========================================
def obtener_siguiente_tag(nivel, padre_tag):
    """
    Genera automáticamente el siguiente TAG (Ej: Si existe EQ-DIG-09, genera EQ-DIG-10)
    """
    filtro = df[df['Nivel'] == nivel]
    if filtro.empty:
        return f"{padre_tag}-01"
    
    # Lógica simple de autoincremento (se puede sofisticar)
    count = len(filtro) + 1
    if nivel == "L4-Equipo":
        prefix = "EQ"
    elif nivel == "L5-Componente":
        prefix = "CMP"
    else:
        prefix = "NEW"
        
    return f"{padre_tag}-{prefix}-{count:02d}"

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================
st.title("🏭 Maestro de Activos & Componentes")
st.markdown("Gestión Jerárquica: Planta > Área > Equipo > Componente")

tab1, tab2, tab3 = st.tabs(["🌳 Árbol de Equipos (Cascada)", "➕ Crear Equipo Nuevo", "🔧 Asignar Repuesto (BOM)"])

# --- TAB 1: VISUALIZADOR EN CASCADA ---
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Nivel Planta
    plantas = df[df['Nivel'] == 'L2-Planta']['TAG'].unique()
    sel_planta = col1.selectbox("1. Seleccionar Planta", plantas)
    
    # 2. Nivel Área (Filtrado por Planta)
    areas = df[df['TAG_Padre'] == sel_planta]['TAG'].unique()
    sel_area = col2.selectbox("2. Seleccionar Área", areas)
    
    # 3. Nivel Equipo (Filtrado por Área)
    equipos = df[(df['TAG_Padre'] == sel_area) & (df['Nivel'] == 'L4-Equipo')]['TAG'].unique()
    sel_equipo = col3.selectbox("3. Seleccionar Equipo", equipos)
    
    # 4. Mostrar Info
    if sel_equipo:
        st.divider()
        equipo_data = df[df['TAG'] == sel_equipo].iloc[0]
        st.subheader(f"{equipo_data['Nombre']} ({sel_equipo})")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info(f"**Especificaciones:** {equipo_data['Especificaciones']}")
            
        with c2:
            st.markdown("#### 🔩 Componentes Instalados")
            # Filtrar componentes hijos de este equipo
            componentes = df[df['TAG_Padre'] == sel_equipo]
            
            if not componentes.empty:
                st.dataframe(componentes[['TAG', 'Nombre', 'Categoria', 'Especificaciones']], use_container_width=True)
                
                # Ver si hay BOM (Fajas B86, etc)
                st.markdown("#### 📦 Repuestos Asignados (BOM)")
                # Buscamos BOM asociada a cualquiera de los componentes listados o al equipo
                tags_familia = [sel_equipo] + componentes['TAG'].tolist()
                bom_asociada = df_bom[df_bom['TAG_Equipo'].isin(tags_familia)]
                
                if not bom_asociada.empty:
                    st.table(bom_asociada)
                else:
                    st.caption("No hay repuestos (fajas/rodamientos) asignados aún.")
            else:
                st.warning("Este equipo no tiene componentes desglosados.")

# --- TAB 2: CREAR EQUIPO/COMPONENTE (ESCALABLE) ---
with tab2:
    st.subheader("Alta de Nuevos Activos")
    
    c_padre, c_nivel = st.columns(2)
    
    # Selección inteligente del padre para mantener la cascada
    padre_opciones = df['TAG'].tolist()
    tag_padre = c_padre.selectbox("Seleccione TAG Padre (Donde se instalará)", padre_opciones, index=len(padre_opciones)-1)
    
    nivel_nuevo = c_nivel.selectbox("Nivel del Nuevo Activo", ["L3-Area", "L4-Equipo", "L5-Componente"])
    
    # Generar TAG sugerido
    tag_sugerido = obtener_siguiente_tag(nivel_nuevo, tag_padre)
    
    with st.form("nuevo_equipo"):
        col_a, col_b = st.columns(2)
        nuevo_tag = col_a.text_input("TAG (Automático/Editable)", value=tag_sugerido)
        nuevo_nombre = col_b.text_input("Nombre del Activo")
        nueva_cat = col_a.selectbox("Categoría", ["Mecánico", "Eléctrico", "Instrumentación", "Estructura"])
        nueva_spec = col_b.text_area("Especificaciones Técnicas (Ej: Faja B86, Motor 5HP)")
        
        submitted = st.form_submit_button("💾 Guardar en Inventario")
        
        if submitted:
            # Validación de duplicados
            if nuevo_tag in df['TAG'].values:
                st.error("❌ Error: Ese TAG ya existe en la base de datos.")
            else:
                nuevo_registro = {
                    "ID": df['ID'].max() + 1,
                    "TAG": nuevo_tag,
                    "Nombre": nuevo_nombre,
                    "Nivel": nivel_nuevo,
                    "TAG_Padre": tag_padre,
                    "Categoria": nueva_cat,
                    "Especificaciones": nueva_spec
                }
                # Agregar al DataFrame en Session State
                st.session_state.df_activos = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
                st.success(f"✅ Activo {nuevo_tag} creado correctamente bajo {tag_padre}")
                st.rerun() # Recargar para ver cambios

# --- TAB 3: ASIGNACIÓN MASIVA (EJ: FAJAS B86) ---
with tab3:
    st.subheader("Asignación de Repuestos a Componentes")
    st.markdown("Usa esto para asignar **Fajas B86** o Rodamientos a múltiples equipos.")
    
    col_filtro, col_accion = st.columns([1, 2])
    
    with col_filtro:
        # Filtro para encontrar rápido dónde poner la faja
        filtro_txt = st.text_input("Filtrar equipos por nombre (ej: 'Transmisión')")
        
        if filtro_txt:
            # Buscar en el dataframe
            opciones = df[df['Nombre'].str.contains(filtro_txt, case=False, na=False)]
        else:
            opciones = df[df['Nivel'] == 'L5-Componente']
            
        equipo_destino = st.selectbox("Seleccionar Componente Destino", opciones['TAG'] + " | " + opciones['Nombre'])
    
    with col_accion:
        with st.form("add_bom"):
            st.write(f"Asignando a: **{equipo_destino}**")
            c1, c2, c3 = st.columns(3)
            r_tipo = c1.text_input("Repuesto", value="Faja en V")
            r_modelo = c2.text_input("Modelo/Medida", value="B86")
            r_cant = c3.number_input("Cantidad", min_value=1, value=2)
            r_obs = st.text_input("Observación", "Instalación par")
            
            btn_bom = st.form_submit_button("🔗 Vincular Repuesto")
            
            if btn_bom:
                tag_limpio = equipo_destino.split(" | ")[0]
                nueva_bom = {
                    "TAG_Equipo": tag_limpio,
                    "Tipo_Repuesto": r_tipo,
                    "Modelo": r_modelo,
                    "Cantidad": r_cant,
                    "Observacion": r_obs
                }
                st.session_state.df_bom = pd.concat([df_bom, pd.DataFrame([nueva_bom])], ignore_index=True)
                st.success("Repuesto asignado.")
                st.rerun()

# --- VISUALIZACIÓN DE LA TABLA MAESTRA (PARA QUE VEAS LOS DATOS) ---
st.markdown("---")
with st.expander("Ver Base de Datos Completa (Excel Virtual)"):
    st.dataframe(st.session_state.df_activos)
