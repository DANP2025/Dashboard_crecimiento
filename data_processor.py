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

@st.cache_data(ttl=60)
def load_data_v21():
    import pandas as pd
    import numpy as np
    import streamlit as st
    
    SHEET_ID = "1i21vHAG2ACXKz8M7_eHU9exMz6sGZ_vOBa4QXB1gjvE"
    GID_DATOS = "1766718688"
    GID_INTERCEPTOS = "1255743917"
    
    url_datos = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_DATOS}"
    url_interceptos = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_INTERCEPTOS}"
    
    try:
        # 1. Cargar Datos
        df = pd.read_csv(url_datos)
        df = df.dropna(subset=['Nombre y Apellido', 'Fecha de Evaluacion'], how='all')
        
        # 2. Cargar Interceptos de forma estricta
        df_int = pd.read_csv(url_interceptos)
        df_int = df_int.iloc[:, 0:5].copy() # Tomar las primeras 5 columnas sí o sí
        df_int.columns = ['Edad_Anios', 'B0', 'B1', 'B2', 'B3']
        
        for c in df_int.columns:
            if df_int[c].dtype == object:
                df_int[c] = df_int[c].astype(str).str.replace(',', '.')
            df_int[c] = pd.to_numeric(df_int[c], errors='coerce')
            
        # FIX CRÍTICO: Redondear a 1 decimal para evitar fallos de Merge en Linux
        df_int['Edad_Anios'] = df_int['Edad_Anios'].round(1)
        
        if df_int['B0'].isna().all():
            st.error("Error: Hoja de interceptos vacía.")
            st.stop()
            
    except Exception as e:
        st.error(f"Error en Google Sheets: {e}")
        st.stop()

    cols_limpiar = ['Altura de Pie ', 'Altura sentado', 'Peso', 'Altura del padre', 'Altura de la madre']
    for col in cols_limpiar:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace(r'[^0-9.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Categoria' in df.columns:
        df['Categoria'] = df['Categoria'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['Categoria'] = df['Categoria'].replace(['nan', 'None', ''], np.nan)

    df['Fecha de Nacimiento'] = pd.to_datetime(df['Fecha de Nacimiento'], format='mixed', dayfirst=True, errors='coerce')
    df['Fecha de Evaluacion'] = pd.to_datetime(df['Fecha de Evaluacion'], format='mixed', dayfirst=True, errors='coerce')
    
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    
    df['Mes_Año_Eval'] = df['Fecha de Evaluacion'].apply(
        lambda x: f"{meses_es[x.month]} {x.year}" if pd.notna(x) else np.nan
    )

    df['Edad_Decimal'] = (df['Fecha de Evaluacion'] - df['Fecha de Nacimiento']).dt.days / 365.25
    df = df.sort_values(by=['DNI', 'Fecha de Evaluacion'])
    
    cols_estaticas = ['Altura del padre', 'Altura de la madre', 'Posicion', 'URLFOTO']
    for col in cols_estaticas:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].replace(r'^\s*$', np.nan, regex=True)
            df[col] = df.groupby('DNI')[col].ffill().bfill()

    def normalize_photo_url(url):
        if pd.isna(url) or "ahi esta" in str(url): return np.nan
        url_str = str(url).strip()
        import re
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
    
    df['AltPadre_cm'] = np.where((df['Altura del padre'] > 0) & (df['Altura del padre'] < 3), df['Altura del padre'] * 100, df['Altura del padre'])
    df['AltMadre_cm'] = np.where((df['Altura de la madre'] > 0) & (df['Altura de la madre'] < 3), df['Altura de la madre'] * 100, df['Altura de la madre'])
    
    df['AltPadre_cm'] = np.where(df['AltPadre_cm'].isna() & df['AltMadre_cm'].notna(), df['AltMadre_cm'] + 13.0, df['AltPadre_cm'])
    df['AltMadre_cm'] = np.where(df['AltMadre_cm'].isna() & df['AltPadre_cm'].notna(), df['AltPadre_cm'] - 13.0, df['AltMadre_cm'])
    df['Predictor_Genetico'] = ((df['AltPadre_cm'] + df['AltMadre_cm']) / 2).fillna(174.0)
    
    has_parents = df['AltPadre_cm'].notna() & df['AltMadre_cm'].notna()
    moore2 = -7.999994 + 0.0036124 * (df['Edad_Decimal'] * df['Altura de Pie '])
    moore_padres = -7.999994 + 0.0036124 * (df['Edad_Decimal'] * df['Predictor_Genetico'])
    
    valid_mirwald = mirwald.between(-3.5, 2.5)
    df['M.O'] = np.where(valid_mirwald, mirwald, np.where(has_parents, moore_padres, moore2))
    
    df['Edad Biológica'] = df['Edad_Decimal'] + df['M.O']
    df['Edad PHV'] = df['Edad_Decimal'] - df['M.O']

    # FIX CRÍTICO DEL MERGE: Redondeamos también aquí a 1 decimal
    df['EdadParaTabla'] = (np.floor(df['Edad_Decimal'] * 2 + 0.5) / 2).round(1)
    df = pd.merge(df, df_int, left_on='EdadParaTabla', right_on='Edad_Anios', how='left')
    
    df['Altura_Adulta_Predicha'] = df['B0'] + (df['B1'] * df['Altura de Pie ']) + (df['B2'] * df['Peso']) + (df['B3'] * df['Predictor_Genetico'])
    df['% PHV'] = (df['Altura de Pie '] / df['Altura_Adulta_Predicha']) * 100

    def categorizar(row):
        if pd.isna(row['M.O']) or pd.isna(row['Gr.T']): return "Sin datos"
        if row['M.O'] < 0 and row['Gr.T'] < 7: return "Normal. Enfocar en técnica."
        if row['M.O'] < 0 and row['Gr.T'] >= 7: return "Reducir volumen. Evitar picos."
        if row['M.O'] >= 0 and row['Gr.T'] < 7: return "Progresión de fuerza."
        return "Limitar impacto."

    df['Decision_Entrenamiento'] = df.apply(categorizar, axis=1)
    df['Iniciales'] = df['Nombre y Apellido'].apply(lambda x: "".join([p[0].upper() for p in str(x).split()[:2]]) if pd.notna(x) else "")

    df_latest = df.sort_values('Fecha de Evaluacion').groupby('DNI').tail(1).reset_index(drop=True)
    return df, df_latest
