import spei as si
import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output

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

# Extração dos dados e cálculo do SPEI
dados_1 = extrair_dados(file_path_etp, file_path_prp, 1)
spei_1 = si.spei(pd.Series(dados_1['dados']))

# Função para filtrar os anos
def filtrarPorAno(spei, ano_inicial, ano_final):
    if not isinstance(spei.index, pd.DatetimeIndex):
        raise ValueError("O índice de 'spei' deve ser do tipo DatetimeIndex.")
    
    return spei[(spei.index.year >= ano_inicial) & (spei.index.year <= ano_final)]

# Inicialização do aplicativo Dash
app = dash.Dash(__name__)

# Layout do aplicativo
app.layout = html.Div(children=[
    html.H1(children='Dashboard de SPEI'),

    dcc.Dropdown(
        id='ano-dropdown',
        options=[
            {'label': f'{ano} a {ano + 10}', 'value': f'{ano}-{ano + 9}'} for ano in range(1981, 2012, 10)
        ] + [
            {'label': '2021 a 2022', 'value': '2021-2022'}
        ],
        value='1981-1990',  # Valor padrão
        clearable=False
    ),

    dcc.Graph(id='spei-1-graph'),
    dcc.Graph(id='boxplot-graph'),
    dcc.Graph(id='histogram-graph')  # Adicionando o gráfico de histograma
])

# Callback para atualizar os gráficos
@app.callback(
    [Output('spei-1-graph', 'figure'),
     Output('boxplot-graph', 'figure'),
     Output('histogram-graph', 'figure')],  # Adicionando a saída para o histograma
    Input('ano-dropdown', 'value')
)
def atualizar_graficos(intervalo):
    ano_inicial, ano_final = map(int, intervalo.split('-'))
    spei_filtrado = filtrarPorAno(spei_1, ano_inicial, ano_final)

    # Gráfico de linha
    linha_figure = {
        'data': [
            go.Scatter(
                x=spei_filtrado.index,
                y=spei_filtrado.values,
                mode='lines',
                name=f'SPEI de {ano_inicial} a {ano_final + 1}'
            )
        ],
        'layout': go.Layout(
            title=f'SPEI de {ano_inicial} a {ano_final}',
            xaxis={
                'title': 'Data',
                'tickvals': pd.date_range(start=f'{ano_inicial}-01-01', end=f'{ano_final + 1}-01-01', freq='YS'),
                'ticktext': [str(ano) for ano in range(ano_inicial, ano_final + 1)],
                'range': [spei_filtrado.index.min() - pd.DateOffset(months=1), spei_filtrado.index.max() + pd.DateOffset(months=1)]
            },
            yaxis={
                'title': 'SPEI',
                'range': [-3, 3]
            },
            hovermode='closest'
        )
    }

    # Gráfico de boxplot por ano
    anos = range(ano_inicial, ano_final + 1)
    boxplot_data = []

    for ano in anos:
        # Filtrando os dados para o ano específico
        dados_ano = spei_filtrado[spei_filtrado.index.year == ano]
        boxplot_data.append(go.Box(
            y=dados_ano.values,
            name=str(ano),
            boxmean='sd'
        ))

    boxplot_figure = {
        'data': boxplot_data,
        'layout': go.Layout(
            title=f'Boxplot de SPEI de {ano_inicial} a {ano_final}',
            yaxis={
                'title': 'SPEI',
                'range': [-3, 3]
            }
        )
    }

    # Gráfico de histograma
    histogram_figure = {
        'data': [
            go.Histogram(
                x=spei_filtrado.values,
                nbinsx=30,  # Número de bins do histograma
                name='Distribuição de SPEI'
            )
        ],
        'layout': go.Layout(
            title='Histograma de SPEI',
            xaxis={'title': 'SPEI'},
            yaxis={'title': 'Frequência'},
            bargap=0.2
        )
    }

    return linha_figure, boxplot_figure, histogram_figure  # Retornando também o gráfico de histograma

# Executa o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
