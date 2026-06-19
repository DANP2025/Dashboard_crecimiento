import pandas as pd
import numpy as np
import streamlit as st
import re
import requests
from io import BytesIO

st.cache_data.clear()

@st.cache_data(ttl=3600)
def get_image_bytes(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None
    except:
        return None

# FIX V16: Corrección de Ecuación de Mirwald (Age at PHV = Chronological Age - M.O)
@st.cache_data(ttl=60)
def load_data_v16():
    SHEET_ID = "1FVuYJtctdiwUzsptZOGOZcr7vXe1CMqR4f360kulYME"
    GID_DATOS = "1766718688"
    
    url_datos = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_DATOS}"
    url_interceptos = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Interceptos"
    
    try:
        df = pd.read_csv(url_datos)
        
        # =========================================================
        # FIX DE DEPURACIÓN: Eliminar filas fantasmas (Ghost rows) 
        # =========================================================
        df = df.dropna(subset=['Nombre y Apellido', 'Fecha de Evaluacion'], how='all')
        
        try:
            df_int = pd.read_csv(url_interceptos)
            cols = df_int.columns.astype(str).str.lower()
            
            col_edad = df_int.columns[cols.str.contains('edad')][0] if any(cols.str.contains('edad')) else df_int.columns[0]
            col_b0 = df_int.columns[cols.str.contains('0') | cols.str.contains('intercept')][0] if any(cols.str.contains('0') | cols.str.contains('intercept')) else df_int.columns[1]
            col_b1 = df_int.columns[cols.str.contains('1') | cols.str.contains('estatura') | cols.str.contains('talla')][0] if any(cols.str.contains('1') | cols.str.contains('estatura') | cols.str.contains('talla')) else df_int.columns[2]
            col_b2 = df_int.columns[cols.str.contains('2') | cols.str.contains('peso')][0] if any(cols.str.contains('2') | cols.str.contains('peso')) else df_int.columns[3]
            col_b3 = df_int.columns[cols.str.contains('3') | cols.str.contains('padres') | cols.str.contains('media')][0] if any(cols.str.contains('3') | cols.str.contains('padres') | cols.str.contains('media')) else df_int.columns[4]
            
            df_int = df_int[[col_edad, col_b0, col_b1, col_b2, col_b3]].copy()
            df_int.columns = ['Edad_Anios', 'B0', 'B1', 'B2', 'B3']
            
            for c in df_int.columns:
                if df_int[c].dtype == object:
                    df_int[c] = df_int[c].astype(str).str.replace(',', '.')
                df_int[c] = pd.to_numeric(df_int[c], errors='coerce')
        except Exception as e:
            df_int = pd.DataFrame({'Edad_Anios': np.arange(10, 18, 0.5), 'B0': [-12]*16, 'B1': [0.8]*16, 'B2': [0.3]*16, 'B3': [0.4]*16})

        cols_limpiar = ['Altura de Pie ', 'Altura sentado', 'Peso', 'Altura del padre', 'Altura de la madre']
        for col in cols_limpiar:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['Fecha de Nacimiento'] = pd.to_datetime(df['Fecha de Nacimiento'], format='mixed', dayfirst=True, errors='coerce')
        df['Fecha de Evaluacion'] = pd.to_datetime(df['Fecha de Evaluacion'], format='mixed', dayfirst=True, errors='coerce')
        
        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        
        df['Mes_Año_Eval'] = df['Fecha de Evaluacion'].apply(
            lambda x: f"{meses_es[x.month]} {x.year}" if pd.notna(x) else np.nan
        )

        df['Edad_Decimal'] = (df['Fecha de Evaluacion'] - df['Fecha de Nacimiento']).dt.days / 365.25
        df = df.sort_values(by=['DNI', 'Fecha de Evaluacion'])
        
        if 'URLFOTO' in df.columns:
            df['URLFOTO'] = df['URLFOTO'].replace(r'^\s*$', np.nan, regex=True)
            df['URLFOTO'] = df.groupby('DNI')['URLFOTO'].ffill().bfill()

        def normalize_photo_url(url):
            if pd.isna(url) or "ahi esta" in str(url): return np.nan
            url_str = str(url).strip()
            match1 = re.search(r'/d/([a-zA-Z0-9_-]+)', url_str)
            match3 = re.search(r'id=([a-zA-Z0-9_-]+)', url_str)
            if match1: return f"https://drive.google.com/uc?export=download&id={match1.group(1)}"
            elif match3: return f"https://drive.google.com/uc?export=download&id={match3.group(1)}"
            return url_str

        if 'URLFOTO' in df.columns:
            df['URLFOTO'] = df['URLFOTO'].apply(normalize_photo_url)

        df['Delta_Altura_cm'] = df.groupby('DNI')['Altura de Pie '].diff()
        df['Delta_Edad_años'] = df.groupby('DNI')['Edad_Decimal'].diff()
        df['Gr.T'] = np.where(df['Delta_Edad_años'] > 0, df['Delta_Altura_cm'] / df['Delta_Edad_años'], np.nan)

        df['Leg'] = df['Altura de Pie '] - df['Altura sentado']
        df['Pxt'] = np.where(df['Altura de Pie '] > 0, (df['Peso'] / df['Altura de Pie ']) * 100, np.nan)
        
        mirwald = -9.236 + 0.0002708 * df['Leg'] * df['Altura sentado'] - 0.001663 * df['Edad_Decimal'] * df['Leg'] + 0.007216 * df['Edad_Decimal'] * df['Altura sentado'] + 0.02292 * df['Pxt']
        
        df['AltPadre_cm'] = pd.to_numeric(df.get('Altura del padre', np.nan), errors='coerce').replace(0, np.nan)
        df['AltMadre_cm'] = pd.to_numeric(df.get('Altura de la madre', np.nan), errors='coerce').replace(0, np.nan)
        df['AltPadre_cm'] = np.where((df['AltPadre_cm'] > 0) & (df['AltPadre_cm'] < 3), df['AltPadre_cm'] * 100, df['AltPadre_cm'])
        df['AltMadre_cm'] = np.where((df['AltMadre_cm'] > 0) & (df['AltMadre_cm'] < 3), df['AltMadre_cm'] * 100, df['AltMadre_cm'])
        df['Predictor_Genetico'] = ((df['AltPadre_cm'] + df['AltMadre_cm']) / 2).fillna(174.0)
        
        has_parents = df['AltPadre_cm'].notna() & df['AltMadre_cm'].notna()
        moore2 = -7.999994 + 0.0036124 * (df['Edad_Decimal'] * df['Altura de Pie '])
        moore_padres = -7.999994 + 0.0036124 * (df['Edad_Decimal'] * df['Predictor_Genetico'])
        
        valid_mirwald = mirwald.between(-3.5, 2.5)
        df['M.O'] = np.where(valid_mirwald, mirwald, np.where(has_parents, moore_padres, moore2))
        
        # =========================================================
        # FIX CIENTÍFICO: Edad al PHV = Edad Cronológica - Maturity Offset
        # =========================================================
        df['Edad PHV'] = df['Edad_Decimal'] - df['M.O']

        df['EdadParaTabla'] = np.floor(df['Edad_Decimal'] * 2 + 0.5) / 2
        df = pd.merge(df, df_int, left_on='EdadParaTabla', right_on='Edad_Anios', how='left')
        
        df['Altura_Adulta_Predicha'] = df['B0'] + (df['B1'] * df['Altura de Pie ']) + (df['B2'] * df['Peso']) + (df['B3'] * df['Predictor_Genetico'])
        df['% PHV'] = (df['Altura de Pie '] / df['Altura_Adulta_Predicha']) * 100

        def categorizar(row):
            if pd.isna(row['M.O']) or pd.isna(row['Gr.T']): return "Sin datos de velocidad"
            if row['M.O'] < 0 and row['Gr.T'] < 7: return "Entrenamiento normal. Enfocar en técnica y coordinación."
            if row['M.O'] < 0 and row['Gr.T'] >= 7: return "Reducir volumen. Evitar picos de impacto."
            if row['M.O'] >= 0 and row['Gr.T'] < 7: return "Progresión gradual de fuerza y potencia."
            return "Limitar impacto. Priorizar prevención."

        df['Decision_Entrenamiento'] = df.apply(categorizar, axis=1)
        df['Iniciales'] = df['Nombre y Apellido'].apply(lambda x: "".join([p[0].upper() for p in str(x).split()[:2]]) if pd.notna(x) else "")

        df_latest = df.sort_values('Fecha de Evaluacion').groupby('DNI').tail(1).reset_index(drop=True)
        return df, df_latest

    except Exception as e:
        st.error(f"🚨 **ALERTA DE DATOS:** Se encontró un error matemático o de formato en el Google Sheets.")
        st.code(f"Detalle técnico: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()
