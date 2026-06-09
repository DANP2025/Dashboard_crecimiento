import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
from data_processor import load_data_v5, get_image_bytes
from pdf_generator import create_pdf

# Configuración inicial
st.set_page_config(page_title="Bio-Banding Institucional", page_icon="⚽", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PREMIUM Y FUENTES AGENCY FB ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    
    @import url('https://fonts.cdnfonts.com/css/agency-fb');
    html, body, [class*="css"], p, span, div, label, h1, h2, h3, h4, h5, h6, button, th, td { 
        font-family: 'Agency FB', 'Segoe UI', Roboto, Helvetica, sans-serif !important; 
    }
    
    html, body, [class*="css"] { font-size: 20px !important; }
    
    .stSelectbox label { font-size: 1.5rem !important; font-weight: 800 !important; color: #1A5B36 !important; letter-spacing: 1px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 3px solid #27AE60; padding-top: 15px; }
    .stTabs [data-baseweb="tab"] {
        height: 60px; background-color: #f8f9fa; border-radius: 12px 12px 0px 0px;
        padding: 10px 35px; color: #555; font-size: 26px !important; font-weight: 700;
        border: 2px solid #e0e0e0; border-bottom: none; transition: all 0.3s ease; letter-spacing: 1px;
    }
    .stTabs [data-baseweb="tab"]:hover { background-color: #F4D03F; color: #1A5B36; }
    .stTabs [aria-selected="true"] { background-color: #27AE60 !important; color: white !important; border-color: #27AE60 !important; }
    
    .kpi-card {
        background-color: #ffffff; border-radius: 15px; padding: 20px 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08); border-left: 8px solid #27AE60;
        transition: transform 0.3s ease, box-shadow 0.3s ease; margin-bottom: 20px; 
        border-right: 1px solid #f0f0f0; border-top: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0;
    }
    .kpi-card:hover { transform: translateY(-8px); box-shadow: 0 12px 30px rgba(39, 174, 96, 0.2); }
    .kpi-val { font-size: 3.5rem !important; font-weight: 900; color: #1A5B36; margin: 0; line-height: 1; }
    .kpi-label { font-size: 1.4rem !important; color: #7f8c8d; margin: 0; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-top: 8px; }
    
    .sticky-player {
        position: fixed; top: 15px; right: 25px; background-color: rgba(255, 255, 255, 0.95);
        padding: 6px 20px 6px 6px; border-radius: 60px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        z-index: 999999; display: flex; align-items: center; gap: 12px;
        border: 3px solid #27AE60; backdrop-filter: blur(8px);
    }
    .sticky-player img { border-radius: 50%; width: 45px; height: 45px; object-fit: cover; border: 2px solid #F4D03F; }
    .sticky-player-name { font-size: 22px; font-weight: 900; color: #1A5B36; text-transform: uppercase; white-space: nowrap; letter-spacing: 1px;}
    </style>
""", unsafe_allow_html=True)

def get_base64_image(img_bytes):
    if img_bytes: return base64.b64encode(img_bytes.getvalue()).decode()
    return ""

col_empty, col_title, col_logo = st.columns([1, 8, 1])
with col_title:
    st.markdown("""
        <div style='margin-bottom: 15px; text-align: center;'>
            <h1 style='color: #1A5B36; font-weight: 900; margin: 0; font-size: 3.5rem; line-height: 1.1; letter-spacing: 1px;'>BIO-BANDING INSTITUCIONAL:</h1>
            <h2 style='color: #27AE60; font-weight: 800; margin: 0; font-size: 2.2rem; line-height: 1.2; letter-spacing: 0.5px;'>ENTRENAMIENTO DEL FUTBOLISTA POR MADURACIÓN BIOLÓGICA</h2>
            <h3 style='color: #555555; font-weight: 700; margin: 0; font-size: 1.6rem; line-height: 1.2; letter-spacing: 0.5px;'>MATRIZ METODOLÓGICA INTEGRADA: MODELO - FUTBOLISTAS ATLETAS</h3>
        </div>
    """, unsafe_allow_html=True)
with col_logo:
    try: st.image('logo.jpeg', width=130)
    except: pass

df_historico, df_latest = load_data_v5()

if not df_latest.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])
    with col_f1: fecha_sel = st.selectbox("FECHA DE EVALUACIÓN", ["Todos"] + sorted(df_latest['Mes_Año_Eval'].dropna().unique()))
    with col_f2: pos_sel = st.selectbox("POSICIÓN", ["Todos"] + sorted(df_latest['Posicion'].dropna().unique()))
    with col_f3: cat_sel = st.selectbox("CATEGORÍA", ["Todos"] + sorted(df_latest['Categoria'].dropna().unique()))
    with col_f4: jug_sel = st.selectbox("JUGADOR", ["Todos"] + sorted(df_latest['Nombre y Apellido'].dropna().unique()))

    df_filtrado = df_latest.copy()
    if fecha_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes_Año_Eval'] == fecha_sel]
    if pos_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Posicion'] == pos_sel]
    if cat_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Categoria'] == cat_sel]
    if jug_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Nombre y Apellido'] == jug_sel]

    data_jug = pd.DataFrame()

    if jug_sel != "Todos":
        data_jug = df_filtrado[df_filtrado['Nombre y Apellido'] == jug_sel]
        if not data_jug.empty:
            img_bytes = None
            if 'URLFOTO' in data_jug.columns and pd.notna(data_jug['URLFOTO'].values[0]):
                img_bytes = get_image_bytes(data_jug['URLFOTO'].values[0])
            
            if img_bytes:
                b64_img = get_base64_image(img_bytes)
                st.markdown(f"""
                <div class="sticky-player">
                    <img src="data:image/jpeg;base64,{b64_img}">
                    <span class="sticky-player-name">{jug_sel}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="sticky-player" style="padding-left: 20px;">
                    <span class="sticky-player-name">👤 {jug_sel}</span>
                </div>
                """, unsafe_allow_html=True)

            if 'current_jug' not in st.session_state or st.session_state['current_jug'] != jug_sel:
                st.session_state['current_jug'] = jug_sel
                st.session_state['pdf_ready'] = False
                st.session_state['pdf_bytes'] = None

            c1, c2, c3 = st.columns([1.5, 2, 1.5])
            with c2:
                if img_bytes:
                    b64_img_main = get_base64_image(img_bytes)
                    st.markdown(f"""
                    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                        <img src="data:image/jpeg;base64,{b64_img_main}" style="width: 170px; height: 170px; object-fit: cover; border-radius: 15px; border: 3px solid #27AE60; box-shadow: 0 6px 15px rgba(0,0,0,0.15);">
                    </div>
                    """, unsafe_allow_html=True)
                
                if not st.session_state['pdf_ready']:
                    if st.button("⚙️ Generar reporte", use_container_width=True):
                        with st.spinner("Generando reporte..."):
                            st.session_state['pdf_bytes'] = create_pdf(jug_sel, data_jug, df_filtrado, df_historico)
                            st.session_state['pdf_ready'] = True
                            st.rerun()
                else:
                    st.download_button("📥 Descargar reporte", data=st.session_state['pdf_bytes'], file_name=f"Reporte_{jug_sel}.pdf", mime='application/pdf', use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_dep, tab_perf, tab_con = st.tabs(["👥 Jugadores", "👤 Perfil Individual", "🌍 Conocimiento Global"])

    plotly_font_config = dict(size=20, color="#333", family="Agency FB, Segoe UI, Arial")
    plotly_hover_config = dict(font_size=22, font_family="Agency FB, Segoe UI, Arial")

    # FIX DE ESTRATEGIA LAYOUT: Configura el font-size de la tabla dinámicamente y fuerza el salto de línea (white-space: normal)
    def style_dataframe(df_styled, font_size="16px"):
        df_styled = df_styled.set_properties(**{'font-size': font_size, 'padding': '6px 8px', 'font-family': 'Agency FB'})
        df_styled = df_styled.set_table_styles([
            {'selector': 'th', 'props': [('font-size', font_size), ('font-family', 'Agency FB'), ('white-space', 'normal'), ('text-align', 'center')]}
        ])
        return df_styled

    # ==========================================
    # TAB 1: JUGADORES
    # ==========================================
    with tab_dep:
        st.markdown("<br>", unsafe_allow_html=True)
        # FIX: Le damos una proporción mayor a la tabla (1.6) para que quepan las columnas largas
        col_tabla, col_grafico = st.columns([1.6, 1])
        with col_tabla:
            st.markdown("<h3 style='text-align: center; color: #1A5B36; font-weight: 800; font-size: 2.2rem;'>INDICADORES CLAVES DE RENDIMIENTO</h3>", unsafe_allow_html=True)
            # Revertimos a los nombres completos y originales. Eliminamos na_rep="" para que salga "None" nativo
            df_display = df_filtrado.rename(columns={'Edad_Decimal': 'Edad', 'Altura de Pie ': 'Altura Actual cm', 'Altura_Adulta_Predicha': 'Altura Adulta Predicha cm'})
            cols_table = ['Nombre y Apellido', 'Edad', 'Edad Biológica', 'Altura Actual cm', 'Altura Adulta Predicha cm', 'Gr.T', 'M.O']
            styled_df = df_display[cols_table].style.format({'Edad': '{:.2f}', 'Edad Biológica': '{:.2f}', 'Altura Actual cm': '{:.2f}', 'Altura Adulta Predicha cm': '{:.2f}', 'Gr.T': '{:.2f}', 'M.O': '{:.2f}'})
            st.dataframe(style_dataframe(styled_df, font_size="16px"), hide_index=True, use_container_width=True, height=500)

        with col_grafico:
            st.markdown("<h3 style='text-align: center; color: #1A5B36; font-weight: 800; font-size: 2.2rem;'>Porcentaje de Altura Adulta Predicha</h3>", unsafe_allow_html=True)
            df_bar = df_filtrado.dropna(subset=['% PHV']).sort_values('% PHV', ascending=False)
            if not df_bar.empty:
                fig_bar = px.bar(df_bar, x='Nombre y Apellido', y='% PHV', text='% PHV')
                fig_bar.update_traces(marker_color='#BDC3C7', texttemplate='%{text:.1f}%', textposition='outside', textfont_size=20)
                fig_bar.add_hline(y=90, line_dash="dash", line_color="#E74C3C", line_width=3)
                fig_bar.update_layout(yaxis_range=[60, 105], plot_bgcolor='white', margin=dict(t=20, b=20), xaxis_title="", font=plotly_font_config, hoverlabel=plotly_hover_config)
                st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #1A5B36; font-weight: 800; font-size: 2.2rem;'>Dónde están los jugadores de acuerdo a su desarrollo</h3>", unsafe_allow_html=True)
        df_plot = df_filtrado.dropna(subset=['M.O']) 
        if not df_plot.empty:
            fig = px.scatter(df_plot, x='M.O', y='Gr.T', hover_name='Nombre y Apellido', hover_data={'Iniciales': True, 'M.O': ':.2f', 'Gr.T': ':.2f', 'Decision_Entrenamiento': True}, labels={'M.O': 'Distancia al inicio de maduración', 'Gr.T': 'Crecimiento (cm/año)'})
            fig.update_traces(marker=dict(size=18, color='#3498DB', line=dict(width=2, color='white')))
            fig.add_hline(y=7, line_dash="dash", line_color="#E74C3C", line_width=2)
            fig.add_vline(x=0, line_dash="dash", line_color="#E74C3C", line_width=2)
            fig.update_layout(xaxis_range=[-3, 3], yaxis_range=[0, 20], plot_bgcolor='white', height=600, margin=dict(t=30, b=30), font=plotly_font_config, hoverlabel=plotly_hover_config)
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#EFEFEF', zeroline=False, title_font=dict(size=22, weight='bold'))
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#EFEFEF', zeroline=False, title_font=dict(size=22, weight='bold'))
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # TAB 2: PERFIL INDIVIDUAL
    # ==========================================
    with tab_perf:
        st.markdown("<br>", unsafe_allow_html=True)
        if not data_jug.empty:
            v_edad = f"{data_jug['Edad_Decimal'].values[0]:.2f}"
            v_edad_bio = f"{data_jug['Edad Biológica'].values[0]:.2f}"
            v_etapa = "Normal" if data_jug['M.O'].values[0] >= 0 else "Tardía"
            v_alt = f"{data_jug['Altura de Pie '].values[0]:.1f}"
            v_peso = f"{data_jug['Peso'].values[0]:.2f}"
            grt = data_jug['Gr.T'].values[0]
            v_ritmo = "Sin datos" if pd.isna(grt) else f"{grt:.2f}"
            v_phv = data_jug['% PHV'].values[0] if not pd.isna(data_jug['% PHV'].values[0]) else 0
            v_grt = grt if not pd.isna(grt) else 0
        else:
            v_edad, v_edad_bio, v_etapa, v_alt, v_peso, v_ritmo = "--", "(Blank)", "(Blank)", "(Blank)", "(Blank)", "(Blank)"
            v_phv, v_grt = 0, 0
            grt = np.nan 

        color_phv_gauge = "#27AE60"
        if jug_sel != "Todos":
            if v_phv < 85: color_phv_gauge = "#2ECC71"
            elif v_phv < 88: color_phv_gauge = "#F1C40F"
            elif v_phv <= 92: color_phv_gauge = "#E67E22" 
            elif v_phv <= 97: color_phv_gauge = "#E74C3C" 
            else: color_phv_gauge = "#2ECC71"
        else: color_phv_gauge = "#EBEBEB"

        col_left, col_right = st.columns([1.5, 1.2])
        
        with col_left:
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='kpi-card'><p class='kpi-val'>{v_edad}</p><p class='kpi-label'>Edad</p></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='kpi-card'><p class='kpi-val'>{v_edad_bio}</p><p class='kpi-label'>Edad Biológica</p></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='kpi-card'><p class='kpi-val'>{v_etapa}</p><p class='kpi-label'>Etapa de maduración</p></div>", unsafe_allow_html=True)
            
            c4, c5, c6 = st.columns(3)
            c4.markdown(f"<div class='kpi-card'><p class='kpi-val'>{v_alt}</p><p class='kpi-label'>Altura en cm</p></div>", unsafe_allow_html=True)
            c5.markdown(f"<div class='kpi-card'><p class='kpi-val'>{v_peso}</p><p class='kpi-label'>Peso kg</p></div>", unsafe_allow_html=True)
            c6.markdown(f"<div class='kpi-card'><p class='kpi-val'>{v_ritmo}</p><p class='kpi-label'>Ritmo de Crecimiento</p></div>", unsafe_allow_html=True)

        with col_right:
            g1, g2 = st.columns(2)
            font_color_1 = "white" if jug_sel == "Todos" else "#1A5B36"
            font_color_2 = "white" if (jug_sel == "Todos" or pd.isna(grt)) else "#1A5B36"

            with g1:
                fig1 = go.Figure(go.Indicator(
                    mode="gauge+number", value=v_phv, 
                    number={'font': {'size': 60, 'color': font_color_1, 'family': 'Agency FB'}, 'valueformat': '.1f'}, 
                    domain={'x': [0, 1], 'y': [0, 1]}, 
                    title={'text': "Porcentaje de Madurez %", 'font': {'size': 24, 'color': '#7f8c8d', 'weight': 'bold', 'family': 'Agency FB'}}, 
                    gauge={'axis': {'range': [80, 100], 'tickwidth': 2, 'tickfont': {'size': 18, 'family': 'Agency FB'}}, 'bar': {'color': color_phv_gauge, 'thickness': 0.35}}
                ))
                fig1.update_layout(height=300, margin=dict(l=40, r=40, t=60, b=20), font=plotly_font_config)
                st.plotly_chart(fig1, use_container_width=True)
                
            with g2:
                color_aguja = "rgba(0,0,0,0)" if pd.isna(grt) or jug_sel == "Todos" else "#1A5B36"
                fig2 = go.Figure(go.Indicator(
                    mode="gauge+number", value=v_grt, 
                    number={'font': {'size': 60, 'color': font_color_2, 'family': 'Agency FB'}, 'valueformat': '.2f'}, 
                    domain={'x': [0, 1], 'y': [0, 1]}, 
                    title={'text': "Tasa de crecimiento (cm/año)", 'font': {'size': 24, 'color': '#7f8c8d', 'weight': 'bold', 'family': 'Agency FB'}}, 
                    gauge={'axis': {'range': [0, 15], 'tickwidth': 2, 'tickfont': {'size': 18, 'family': 'Agency FB'}}, 'bar': {'color': color_aguja, 'thickness': 0.35}, 'steps': [{'range': [0, 5], 'color': "#2ECC71"}, {'range': [5, 10], 'color': "#F1C40F"}, {'range': [10, 15], 'color': "#E74C3C"}]}))
                fig2.update_layout(height=300, margin=dict(l=40, r=40, t=60, b=20), font=plotly_font_config)
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<h3 style='text-align: center; color: #1A5B36; margin-top: 30px; font-weight: 800; font-size: 2.2rem;'>Crecimiento de acuerdo a la edad decimal</h3>", unsafe_allow_html=True)
        df_hist_plot = df_historico.dropna(subset=['Edad_Decimal', 'Altura de Pie ']).copy()
        if jug_sel != "Todos": df_hist_plot = df_hist_plot[df_hist_plot['Nombre y Apellido'] == jug_sel]

        df_hist_plot['Etapa'] = np.where(df_hist_plot['M.O'] >= 0, 'Normal', 'Tardía')
        fig3 = px.scatter(df_hist_plot, x='Edad_Decimal', y='Altura de Pie ', color='Etapa', color_discrete_map={'Normal': '#1E3A8A', 'Tardía': '#60A5FA'}, hover_name='Nombre y Apellido', labels={'Edad_Decimal': 'Edad Decimal (Años)', 'Altura de Pie ': 'Altura (cm)'})
        fig3.update_traces(marker=dict(size=18, line=dict(width=2, color='white')))
        fig3.update_layout(plot_bgcolor='white', height=500, margin=dict(t=30, b=30), legend_title_text='Etapa de maduración', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=22)), font=plotly_font_config, hoverlabel=plotly_hover_config)
        fig3.update_xaxes(showgrid=True, gridcolor='#EFEFEF', title_font=dict(size=22, weight='bold'))
        fig3.update_yaxes(showgrid=True, gridcolor='#EFEFEF', title_font=dict(size=22, weight='bold'))
        st.plotly_chart(fig3, use_container_width=True)

    # ==========================================
    # TAB 3: CONOCIMIENTO GLOBAL
    # ==========================================
    with tab_con:
        st.markdown("<br>", unsafe_allow_html=True)
        def color_mo(val):
            if pd.isna(val): return ''
            if val < -2: return 'background-color: #2ECC71; color: black; font-weight:bold;'
            if val < -1: return 'background-color: #F1C40F; color: black; font-weight:bold;'
            if val < 1: return 'background-color: #E74C3C; color: white; font-weight:bold;'
            if val < 2: return 'background-color: #E67E22; color: white; font-weight:bold;'
            return 'background-color: #2ECC71; color: black; font-weight:bold;'
        def color_gt(val):
            if pd.isna(val): return ''
            if val < 3: return 'background-color: #2ECC71; color: black; font-weight:bold;'
            if val < 5: return 'background-color: #F1C40F; color: black; font-weight:bold;'
            if val < 7: return 'background-color: #E67E22; color: white; font-weight:bold;'
            if val < 9: return 'background-color: #E74C3C; color: white; font-weight:bold;'
            return 'background-color: #8E0000; color: white; font-weight:bold;'
        def color_phv(val):
            if pd.isna(val): return ''
            if val < 85: return 'background-color: #2ECC71; color: black; font-weight:bold;'
            if val < 88: return 'background-color: #F1C40F; color: black; font-weight:bold;'
            if val <= 92: return 'background-color: #E74C3C; color: white; font-weight:bold;'
            if val <= 97: return 'background-color: #E67E22; color: white; font-weight:bold;'
            return 'background-color: #2ECC71; color: black; font-weight:bold;'

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<p style='text-align: center; font-weight: 800; font-size: 1.8rem; color: #1A5B36; font-family: \"Agency FB\";'>Jugadores cercanos a la altura PHV</p>", unsafe_allow_html=True)
            # Revertimos a nombres de columnas originales y mantenemos los Nulls nativos
            df_t1 = df_filtrado[['Nombre y Apellido', 'Edad_Decimal', 'Edad Biológica', 'M.O']].copy()
            df_t1['Abs_MO'] = df_t1['M.O'].abs()
            df_t1_disp = df_t1.sort_values('Abs_MO').head(10).drop(columns=['Abs_MO']).rename(columns={'Edad_Decimal': 'Edad'})
            styled_t1 = df_t1_disp.style.map(color_mo, subset=['M.O']).format({'Edad': '{:.2f}', 'Edad Biológica': '{:.2f}', 'M.O': '{:.2f}'})
            st.dataframe(style_dataframe(styled_t1, font_size="14px"), hide_index=True, use_container_width=True)
            
        with col2:
            st.markdown("<p style='text-align: center; font-weight: 800; font-size: 1.8rem; color: #1A5B36; font-family: \"Agency FB\";'>Jugadores que todavia siguen creciendo</p>", unsafe_allow_html=True)
            # Revertimos, incluimos todas las columnas como pediste
            df_t2 = df_filtrado[df_filtrado['M.O'] < 0][['Nombre y Apellido', 'Edad_Decimal', 'Edad Biológica', '% PHV', 'M.O', 'Gr.T']].copy()
            df_t2_disp = df_t2.sort_values('% PHV').head(10).rename(columns={'Edad_Decimal': 'Edad'})
            styled_t2 = df_t2_disp.style.map(color_phv, subset=['% PHV']).format({'Edad': '{:.2f}', 'Edad Biológica': '{:.2f}', '% PHV': '{:.2f}', 'M.O': '{:.2f}', 'Gr.T': '{:.2f}'})
            st.dataframe(style_dataframe(styled_t2, font_size="14px"), hide_index=True, use_container_width=True)
            
        with col3:
            st.markdown("<p style='text-align: center; font-weight: 800; font-size: 1.8rem; color: #1A5B36; font-family: \"Agency FB\";'>Mas altas de Crecimiento</p>", unsafe_allow_html=True)
            df_t3 = df_filtrado[['Nombre y Apellido', 'Edad_Decimal', 'M.O', 'Gr.T']].copy()
            df_t3_disp = df_t3.sort_values('Gr.T', ascending=False).head(10).rename(columns={'Edad_Decimal': 'Edad'})
            styled_t3 = df_t3_disp.style.map(color_gt, subset=['Gr.T']).format({'Edad': '{:.2f}', 'M.O': '{:.2f}', 'Gr.T': '{:.2f}'})
            st.dataframe(style_dataframe(styled_t3, font_size="14px"), hide_index=True, use_container_width=True)

        st.markdown("<h3 style='text-align: center; color: #1A5B36; margin-top: 40px; font-weight: 800; font-size: 2.2rem;'>Análisis Global de Desarrollo</h3>", unsafe_allow_html=True)
        df_plot2 = df_filtrado.dropna(subset=['M.O'])
        if not df_plot2.empty:
            fig_c = px.scatter(df_plot2, x='M.O', y='Gr.T', hover_name='Nombre y Apellido', hover_data={'Iniciales': True, 'M.O': ':.2f', 'Gr.T': ':.2f', 'Decision_Entrenamiento': True}, labels={'M.O': 'Distancia al inicio de maduración', 'Gr.T': 'Crecimiento (cm/año)'})
            fig_c.update_traces(marker=dict(size=16, color='#95A5A6', line=dict(width=1, color='white')))
            fig_c.add_hline(y=7, line_dash="dash", line_color="#E74C3C", line_width=2)
            fig_c.add_vline(x=0, line_dash="dash", line_color="#E74C3C", line_width=2)
            if jug_sel != "Todos" and not data_jug.empty: fig_c.add_scatter(x=data_jug['M.O'], y=data_jug['Gr.T'], mode='markers', marker=dict(size=25, color='#F1C40F', symbol='star', line=dict(width=2, color='black')), name=jug_sel)
            fig_c.update_layout(xaxis_range=[-3, 3], yaxis_range=[0, 20], plot_bgcolor='white', height=550, font=plotly_font_config, hoverlabel=plotly_hover_config)
            fig_c.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#EFEFEF', zeroline=False, title_font=dict(size=20, weight='bold'))
            fig_c.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#EFEFEF', zeroline=False, title_font=dict(size=20, weight='bold'))
            st.plotly_chart(fig_c, use_container_width=True)
