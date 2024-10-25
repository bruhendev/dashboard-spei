import spei as si
import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np
from sklearn.linear_model import LinearRegression

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
stats = spei_df.groupby('decada')['SPEI'].agg(['mean', 'std', 'min', 'max'])

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Graph(
        id='grafico-spei',
        figure={
            'data': [
                go.Bar(
                    x=stats.index,
                    y=stats['mean'],
                    name='Média SPEI',
                )
            ],
            'layout': go.Layout(title='Média SPEI a cada 10 anos')
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)


# # Supondo que 'spei_1' é uma série temporal do SPEI
# spei_df = pd.DataFrame(spei_1, columns=['SPEI'])
# spei_df['ano'] = spei_df.index.year

# # Regressão Linear
# X = spei_df['ano'].values.reshape(-1, 1)  # Variável independente (anos)
# y = spei_df['SPEI'].values  # Variável dependente (SPEI)

# model = LinearRegression().fit(X, y)

# # Coeficientes
# slope = model.coef_[0]
# intercept = model.intercept_
# print(f"Coeficiente angular (slope): {slope}")
# print(f"Intercepto: {intercept}")

# import matplotlib.pyplot as plt

# # Predição
# spei_df['tendencia'] = model.predict(X)

# # Gráfico
# plt.figure(figsize=(12, 6))
# plt.plot(spei_df.index, spei_df['SPEI'], label='SPEI', color='blue')
# plt.plot(spei_df.index, spei_df['tendencia'], label='Tendência Linear', color='red', linestyle='--')
# plt.title('SPEI e Tendência Linear')
# plt.xlabel('Ano')
# plt.ylabel('SPEI')
# plt.legend()
# plt.show()
