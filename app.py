import spei as si
import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

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

# Função para filtrar os anos
def filtrarPorAno(spei, ano_inicial, ano_final):
    return spei[(spei.index.year >= ano_inicial) & (spei.index.year <= ano_final)]

# Função para categorizar SPEI com os novos limites
def categorizar_spei(spei_value):
    if spei_value > 2.33:
        return 'Umidade extrema'
    elif spei_value > 1.65:
        return 'Umidade severa'
    elif spei_value > 1.28:
        return 'Umidade moderada'
    elif spei_value > 0.84:
        return 'Condições normais de umidade'
    elif spei_value > -0.84:
        return 'Condições normais de umidade'
    elif spei_value > -1.28:
        return 'Seca moderada'
    elif spei_value > -1.65:
        return 'Seca severa'
    elif spei_value > -2.33:
        return 'Seca extrema'
    else:
        return 'Seca extrema'

# Inicialização do aplicativo Dash com tema Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Layout do aplicativo
app.layout = dbc.Container(fluid=True, style={'height': '100vh'}, children=[
    dbc.Row(dbc.Col(html.H1(children='Dashboard de SPEI', className='text-center text-light'))),

    dbc.Row([
        # Coluna para o combo box
        dbc.Col(
            dcc.Dropdown(
                id='ano-dropdown',
                options=[{'label': f'{ano} a {ano + 10}', 'value': f'{ano}-{ano + 9}'} for ano in range(1981, 2012, 10)] +
                         [{'label': '2021 a 2022', 'value': '2021-2022'}],
                value='1981-1990',  # Valor padrão
                clearable=False,
                className='mb-4'
            ), width=2
        ),

        # Coluna para os gráficos
        dbc.Col(
            children=[
                dbc.Row([dbc.Col(dcc.Graph(id='spei-1-graph'), width=12)]),
                dbc.Row([dbc.Col(dcc.Graph(id='barras-empilhadas-graph'), width=12)]),
                dbc.Row([dbc.Col(dcc.Graph(id='bar-graph'), width=12)]),
                dbc.Row([dbc.Col(dcc.Graph(id='area-graph'), width=12)]),
                dbc.Row([dbc.Col(dcc.Graph(id='histograma-graph'), width=12)]),
                dbc.Row([dbc.Col(dcc.Graph(id='scatter-graph'), width=12)])
            ],
            width=10,
            style={'overflowY': 'auto', 'height': '100%', 'padding': '1rem'}
        )
    ], style={'height': '100%'})
])

