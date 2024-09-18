import spei as si
import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objs as go

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

# Caminhos dos arquivos
file_path_etp = 'dados/ETP_HARVREAVES_TERRACLIMATE.xlsx'
file_path_prp = 'dados/PRP_TERRACLIMATE.xlsx'

# Extração dos dados e cálculo do SPEI para diferentes períodos de acumulação
dados_1 = extrair_dados(file_path_etp, file_path_prp, 1)
spei_1 = si.spei(pd.Series(dados_1['dados']))

# Inicialização do aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div(children=[
    html.H1(children='Dashboard de SPEI'),

    dcc.Graph(
        id='spei-1-graph',
        figure={
            'data': [
                go.Scatter(
                    x=spei_1.index,
                    y=spei_1,
                    mode='lines',
                    name='SPEI-1'
                )
            ],
            'layout': go.Layout(
                title='SPEI-1 ao Longo do Tempo',
                xaxis={'title': 'Data'},
                yaxis={'title': 'SPEI'},
            )
        }
    ),
])

# Executa o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
