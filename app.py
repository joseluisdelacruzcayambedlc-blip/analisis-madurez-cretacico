import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Análisis de Madurez Termal y Plays - Cretácico", layout="wide")

st.title("📊 Tablero Interactivo de la Madurez Térmica")
st.subheader("Análisis de la reflectancia de vitrinita %Rov de la Formación Napo (Cretácico)")

# Carga de datos
NOMBRE_ARCHIVO = "Datos_RoV_Pozos.xlsx"

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel(NOMBRE_ARCHIVO)
        df['Nombre del pozo'] = df['Nombre del pozo'].ffill()
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo '{NOMBRE_ARCHIVO}': {e}")
        return None

df = cargar_datos()

if df is not None:
    # Nombres exactos de las columnas según tu Excel
    col_prof = 'Profundidad (pies)'
    col_rov = 'Reflectancia de vitrinita (%Rov)'

    # Clasificación de Plays según profundidad y Madurez según RoV
    def clasificar_play(depth):
        if depth < 3000:
            return 'Play subandino-Bermejo'
        elif depth <= 10000:
            return 'Play oriental ITT'
        else:
            return 'Play central-Libertador'

    def clasificar_madurez(rov):
        if rov < 0.55:
            return 'Inmaduro'
        elif rov < 0.70:
            return 'Madurez Temprana'
        elif rov <= 1.0:
            return 'Maduro'
        else:
            return 'Sobremaduro'

    df['Play petrolero'] = df[col_prof].apply(clasificar_play)
    df['Madurez Térmica'] = df[col_rov].apply(clasificar_madurez)

    # Identificación flexible de la columna de unidad estratigráfica
    col_unidad = 'Unidad estratigráfica' if 'Unidad estratigráfica' in df.columns else 'Unidad Estratigráfica'

    # --- CONTROLES DE FILTRADO DINÁMICO ---
    st.markdown("### Controles de Filtrado Dinámico")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        plays_opciones = ["Todos los Plays"] + sorted(list(df['Play petrolero'].dropna().unique()))
        play_sel = st.selectbox("📌 Seleccionar Play Petrolero:", plays_opciones)

    with col2:
        madurez_opciones = ["Todas las Madureces"] + sorted(list(df['Madurez Térmica'].dropna().unique()))
        madurez_sel = st.selectbox("📌 Seleccionar Nivel de Madurez:", madurez_opciones)

    with col3:
        if col_unidad in df.columns:
            unidades_opciones = ["Todas las Unidades"] + sorted(list(df[col_unidad].dropna().unique()))
        else:
            unidades_opciones = ["Todas las Unidades"]
        unidad_sel = st.selectbox("🏛️ Seleccionar Unidad Estratigráfica:", unidades_opciones)

    # Filtrado dinámico acumulativo para la lista de pozos
    df_filtrado = df.copy()

    if play_sel != "Todos los Plays":
        df_filtrado = df_filtrado[df_filtrado['Play petrolero'] == play_sel]

    if madurez_sel != "Todas las Madureces":
        df_filtrado = df_filtrado[df_filtrado['Madurez Térmica'] == madurez_sel]

    if col_unidad in df_filtrado.columns and unidad_sel != "Todas las Unidades":
        df_filtrado = df_filtrado[df_filtrado[col_unidad] == unidad_sel]

    with col4:
        pozos_opciones = ["Todos los Pozos"] + sorted(list(df_filtrado['Nombre del pozo'].dropna().unique()))
        pozo_sel = st.selectbox("🛢️ Seleccionar Pozo Específico:", pozos_opciones)

    if pozo_sel != "Todos los Pozos":
        df_filtrado = df_filtrado[df_filtrado['Nombre del pozo'] == pozo_sel]

    st.markdown("---")

    # Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pozos Seleccionados", df_filtrado['Nombre del pozo'].nunique())
    m2.metric("Muestras Evaluadas", len(df_filtrado))
    m3.metric("Profundidad Promedio", f"{df_filtrado[col_prof].mean():.2f} ft" if not df_filtrado.empty else "N/A")
    m4.metric("%Ro Promedio", f"{df_filtrado[col_rov].mean():.2f}" if not df_filtrado.empty else "N/A")

    st.markdown("---")

    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron muestras para la combinación de filtros seleccionada.")
    else:
        tab1, tab2 = st.tabs(["📉 Perfil %Ro vs Profundidad", "📊 Distribución por Play y Madurez"])

        with tab1:
            hover_fields = [col_prof, col_rov, 'Play petrolero', 'Madurez Térmica']
            if col_unidad in df_filtrado.columns:
                hover_fields.append(col_unidad)

            fig_scatter = px.scatter(
                df_filtrado,
                x=col_prof,
                y=col_rov,
                color='Nombre del pozo',
                symbol='Madurez Térmica',
                hover_name='Nombre del pozo',
                hover_data=hover_fields,
                title="Perfil de Madurez Térmica (%Ro vs Profundidad)",
                labels={
                    col_prof: 'Depth [ft]',
                    col_rov: 'RoV [%]',
                    'Nombre del pozo': 'Pozo',
                    col_unidad: 'Unidad Estratigráfica'
                },
                height=650
            )

            # LÍNEAS DE MADUREZ TÉRMICA (HORIZONTALES)
            fig_scatter.add_hline(y=0.55, line_width=1.5, line_color="#1f77b4")
            fig_scatter.add_hline(y=0.70, line_width=1.5, line_color="#1f77b4")
            fig_scatter.add_hline(y=1.00, line_width=1.5, line_color="#1f77b4")

            # ETIQUETAS DE MADUREZ EN EL COSTADO DERECHO
            fig_scatter.add_annotation(x=1.02, xref="paper", y=0.275, yref="y", text="<b>Inmaduro</b>", showarrow=False, font=dict(size=12))
            fig_scatter.add_annotation(x=1.02, xref="paper", y=0.625, yref="y", text="<b>Madurez temprana</b>", showarrow=False, font=dict(size=12))
            fig_scatter.add_annotation(x=1.02, xref="paper", y=0.850, yref="y", text="<b>Maduro</b>", showarrow=False, font=dict(size=12))
            fig_scatter.add_annotation(x=1.02, xref="paper", y=1.250, yref="y", text="<b>Sobremaduro</b>", showarrow=False, font=dict(size=12))

            # LÍNEAS VERTICALES DE LÍMITE DE PLAYS (3000 y 10000 ft) Y ETIQUETAS
            fig_scatter.add_vline(x=3000, line_width=2, line_color="red")
            fig_scatter.add_vline(x=10000, line_width=2, line_color="red")

            fig_scatter.add_annotation(x=1500, y=1.55, text="<b>Play<br>Subandino-Bermejo</b>", showarrow=False, font=dict(size=13, color="black"), align="center")
            fig_scatter.add_annotation(x=6500, y=1.55, text="<b>Play<br>Oriental-ITT</b>", showarrow=False, font=dict(size=13, color="black"), align="center")
            fig_scatter.add_annotation(x=11500, y=1.55, text="<b>Play<br>Central-Libertador</b>", showarrow=False, font=dict(size=13, color="black"), align="center")

            fig_scatter.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray')
            fig_scatter.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', range=[0, 1.7])

            fig_scatter.update_layout(
                legend_title_text='Pozos',
                hovermode='closest',
                margin=dict(r=120, t=80)
            )

            st.plotly_chart(fig_scatter, use_container_width=True)

        with tab2:
            fig_bar = px.histogram(
                df_filtrado,
                x='Play petrolero',
                color='Madurez Térmica',
                barmode='group',
                title="Conteo de Muestras y Pozos por Play Petrolero",
                color_discrete_map={
                    'Inmaduro': '#2ca02c', 
                    'Madurez Temprana': '#ff7f0e', 
                    'Maduro': '#d62728',
                    'Sobremaduro': '#9467bd'
                },
                height=500
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # TABLA DINÁMICA DE DATOS FORMATEADA
        st.markdown("### 📋 Tabla Dinámica de Datos")
        
        df_tabla = df_filtrado.copy()
        df_tabla[col_prof] = df_tabla[col_prof].apply(lambda x: f"{x:.2f}")
        df_tabla[col_rov] = df_tabla[col_rov].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(df_tabla, use_container_width=True)
