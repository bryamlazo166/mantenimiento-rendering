import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y ESTRUCTURA DE DATOS
# ==========================================
st.set_page_config(page_title="Sistema Integral Rendering", layout="wide", page_icon="🏭")

# Inicialización de la Base de Datos en Memoria
if 'df_activos' not in st.session_state:
    # Definimos columnas base
    st.session_state.df_activos = pd.DataFrame(columns=[
        "TAG", "Nombre", "Nivel", "TAG_Padre", "Area", "Estado", "Especificaciones"
    ])
    st.session_state.df_ots = pd.DataFrame(columns=["ID", "TAG_Equipo", "Descripcion", "Estado", "Fecha"])
    st.session_state.df_lecturas = pd.DataFrame(columns=["Fecha", "TAG", "Variable", "Valor", "Inspector"])

    # --- GENERADOR DE DATA DEMO (9 DIGESTORES CON SISTEMAS) ---
    data_demo = []
    
    # Nivel 2 y 3
    data_demo.append({"TAG": "PL-REND", "Nombre": "Planta Rendering", "Nivel": "L2-Planta", "TAG_Padre": "ROOT", "Area": "General"})
    data_demo.append({"TAG": "AR-COCC", "Nombre": "Área de Cocción", "Nivel": "L3-Area", "TAG_Padre": "PL-REND", "Area": "Cocción"})
    
    # Bucle para los 9 Digestores
    for i in range(1, 10):
        dig_num = f"{i:02d}"
        tag_dig = f"EQ-DIG-{dig_num}"
        
        # L4 - EQUIPO
        data_demo.append({"TAG": tag_dig, "Nombre": f"Digestor #{i}", "Nivel": "L4-Equipo", "TAG_Padre": "AR-COCC", "Area": "Cocción", "Especificaciones": "5 Ton/h"})
        
        # --- L5 - SISTEMAS DEL DIGESTOR ---
        tag_sis_mot = f"{tag_dig}-SIS-MOT"
        tag_sis_trm = f"{tag_dig}-SIS-TRM"
        
        data_demo.append({"TAG": tag_sis_mot, "Nombre": "Sistema Motriz", "Nivel": "L5-Sistema", "TAG_Padre": tag_dig, "Area": "Cocción", "Especificaciones": "Alimentación eléctrica"})
        data_demo.append({"TAG": tag_sis_trm, "Nombre": "Sistema de Transmisión", "Nivel": "L5-Sistema", "TAG_Padre": tag_dig, "Area": "Cocción", "Especificaciones": "Mecánico"})
        
        # --- L6 - COMPONENTES (HIJOS DE LOS SISTEMAS) ---
        # Componentes del Sistema Motriz
        data_demo.append({"TAG": f"{tag_dig}-MTR", "Nombre": "Motor Eléctrico 75HP", "Nivel": "L6-Componente", "TAG_Padre": tag_sis_mot, "Area": "Cocción", "Especificaciones": "440V, 1800RPM"})
        
        # Componentes del Sistema de Transmisión
        data_demo.append({"TAG": f"{tag_dig}-FAJ", "Nombre": "Juego de Fajas B86", "Nivel": "L6-Componente", "TAG_Padre": tag_sis_trm, "Area": "Cocción", "Especificaciones": "Perfil B, L=86"})
        data_demo.append({"TAG": f"{tag_dig}-POL", "Nombre": "Polea Motriz 4 Canales", "Nivel": "L6-Componente", "TAG_Padre": tag_sis_trm, "Area": "Cocción", "Especificaciones": "Hierro Fundido"})

    st.session_state.df_activos = pd.DataFrame(data_demo)

# Atajos
def get_db(): return st.session_state.df_activos
def save_db(df): st.session_state.df_activos = df

# ==========================================
# 2. LÓGICA DE FILTROS EN CASCADA (5 NIVELES)
# ==========================================
def filtro_cascada_5_niveles(key_suffix):
    """
    Genera selectores dependientes: Planta > Área > Equipo > Sistema
    Devuelve la selección de cada nivel.
    """
    df = get_db()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Planta
    plantas = df[df['Nivel'] == 'L2-Planta']['TAG'].unique()
    sel_planta = col1.selectbox("📍 Planta", plantas, key=f"p_{key_suffix}")
    
    # 2. Área
    areas = df[df['TAG_Padre'] == sel_planta]['TAG'].unique() if sel_planta else []
    sel_area = col2.selectbox("🏭 Área", areas, key=f"a_{key_suffix}")
    
    # 3. Equipo
    equipos = df[df['TAG_Padre'] == sel_area]['TAG'].unique() if sel_area else []
    sel_equipo = col3.selectbox("⚙️ Equipo", equipos, key=f"e_{key_suffix}")
    
    # 4. Sistema (NUEVO NIVEL)
    sistemas = df[df['TAG_Padre'] == sel_equipo]['TAG'].unique() if sel_equipo else []
    sel_sistema = col4.selectbox("🔄 Sistema", sistemas, key=f"s_{key_suffix}")
    
    return sel_planta, sel_area, sel_equipo, sel_sistema

