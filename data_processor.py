import pandas as pd
import numpy as np
import streamlit as st
import re
import requests
from io import BytesIO

# Nueva función para descargar la imagen desde el backend burlando a Google
@st.cache_data(ttl=3600) # Cacheamos la imagen 1 hora para que sea ultra rápido
def get_image_bytes(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None
    except:
        return None

@st.cache_data(ttl=60)
def load_data():
    SHEET_ID = "1FVuYJtctdiwUzsptZOGOZcr7vXe1CMqR4f360kulYME"
    GID_DATOS = "1766718688"
    
    url_datos = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_DATOS}"
    url_excel = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
    
    try:
        df = pd.read_csv(url_datos)
        
        try:
            df_int = pd.read_excel(url_excel, sheet_name='Interceptos', engine='openpyxl')
            df_int.columns = ['Edad_Anios', 'B0', 'B1', 'B2', 'B3']
        except:
            df_int = pd.DataFrame({'Edad_Anios': np.arange(10, 18, 0.5), 'B0': [-12]*16, 'B1': [0.8]*16, 'B2': [0.3]*16, 'B3': [0.4]*16})

        cols_limpiar = ['Altura de Pie ', 'Altura sentado', 'Peso', 'Altura del padre', 'Altura de la madre']
        for col in cols_limpiar:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['Fecha de Nacimiento'] = pd.to_datetime(df['Fecha de Nacimiento'], format='mixed', errors='coerce')
        df['Fecha de Evaluacion'] = pd.to_datetime(df['Fecha de Evaluacion'], format='mixed', errors='coerce')
        
        df['Mes_Año_Eval'] = df['Fecha de Evaluacion'].dt.strftime('%B %Y')
        df['Edad_Decimal'] = (df['Fecha de Evaluacion'] - df['Fecha de Nacimiento']).dt.days / 365.25
        
        df = df.sort_values(by=['DNI', 'Fecha de Evaluacion'])
        
        # FIX FOTO: Si la última evaluación no tiene foto, arrastra la foto de la evaluación anterior
        if 'URLFOTO' in df.columns:
            df['URLFOTO'] = df['URLFOTO'].replace(r'^\s*$', np.nan, regex=True)
            df['URLFOTO'] = df.groupby('DNI')['URLFOTO'].ffill().bfill()

        # FIX URL: Extrae el ID de cualquier formato de Drive y crea un link de descarga directa
        def normalize_photo_url(url):
            if pd.isna(url) or "ahi esta" in str(url): return np.nan
            url_str = str(url).strip()
            match1 = re.search(r'/d/([a-zA-Z0-9_-]+)', url_str)
            match3 = re.search(r'id=([a-zA-Z0-9_-]+)', url_str)
            
            file_id = None
            if match1: file_id = match1.group(1)
            elif match3: file_id = match3.group(1)
            
            if file_id:
                return f"https://drive.google.com/uc?export=download&id={file_id}"
            return url_str

        if 'URLFOTO' in df.columns:
            df['URLFOTO'] = df['URLFOTO'].apply(normalize_photo_url)

        # Cálculos de maduración
        df['Delta_Altura_cm'] = df.groupby('DNI')['Altura de Pie '].diff()
        df['Delta_Edad_años'] = df.groupby('DNI')['Edad_Decimal'].diff()
        df['Gr.T'] = np.where(df['Delta_Edad_años'] > 0, df['Delta_Altura_cm'] / df['Delta_Edad_años'], np.nan)

        df['Leg'] = df['Altura de Pie '] - df['Altura sentado']
        df['Pxt'] = np.where(df['Altura de Pie '] > 0, (df['Peso'] / df['Altura de Pie ']) * 100, np.nan)
        df['M.O'] = -9.236 + 0.0002708 * df['Leg'] * df['Altura sentado'] - 0.001663 * df['Edad_Decimal'] * df['Leg'] + 0.007216 * df['Edad_Decimal'] * df['Altura sentado'] + 0.02292 * df['Pxt']
        df['Edad PHV'] = df['Edad_Decimal'] - df['M.O']

        df['EdadParaTabla'] = (df['Edad_Decimal'] * 2).round() / 2
        df = pd.merge(df, df_int, left_on='EdadParaTabla', right_on='Edad_Anios', how='left')
        
        df['AltPadre_cm'] = np.where(df['Altura del padre'] < 3, df['Altura del padre'] * 100, df['Altura del padre'])
        df['AltMadre_cm'] = np.where(df['Altura de la madre'] < 3, df['Altura de la madre'] * 100, df['Altura de la madre'])
        df['Predictor_Genetico'] = ((df['AltPadre_cm'] + df['AltMadre_cm']) / 2).fillna(174.0)
        
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
        if "401" in str(e):
            st.error("🔒 **Error 401: El archivo Google Sheet es privado.**")
        else:
            st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()
