import spei as si
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go

# Função para extrair dados
def extrair_dados(path_etp, path_prp):
    # Leitura e preparação dos dados de ETP
    df_etp = pd.read_excel(path_etp)
    df_etp = df_etp.rename(columns={'Hargreaves Potential Evapotranspiration (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_etp = df_etp.iloc[1:].reset_index(drop=True)

    # Leitura e preparação dos dados de precipitação
    df_prp = pd.read_excel(path_prp)
    df_prp = df_prp.rename(columns={'Precipitation (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_prp = df_prp.iloc[1:].reset_index(drop=True)

    # Mesclagem dos DataFrames
    df_merged = pd.merge(df_etp, df_prp, on='data', suffixes=('_etp', '_prp'))
    df_merged['balanco_hidrico'] = df_merged['dados_prp'] - df_merged['dados_etp']
    df_merged['data'] = pd.to_datetime(df_merged['data'], format='%Y-%m-%d')

    # Criação do DataFrame final
    df = pd.DataFrame({
        'data': df_merged['data'],
        'dados': pd.to_numeric(df_merged['balanco_hidrico'])
    })
    df.set_index('data', inplace=True)

    return df

# Caminhos dos arquivos
file_path_etp = 'dados/ETP_HARVREAVES_TERRACLIMATE.xlsx'
file_path_prp = 'dados/PRP_TERRACLIMATE.xlsx'

# Extração dos dados
dados = extrair_dados(file_path_etp, file_path_prp)

# Cálculo do SPEI a cada 10 anos
spei_10_anos = {}
intervalos = []
for year in range(dados.index.year.min(), dados.index.year.max() + 1, 10):
    dados_periodo = dados[dados.index.year.isin(range(year, year + 10))]
    if not dados_periodo.empty:
        spei_10_anos[year] = si.spei(pd.Series(dados_periodo['dados']))
        intervalo_label = f"{year} a {year + 10 if year + 10 <= dados.index.year.max() else dados.index.year.max()}"
        intervalos.append({'label': intervalo_label, 'value': year})

# Inicialização do aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div(children=[
    html.H1(children='Dashboard de SPEI'),

    # Dropdown para selecionar o intervalo de anos
    dcc.Dropdown(
        id='year-dropdown',
        options=intervalos,
        value=min(spei_10_anos.keys()),  # Valor inicial
        clearable=False
    ),

    dcc.Graph(id='spei-graph')
])

# Callback para atualizar o gráfico
@app.callback(
    Output('spei-graph', 'figure'),
    Input('year-dropdown', 'value')
)
def update_graph(selected_year):
    # Obtém o SPEI para o ano selecionado
    filtered_data = spei_10_anos[selected_year]

    # Criação do gráfico
    figure = {
        'data': [
            go.Scatter(
                x=filtered_data.index,
                y=filtered_data,
                mode='lines',
                name=f'SPEI - {selected_year} a {selected_year + 10}'
            )
        ],
        'layout': go.Layout(
            title=f'SPEI a Cada 10 Anos - {selected_year} a {selected_year + 10}',
            xaxis={'title': 'Data'},
            yaxis={'title': 'SPEI'},
        )
    }
    return figure

# Executa o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