# ==========================================
# 3. INTERFAZ PRINCIPAL
# ==========================================
st.title("🏭 Gestión Integral de Activos ISO-14224")
st.markdown("**Estructura:** Planta > Área > Equipo > Sistema > Componente")

tab_arbol, tab_nuevo, tab_datos = st.tabs(["🌳 Árbol Jerárquico", "➕ Agregar Activo", "📝 Editar Datos Manualmente"])

# --- TAB 1: VISUALIZADOR DE ÁRBOL ---
with tab_arbol:
    st.subheader("Explorador de Activos")
    st.info("Selecciona los filtros para navegar hasta el componente.")
    
    planta, area, equipo, sistema = filtro_cascada_5_niveles("nav")
    
    if sistema:
        st.divider()
        st.markdown(f"### 📂 {sistema} (Perteneciente a {equipo})")
        
        # Buscar componentes hijos de este sistema
        df = get_db()
        componentes = df[df['TAG_Padre'] == sistema]
        
        if not componentes.empty:
            st.markdown("#### 🔩 Componentes Instalados:")
            st.dataframe(componentes[['TAG', 'Nombre', 'Especificaciones', 'Estado']], use_container_width=True)
        else:
            st.warning("Este sistema no tiene componentes registrados aún.")

# --- TAB 2: AGREGAR NUEVO ACTIVO (CRUD) ---
with tab_nuevo:
    st.subheader("Alta de Nuevos Elementos")
    st.markdown("Usa los filtros para definir **DÓNDE** se instalará el nuevo activo.")
    
    # Reutilizamos la cascada para elegir el PADRE
    st.markdown("##### 1. Selecciona el Padre:")
    p, a, e, s = filtro_cascada_5_niveles("add")
    
    # Lógica para determinar quién es el padre y qué nivel toca
    padre_final = "ROOT"
    nivel_sugerido = "L2-Planta"
    
    if s:
        padre_final = s
        nivel_sugerido = "L6-Componente"
        st.success(f"Vas a crear un COMPONENTE dentro del sistema: **{s}**")
    elif e:
        padre_final = e
        nivel_sugerido = "L5-Sistema"
        st.success(f"Vas a crear un SISTEMA dentro del equipo: **{e}**")
    elif a:
        padre_final = a
        nivel_sugerido = "L4-Equipo"
        st.success(f"Vas a crear un EQUIPO dentro del área: **{a}**")
    elif p:
        padre_final = p
        nivel_sugerido = "L3-Area"
    
    st.markdown("##### 2. Detalles del Activo:")
    with st.form("frm_add"):
        c1, c2 = st.columns(2)
        nuevo_tag = c1.text_input("TAG Nuevo", value=f"{padre_final}-NUEVO")
        nuevo_nom = c2.text_input("Nombre", placeholder="Ej: Faja B86, Bomba Hidráulica...")
        nuevo_niv = c1.selectbox("Nivel", ["L3-Area", "L4-Equipo", "L5-Sistema", "L6-Componente"], index=["L3-Area", "L4-Equipo", "L5-Sistema", "L6-Componente"].index(nivel_sugerido) if nivel_sugerido != "L2-Planta" else 0)
        nueva_esp = c2.text_area("Especificaciones Técnicas")
        
        if st.form_submit_button("💾 Guardar en Base de Datos"):
            if nuevo_tag in get_db()['TAG'].values:
                st.error("Error: El TAG ya existe.")
            else:
                nuevo_reg = {
                    "TAG": nuevo_tag, "Nombre": nuevo_nom, "Nivel": nuevo_niv, 
                    "TAG_Padre": padre_final, "Area": "Manual", 
                    "Estado": "Operativo", "Especificaciones": nueva_esp
                }
                save_db(pd.concat([get_db(), pd.DataFrame([nuevo_reg])], ignore_index=True))
                st.toast("✅ Activo creado correctamente!")
                st.rerun()

# --- TAB 3: EDICIÓN MANUAL (EXCEL) ---
with tab_datos:
    st.subheader("Gestión Masiva de Datos")
    st.markdown("Aquí puedes editar nombres, especificaciones o corregir errores directamente.")
    
    df_editor = st.data_editor(get_db(), num_rows="dynamic", use_container_width=True, height=600)
    
    col_btn, col_info = st.columns([1, 4])
    if col_btn.button("💾 Guardar Cambios"):
        save_db(df_editor)
        st.success("Base de datos actualizada.")

# --- BARRA LATERAL: RESUMEN ---
st.sidebar.header("Resumen de Planta")
df_actual = get_db()
cant_equipos = len(df_actual[df_actual['Nivel'] == 'L4-Equipo'])
cant_sistemas = len(df_actual[df_actual['Nivel'] == 'L5-Sistema'])
cant_comp = len(df_actual[df_actual['Nivel'] == 'L6-Componente'])

st.sidebar.metric("Equipos (Digestores)", cant_equipos)
st.sidebar.metric("Sistemas", cant_sistemas)
st.sidebar.metric("Componentes", cant_comp)
st.sidebar.markdown("---")
st.sidebar.info("Modo: **Gestión Manual en Memoria**")
