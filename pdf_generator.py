from fpdf import FPDF
from io import BytesIO
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

def create_pdf(jug_sel, data_jug, df_filtrado, df_historico):
    # =========================================================
    # FIX SEGURO PARA STREAMLIT CLOUD Y LINUX
    # =========================================================
    try:
        # Inyectamos los permisos de seguridad de Linux directamente en Plotly
        current_args = list(pio.kaleido.scope.chromium_args)
        if "--no-sandbox" not in current_args:
            current_args.extend(["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process"])
            pio.kaleido.scope.chromium_args = tuple(current_args)
    except Exception:
        pass

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    
    def add_page_header(title):
        pdf.add_page()
        try:
            pdf.image("logo.jpeg", x=175, y=10, w=25)
        except:
            pass
        pdf.set_font("Arial", "B", 22)
        pdf.set_text_color(26, 91, 54) # Verde Institucional DyJ
        pdf.cell(0, 15, "Reporte Bio-Banding", ln=True, align="L")
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, title, ln=True, align="L")
        pdf.ln(5)

    # =========================================================
    # PÁGINA 1: PERFIL INDIVIDUAL
    # =========================================================
    add_page_header(f"Perfil Individual: {jug_sel}")
    
    url_foto = data_jug['URLFOTO'].values[0] if 'URLFOTO' in data_jug.columns and not data_jug.empty else None
    if pd.notna(url_foto):
        try:
            res = requests.get(url_foto, timeout=5)
            if res.status_code == 200:
                pdf.image(BytesIO(res.content), x=90, y=42, w=30) 
        except:
            pass

    pdf.set_y(80) 
    
    if not data_jug.empty:
        v_edad = f"{data_jug['Edad_Decimal'].values[0]:.2f}"
        v_edad_bio = f"{data_jug['Edad PHV'].values[0]:.2f}"
        v_etapa = "Normal" if data_jug['M.O'].values[0] >= 0 else "Tardía"
        v_alt = f"{data_jug['Altura de Pie '].values[0]:.1f}"
        v_peso = f"{data_jug['Peso'].values[0]:.2f}"
        grt = data_jug['Gr.T'].values[0]
        v_ritmo = f"{grt:.2f}" if pd.notna(grt) else "Sin datos"
        v_phv = data_jug['% PHV'].values[0] if pd.notna(data_jug['% PHV'].values[0]) else 0
        v_grt = grt if pd.notna(grt) else 0
    else:
        v_edad, v_edad_bio, v_etapa, v_alt, v_peso, v_ritmo, v_phv, v_grt = "--", "--", "--", "--", "--", "--", 0, 0

    def draw_kpi(x, y, label, value):
        pdf.set_xy(x, y)
        pdf.set_fill_color(248, 249, 250)
        pdf.set_draw_color(39, 174, 96) 
        pdf.cell(55, 18, "", border=1, fill=True)
        pdf.set_xy(x, y+2)
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0,0,0)
        pdf.cell(55, 8, str(value), align="C")
        pdf.set_xy(x, y+10)
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(55, 8, label, align="C")
        pdf.set_text_color(0, 0, 0)

    draw_kpi(15, 80, "EDAD", v_edad)
    draw_kpi(77.5, 80, "EDAD BIOLOGICA", v_edad_bio)
    draw_kpi(140, 80, "MADURACION", v_etapa)
    draw_kpi(15, 103, "ALTURA (CM)", v_alt)
    draw_kpi(77.5, 103, "PESO (KG)", v_peso)
    draw_kpi(140, 103, "RITMO (CM/AÑO)", v_ritmo)

    color_phv = "#E74C3C" if v_phv >= 92 else ("#E67E22" if v_phv >= 88 else "#2ECC71")
    fig_g = go.Figure()
    fig_g.add_trace(go.Indicator(mode="gauge+number", value=v_phv, domain={'x': [0, 0.45], 'y': [0, 1]}, title={'text': "% Madurez", 'font': {'size': 24}}, gauge={'axis': {'range': [80, 100]}, 'bar': {'color': color_phv}}))
    fig_g.add_trace(go.Indicator(mode="gauge+number", value=v_grt, domain={'x': [0.55, 1], 'y': [0, 1]}, title={'text': "Tasa Crecimiento", 'font': {'size': 24}}, gauge={'axis': {'range': [0, 15]}, 'bar': {'color': "black"}, 'steps': [{'range': [0, 5], 'color': "#2ECC71"}, {'range': [5, 10], 'color': "#F1C40F"}, {'range': [10, 15], 'color': "#E74C3C"}]}))
    fig_g.update_layout(width=1200, height=400, margin=dict(l=80, r=80, t=60, b=40))
    
    try:
        img_g_bytes = fig_g.to_image(format="png", engine="kaleido", scale=2)
        pdf.image(BytesIO(img_g_bytes), x=10, y=128, w=190)
    except:
        pdf.set_xy(10, 140)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(190, 10, "Generando grafico de medidores...", align="C")

    df_hist_plot = df_historico[df_historico['Nombre y Apellido'] == jug_sel]
    if not df_hist_plot.empty:
        fig_hist = px.scatter(df_hist_plot, x='Edad_Decimal', y='Altura de Pie ', title="Crecimiento vs Edad Decimal")
        fig_hist.update_traces(marker=dict(size=20, color='#1E3A8A'))
        fig_hist.update_layout(width=1200, height=500, title_x=0.5, plot_bgcolor='white', margin=dict(l=80, r=60, t=60, b=80), font=dict(size=18))
        fig_hist.update_xaxes(showgrid=True, gridcolor='#EFEFEF', title="Edad Decimal")
        fig_hist.update_yaxes(showgrid=True, gridcolor='#EFEFEF', title="Altura de Pie (cm)")
        
        try:
            img_hist_bytes = fig_hist.to_image(format="png", engine="kaleido", scale=2)
            pdf.image(BytesIO(img_hist_bytes), x=10, y=195, w=190)
        except:
            pass

    # =========================================================
    # PÁGINA 2: JUGADORES
    # =========================================================
    add_page_header("Resumen Global de Jugadores")
    
    pdf.set_y(32)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(26, 91, 54)
    pdf.cell(60, 6, "Cercanos a PHV", border=0, align="C")
    pdf.cell(5, 6, "", border=0)
    pdf.cell(60, 6, "Siguen Creciendo", border=0, align="C")
    pdf.cell(5, 6, "", border=0)
    pdf.cell(60, 6, "Más altas Crecimiento", border=0, ln=True, align="C")
    
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0,0,0)
    
    pdf.cell(45, 6, "Nombre", border=1, fill=True)
    pdf.cell(15, 6, "Dist. PHV", border=1, align="C", fill=True)
    pdf.cell(5, 6, "", border=0)
    pdf.cell(45, 6, "Nombre", border=1, fill=True)
    pdf.cell(15, 6, "% PHV", border=1, align="C", fill=True)
    pdf.cell(5, 6, "", border=0)
    pdf.cell(45, 6, "Nombre", border=1, fill=True)
    pdf.cell(15, 6, "Cm/Año", border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    df_t1 = df_filtrado.copy()
    df_t1['Abs_MO'] = df_t1['M.O'].abs()
    top_phv = df_t1.sort_values('Abs_MO').head(10)[['Nombre y Apellido', 'M.O']]
    top_siguen = df_filtrado[df_filtrado['M.O'] < 0].sort_values('% PHV').head(10)[['Nombre y Apellido', '% PHV']]
    top_crec = df_filtrado.sort_values('Gr.T', ascending=False).head(10)[['Nombre y Apellido', 'Gr.T']]
    
    for i in range(10):
        n1 = str(top_phv.iloc[i,0])[:22] if i < len(top_phv) else ""
        v1 = f"{top_phv.iloc[i,1]:.2f}" if i < len(top_phv) else ""
        n2 = str(top_siguen.iloc[i,0])[:22] if i < len(top_siguen) else ""
        v2 = f"{top_siguen.iloc[i,1]:.2f}" if i < len(top_siguen) else ""
        n3 = str(top_crec.iloc[i,0])[:22] if i < len(top_crec) else ""
        v3 = f"{top_crec.iloc[i,1]:.2f}" if i < len(top_crec) else ""
        
        pdf.cell(45, 6, n1, border=1)
        pdf.cell(15, 6, v1, border=1, align="C")
        pdf.cell(5, 6, "", border=0)
        pdf.cell(45, 6, n2, border=1)
        pdf.cell(15, 6, v2, border=1, align="C")
        pdf.cell(5, 6, "", border=0)
        pdf.cell(45, 6, n3, border=1)
        pdf.cell(15, 6, v3, border=1, align="C")
        pdf.ln()

    df_plot = df_filtrado.dropna(subset=['M.O'])
    if not df_plot.empty:
        fig_g1 = px.scatter(df_plot, x='M.O', y='Gr.T', title="Distribución Global (Maduración vs Crecimiento)")
        fig_g1.update_traces(marker=dict(size=18, color='#3498DB', line=dict(width=1, color='white')))
        fig_g1.add_hline(y=7, line_dash="dash", line_color="#E74C3C", line_width=2)
        fig_g1.add_vline(x=0, line_dash="dash", line_color="#E74C3C", line_width=2)
        fig_g1.update_layout(width=1200, height=600, title_x=0.5, plot_bgcolor='white', margin=dict(l=80, r=60, t=60, b=80), font=dict(size=18), xaxis_range=[-3, 3], yaxis_range=[0, 20])
        fig_g1.update_xaxes(showgrid=True, gridcolor='#EFEFEF', title="Distancia al inicio de maduración (M.O)")
        fig_g1.update_yaxes(showgrid=True, gridcolor='#EFEFEF', title="Crecimiento (cm/año)")
        
        try:
            img_g1_bytes = fig_g1.to_image(format="png", engine="kaleido", scale=2)
            pdf.image(BytesIO(img_g1_bytes), x=10, y=110, w=190)
        except:
            pass

    # =========================================================
    # PÁGINA 3: CONOCIMIENTO GLOBAL
    # =========================================================
    add_page_header("Conocimiento Global")
    
    df_bar = df_filtrado.dropna(subset=['% PHV']).sort_values('% PHV', ascending=False)
    if not df_bar.empty:
        fig_b = px.bar(df_bar, x='Nombre y Apellido', y='% PHV', title="Porcentaje de Altura Adulta Predicha")
        fig_b.update_traces(marker_color='#BDC3C7', texttemplate='%{y:.1f}%', textposition='outside')
        fig_b.add_hline(y=90, line_dash="dash", line_color="#E74C3C", line_width=2)
        fig_b.update_layout(width=1200, height=500, title_x=0.5, plot_bgcolor='white', yaxis_range=[60, 105], margin=dict(l=80, r=60, t=60, b=100), font=dict(size=18))
        
        try:
            img_b_bytes = fig_b.to_image(format="png", engine="kaleido", scale=2)
            pdf.image(BytesIO(img_b_bytes), x=10, y=35, w=190)
        except:
            pass

    if not df_plot.empty:
        fig_c = px.scatter(df_plot, x='M.O', y='Gr.T', title=f"Ubicación de {jug_sel} en el Plantel")
        fig_c.update_traces(marker=dict(size=16, color='#95A5A6', line=dict(width=1, color='white')))
        fig_c.add_hline(y=7, line_dash="dash", line_color="#E74C3C", line_width=2)
        fig_c.add_vline(x=0, line_dash="dash", line_color="#E74C3C", line_width=2)
        if not data_jug.empty:
            fig_c.add_scatter(x=data_jug['M.O'], y=data_jug['Gr.T'], mode='markers', marker=dict(size=28, color='#F1C40F', symbol='star', line=dict(width=2, color='black')), name=jug_sel)
        fig_c.update_layout(width=1200, height=600, title_x=0.5, plot_bgcolor='white', xaxis_range=[-3, 3], yaxis_range=[0, 20], margin=dict(l=80, r=60, t=60, b=80), font=dict(size=18))
        fig_c.update_xaxes(showgrid=True, gridcolor='#EFEFEF', title="Distancia al inicio de maduración (M.O)")
        fig_c.update_yaxes(showgrid=True, gridcolor='#EFEFEF', title="Crecimiento (cm/año)")
        
        try:
            img_c_bytes = fig_c.to_image(format="png", engine="kaleido", scale=2)
            pdf.image(BytesIO(img_c_bytes), x=10, y=140, w=190)
        except:
            pass

    return bytes(pdf.output())
