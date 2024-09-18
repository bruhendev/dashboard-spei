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
for year in range(dados.index.year.min(), dados.index.year.max() + 1, 10):
    dados_periodo = dados[dados.index.year.isin(range(year, year + 10))]
    if not dados_periodo.empty:
        spei_10_anos[year] = si.spei(pd.Series(dados_periodo['dados']))

# Inicialização do aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div(children=[
    html.H1(children='Dashboard de SPEI'),

    # Dropdown para selecionar o intervalo de anos
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': f"{year} a {year + 10}", 'value': year} for year in spei_10_anos.keys()],
        value=min(spei_10_anos.keys()),  # Valor inicial
        clearable=False
    ),

    dcc.Graph(id='spei-graph'),
    dcc.Graph(id='boxplot-graph')  # Gráfico Boxplot adicionado aqui
])

# Callback para atualizar o gráfico SPEI
@app.callback(
    Output('spei-graph', 'figure'),
    Input('year-dropdown', 'value')
)
def update_graph(selected_year):
    filtered_data = spei_10_anos[selected_year]

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

# Callback para o Boxplot Anual
@app.callback(
    Output('boxplot-graph', 'figure'),
    Input('year-dropdown', 'value')
)
def update_boxplot(selected_year):
    # Coletar dados para o intervalo selecionado
    anos_selecionados = range(selected_year, selected_year + 10)
    dados_anuais = dados[dados.index.year.isin(anos_selecionados)]
    
    # Criar uma lista para armazenar os valores do SPEI para cada ano
    dados_por_ano = [dados_anuais[dados_anuais.index.year == ano]['dados'].values for ano in anos_selecionados]

    # Criar o boxplot
    figure = {
        'data': [
            go.Box(
                y=dados_por_ano[i],
                name=str(anos_selecionados[i]),
                boxmean='sd'  # Adiciona a média e o desvio padrão no boxplot
            ) for i in range(len(dados_por_ano))
        ],
        'layout': go.Layout(
            title='Boxplot Anual do SPEI',
            yaxis={'title': 'SPEI'},
            xaxis={'title': 'Ano'}
        )
    }
    return figure

# Executa o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