# Callback para atualizar os gráficos
@app.callback(
    [Output('spei-1-graph', 'figure'),
     Output('barras-empilhadas-graph', 'figure'),
     Output('bar-graph', 'figure'),
     Output('area-graph', 'figure'),
     Output('histograma-graph', 'figure'),
     Output('scatter-graph', 'figure')],
    Input('ano-dropdown', 'value')
)
def atualizar_graficos(intervalo):
    ano_inicial, ano_final = map(int, intervalo.split('-'))

    # Filtrando SPEI
    spei_filtrado = filtrarPorAno(spei_1, ano_inicial, ano_final)

    # Criando as categorias para os valores de SPEI
    categorias = spei_filtrado.apply(categorizar_spei)
    contagem_categorias = categorias.value_counts()

    # Calculando a porcentagem para cada categoria
    porcentagem_categorias = (contagem_categorias / contagem_categorias.sum()) * 100

    # Agrupando por ano
    dados_ano = spei_filtrado.groupby(spei_filtrado.index.year).apply(lambda x: x.apply(categorizar_spei).value_counts(normalize=True) * 100).unstack(fill_value=0)

    # Gráfico de linha SPEI
    linha_figure = {
        'data': [
            go.Scatter(
                x=spei_filtrado.index,
                y=spei_filtrado.values,
                mode='lines',
                name=f'SPEI de {ano_inicial} a {ano_final + 1}',
                line=dict(color='cyan')
            )
        ],
        'layout': go.Layout(
            title=f'SPEI de {ano_inicial} a {ano_final}',
            xaxis={'title': 'Data'},
            yaxis={'title': 'SPEI', 'range': [-3, 3]},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
    }

    # Gráfico de barras empilhadas
    barras_empilhadas_figure = {
        'data': [
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get('Umidade extrema', [0]*len(dados_ano)),
                name='Umidade extrema'
            ),
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get('Umidade severa', [0]*len(dados_ano)),
                name='Umidade severa',
                base=dados_ano.get('Umidade extrema', [0]*len(dados_ano))
            ),
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get('Umidade moderada', [0]*len(dados_ano)),
                name='Umidade moderada',
                base=[i + j for i, j in zip(dados_ano.get('Umidade extrema', [0]*len(dados_ano)), dados_ano.get('Umidade severa', [0]*len(dados_ano)))]
            ),
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get('Condições normais de umidade', [0]*len(dados_ano)),
                name='Condições normais de umidade',
                base=[i + j + k for i, j, k in zip(
                    dados_ano.get('Umidade extrema', [0]*len(dados_ano)),
                    dados_ano.get('Umidade severa', [0]*len(dados_ano)),
                    dados_ano.get('Umidade moderada', [0]*len(dados_ano))
                )]
            ),
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get('Seca moderada', [0]*len(dados_ano)),
                name='Seca moderada',
                base=[i + j + k + l for i, j, k, l in zip(
                    dados_ano.get('Umidade extrema', [0]*len(dados_ano)),
                    dados_ano.get('Umidade severa', [0]*len(dados_ano)),
                    dados_ano.get('Umidade moderada', [0]*len(dados_ano)),
                    dados_ano.get('Condições normais de umidade', [0]*len(dados_ano))
                )]
            ),
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get('Seca severa', [0]*len(dados_ano)),
                name='Seca severa',
                base=[i + j + k + l + m for i, j, k, l, m in zip(
                    dados_ano.get('Umidade extrema', [0]*len(dados_ano)),
                    dados_ano.get('Umidade severa', [0]*len(dados_ano)),
                    dados_ano.get('Umidade moderada', [0]*len(dados_ano)),
                    dados_ano.get('Condições normais de umidade', [0]*len(dados_ano)),
                    dados_ano.get('Seca moderada', [0]*len(dados_ano))
                )]
            ),
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get('Seca extrema', [0]*len(dados_ano)),
                name='Seca extrema',
                base=[i + j + k + l + m + n for i, j, k, l, m, n in zip(
                    dados_ano.get('Umidade extrema', [0]*len(dados_ano)),
                    dados_ano.get('Umidade severa', [0]*len(dados_ano)),
                    dados_ano.get('Umidade moderada', [0]*len(dados_ano)),
                    dados_ano.get('Condições normais de umidade', [0]*len(dados_ano)),
                    dados_ano.get('Seca moderada', [0]*len(dados_ano)),
                    dados_ano.get('Seca severa', [0]*len(dados_ano))
                )]
            )
        ],
        'layout': go.Layout(
            title='Porcentagem das Categorias de SPEI por Ano',
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Porcentagem'},
            barmode='stack',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
    }



    # Gráfico de barras: ETP e precipitação
    bar_figure = {
        'data': [
            go.Scatter(
                x=df_etp_prp.index,
                y=df_etp_prp['ETP'],
                name='Evapotranspiração (ETP)',
                mode='lines',
                line=dict(color='blue')
            ),
            go.Bar(
                x=df_etp_prp.index,
                y=df_etp_prp['Precipitação'],
                name='Precipitação',
                marker=dict(color='green')
            )
        ],
        'layout': go.Layout(
            title='ETP e Precipitação por Período',
            xaxis={'title': 'Data'},
            yaxis={'title': 'Valor'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
    }

    # Gráfico de área: Acumulado de SPEI
    area_figure = {
        'data': [
            go.Scatter(
                x=spei_filtrado.index,
                y=spei_filtrado.cumsum(),
                mode='lines',
                fill='tozeroy',
                name='Acumulado SPEI',
                line=dict(color='orange')
            )
        ],
        'layout': go.Layout(
            title='Acumulado de SPEI',
            xaxis={'title': 'Data'},
            yaxis={'title': 'SPEI Acumulado'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
    }

    # Gráfico de histograma: Distribuição de frequência do SPEI
    histograma_figure = {
        'data': [
            go.Histogram(
                x=spei_filtrado.values,
                nbinsx=20,
                marker=dict(color='blue'),
                opacity=0.75
            )
        ],
        'layout': go.Layout(
            title='Distribuição de Frequência do SPEI',
            xaxis={'title': 'SPEI'},
            yaxis={'title': 'Frequência'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
    }

    # Gráfico de dispersão: Relação entre SPEI e tempo
    scatter_figure = {
        'data': [
            go.Scatter(
                x=spei_filtrado.index,
                y=spei_filtrado.values,
                mode='markers',
                marker=dict(color='purple', size=8),
                name='SPEI vs Tempo'
            )
        ],
        'layout': go.Layout(
            title='Relação entre SPEI e Tempo',
            xaxis={'title': 'Data'},
            yaxis={'title': 'SPEI'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
    }

    return linha_figure, barras_empilhadas_figure, bar_figure, area_figure, histograma_figure, scatter_figure

if __name__ == '__main__':
    app.run_server(debug=True)
