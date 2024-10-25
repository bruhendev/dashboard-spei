import spei as si
import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats

# Função para extrair dados
def extrair_dados(path_etp, path_prp, acumulado=1):
    df_etp = pd.read_excel(path_etp)
    df_etp = df_etp.rename(columns={'Hargreaves Potential Evapotranspiration (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_etp = df_etp.iloc[1:].reset_index(drop=True)

    df_prp = pd.read_excel(path_prp)
    df_prp = df_prp.rename(columns={'Precipitation (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_prp = df_prp.iloc[1:].reset_index(drop=True)

    df_merged = pd.merge(df_etp, df_prp, on='data', suffixes=('_etp', '_prp'))
    df_merged['balanco_hidrico'] = df_merged['dados_prp'] - df_merged['dados_etp']
    df_merged['data'] = pd.to_datetime(df_merged['data'], format='%Y-%m-%d')

    df = pd.DataFrame({
        'data': df_merged['data'],
        'dados': pd.to_numeric(df_merged['balanco_hidrico'])
    })
    df.set_index('data', inplace=True)

    df_preparado = pd.DataFrame({
        'data': df['dados'].rolling(acumulado).sum().dropna().index,
        'dados': df['dados'].rolling(acumulado).sum().dropna().values
    })
    df_preparado.set_index('data', inplace=True)

    return df_preparado

# Função para extrair dados somente de ETP e precipitação
def extrair_etp_prp(path_etp, path_prp):
    df_etp = pd.read_excel(path_etp).rename(columns={'Hargreaves Potential Evapotranspiration (TerraClimate)': 'data', 'Unnamed: 1': 'ETP'})
    df_prp = pd.read_excel(path_prp).rename(columns={'Precipitation (TerraClimate)': 'data', 'Unnamed: 1': 'Precipitação'})

    df_etp = df_etp.iloc[1:].reset_index(drop=True)
    df_prp = df_prp.iloc[1:].reset_index(drop=True)

    df_etp['data'] = pd.to_datetime(df_etp['data'], format='%Y-%m-%d')
    df_prp['data'] = pd.to_datetime(df_prp['data'], format='%Y-%m-%d')

    df_merged = pd.merge(df_etp, df_prp, on='data', how='inner')
    df_merged.set_index('data', inplace=True)

    return df_merged

# Caminhos dos arquivos
file_path_etp = 'dados/ETP_HARVREAVES_TERRACLIMATE.xlsx'
file_path_prp = 'dados/PRP_TERRACLIMATE.xlsx'

# Extração dos dados e cálculo do SPEI
dados_1 = extrair_dados(file_path_etp, file_path_prp, 1)
df_etp_prp = extrair_etp_prp(file_path_etp, file_path_prp)
spei_1 = si.spei(pd.Series(dados_1['dados']))

spei_df = pd.DataFrame(spei_1, columns=['SPEI'])
spei_df['decada'] = (spei_df.index.year // 10) * 10
stats_grouped = spei_df.groupby('decada')['SPEI'].agg(['mean', 'std', 'min', 'max'])

# Análise Descritiva
spei_values = spei_df['SPEI'].dropna()  # Remove valores NaN para a análise

# Medidas de Tendência Central
media = spei_values.mean()
mediana = spei_values.median()
moda_result = stats.mode(spei_values)

moda = moda_result.mode

# Medidas de Dispersão
variancia = spei_values.var()
desvio_padrao = spei_values.std()

# Exibindo os resultados
print("Análise Descritiva do SPEI:")
print(f"Média: {media:.2f}")
print(f"Mediana: {mediana:.2f}")
print(f"Moda: {moda:.2f}")
print(f"Variância: {variancia:.2f}")
print(f"Desvio Padrão: {desvio_padrao:.2f}")


# Aplicação Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Graph(
        id='grafico-spei',
        figure={
            'data': [
                go.Bar(
                    x=stats_grouped.index,
                    y=stats_grouped['mean'],
                    name='Média SPEI',
                )
            ],
            'layout': go.Layout(title='Média SPEI a cada 10 anos')
        }
    ),
    html.Div([
        html.H4("Análise Descritiva do SPEI:"),
        html.P(f"Média: {media:.2f}"),
        html.P(f"Mediana: {mediana:.2f}"),
        html.P(f"Moda: {moda:.2f}"),
        html.P(f"Variância: {variancia:.2f}"),
        html.P(f"Desvio Padrão: {desvio_padrao:.2f}")
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
