import dash
from dash import Input, Output, dcc, html
import spei as si
import pandas as pd
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

# Função para extrair dados (sem alterações)
def extrair_dados(path_etp, path_prp, acumulado=1):
    df_etp = pd.read_excel(path_etp).rename(columns={'Hargreaves Potential Evapotranspiration (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_etp = df_etp.iloc[1:].reset_index(drop=True)

    df_prp = pd.read_excel(path_prp).rename(columns={'Precipitation (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_prp = df_prp.iloc[1:].reset_index(drop=True)

    df_merged = pd.merge(df_etp, df_prp, on='data', suffixes=('_etp', '_prp'))
    df_merged['balanco_hidrico'] = df_merged['dados_prp'] - df_merged['dados_etp']
    df_merged['data'] = pd.to_datetime(df_merged['data'], format='%Y-%m-%d')

    df = pd.DataFrame({'data': df_merged['data'], 'dados': pd.to_numeric(df_merged['balanco_hidrico'])})
    df.set_index('data', inplace=True)

    df_preparado = pd.DataFrame({'data': df['dados'].rolling(acumulado).sum().dropna().index,
                                  'dados': df['dados'].rolling(acumulado).sum().dropna().values})
    df_preparado.set_index('data', inplace=True)

    return df_preparado

# Função para extrair dados somente de ETP e precipitação (sem alterações)
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

# Caminhos dos arquivos (sem alterações)
file_path_etp = 'dados/ETP_HARVREAVES_TERRACLIMATE.xlsx'
file_path_prp = 'dados/PRP_TERRACLIMATE.xlsx'

# Extração dos dados e cálculo do SPEI (sem alterações)
dados_1 = extrair_dados(file_path_etp, file_path_prp, 1)
df_etp_prp = extrair_etp_prp(file_path_etp, file_path_prp)
spei_1 = si.spei(pd.Series(dados_1['dados']))

# Função para filtrar os anos (sem alterações)
def filtrar_por_ano(spei, ano_inicial, ano_final):
    return spei[(spei.index.year >= ano_inicial) & (spei.index.year <= ano_final)]

# Função para categorizar SPEI (sem alterações)
def categorizar_spei(spei_value):
    if spei_value > 2.33:
        return 'Umidade extrema'
    elif spei_value > 1.65:
        return 'Umidade severa'
    elif spei_value > 1.28:
        return 'Umidade moderada'
    elif spei_value > 0.84:
        return 'Condição normal'
    elif spei_value > -0.84:
        return 'Condição normal'
    elif spei_value > -1.28:
        return 'Seca moderada'
    elif spei_value > -1.65:
        return 'Seca severa'
    elif spei_value > -2.33:
        return 'Seca extrema'
    else:
        return 'Seca extrema'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'])

# Card de controles (sem alterações)
controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Selecionar ano"),
                dcc.Dropdown(
                    id='ano-dropdown',
                    options=[{'label': f'{ano} a {ano + 10}', 'value': f'{ano}-{ano + 9}'} for ano in range(1981, 2012, 10)] +
                             [{'label': '2021 a 2022', 'value': '2021-2022'}],
                    value='1981-1990',
                    clearable=False,
                ),
            ]
        ),
    ],
    body=True,
)

# Layout do aplicativo (sem alterações)
app.layout = dbc.Container(
    [
        html.H1("Dashboard de SPEI"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("SPEI"),
                            dcc.Graph(id='spei-graph')
                        ],
                        className='card-shadow',
                    ), md=8),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Distribuição de Categorias de SPEI"),
                            dcc.Graph(id='barras-empilhadas-graph'),
                        ],
                        className='card-shadow',
                        style={'marginTop': '20px', 'marginBottom': '20px'}
                    ),
                    md=4
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Média Mensal de SPEI"),
                            dcc.Graph(id='media-mensal-graph'),
                        ],
                        className='card-shadow',
                        style={'marginTop': '20px', 'marginBottom': '20px'}
                    ),
                    md=4
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Histograma de SPEI"),
                            dcc.Graph(id='histograma-graph'),
                        ],
                        className='card-shadow',
                        style={'marginTop': '20px', 'marginBottom': '20px'}
                    ),
                    md=4
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Dispersão de SPEI ao longo do tempo"),
                            dcc.Graph(id='scatter-graph'),
                        ],
                        className='card-shadow',
                        style={'marginBottom': '20px'}
                    ),
                    md=6
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Boxplot de SPEI por Ano"),
                            dcc.Graph(id='boxplot-graph'),
                        ],
                        className='card-shadow',
                        style={'marginBottom': '20px'}
                    ),
                    md=6
                )
            ],
            align="center",
        ),
    ],
    fluid=True,
)

@app.callback(
    [Output('spei-graph', 'figure'),
     Output('barras-empilhadas-graph', 'figure'),
     Output('media-mensal-graph', 'figure'),  # Gráfico de média mensal
     Output('histograma-graph', 'figure'),
     Output('scatter-graph', 'figure'),
     # Removido Output para o gráfico de área
     Output('boxplot-graph', 'figure')],  # Adicionado boxplot
    Input('ano-dropdown', 'value')
)
def atualizar_graficos(intervalo):
    ano_inicial, ano_final = map(int, intervalo.split('-'))
    spei_filtrado = filtrar_por_ano(spei_1, ano_inicial, ano_final)
    categorias = spei_filtrado.apply(categorizar_spei)
    dados_ano = spei_filtrado.groupby(spei_filtrado.index.year).apply(lambda x: x.apply(categorizar_spei).value_counts(normalize=True) * 100).unstack(fill_value=0)

    font_style = dict(family='Arial, sans-serif', size=8, color='black')

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
            title=f'{ano_inicial} a {ano_final}',
            xaxis={'title': 'Data', 'title_font': dict(color='black'), 'tickfont': dict(color='black')},
            yaxis={'title': 'SPEI', 'range': [-3, 3], 'title_font': dict(color='black'), 'tickfont': dict(color='black')},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='black'),
            legend=dict(title='Legenda', font=font_style)
        )
    }

    # Dicionário de cores
    cores_categorias = {
        'Seca extrema': '#8B1A1A',
        'Seca severa': '#DE2929',
        'Seca moderada': '#F3641D',
        'Condição normal': '#22c55e',
        'Umidade moderada': '#FDC404',
        'Umidade severa': '#03F2FD',
        'Umidade extrema': '#1771DE',
    }

    # Gráfico de barras empilhadas
    barras_figure = {
        'data': [
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get(categoria, pd.Series([0] * len(dados_ano.index))),
                name=categoria,
                marker=dict(color=cores_categorias[categoria])
            ) for categoria in [
                'Umidade extrema',
                'Umidade severa',
                'Umidade moderada',
                'Condição normal',
                'Seca moderada',
                'Seca severa',
                'Seca extrema',             
                ]
        ],
        'layout': go.Layout(
            barmode='stack',
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Porcentagem'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='black'),
            legend=dict(traceorder='normal'),
            margin=dict(t=20),
        )
    }

    # Gráfico de média mensal
    media_mensal = spei_filtrado.resample('M').mean()
    media_mensal_por_mes = media_mensal.groupby(media_mensal.index.month).mean()  # Média por mês
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    media_mensal_figure = {
        'data': [
            go.Bar(
                x=meses,
                y=media_mensal_por_mes.values,
                name='Média Mensal de SPEI',
                marker=dict(color='blue')
            )
        ],
        'layout': go.Layout(
            xaxis={'title': 'Meses'},
            yaxis={'title': 'SPEI'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20),
        )
    }

    # Gráfico de histograma
    histograma_figure = {
        'data': [
            go.Histogram(
                x=spei_filtrado.values,
                marker=dict(color='purple'),
                opacity=0.75
            )
        ],
        'layout': go.Layout(
            xaxis={'title': 'SPEI', 'title_font': dict(color='black'), 'tickfont': dict(color='black')},
            yaxis={'title': 'Frequência', 'title_font': dict(color='black'), 'tickfont': dict(color='black')},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20),
        )
    }

    # Gráfico de dispersão
    scatter_figure = {
        'data': [
            go.Scatter(
                x=spei_filtrado.index,
                y=spei_filtrado.values,
                mode='markers',
                marker=dict(color='green', size=5)
            )
        ],
        'layout': go.Layout(
            xaxis={'title': 'Data', 'title_font': dict(color='black'), 'tickfont': dict(color='black')},
            yaxis={'title': 'SPEI', 'range': [-3, 3],'title_font': dict(color='black'), 'tickfont': dict(color='black')},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20),
        )
    }

    # Gráfico de boxplot por ano
    boxplot_figure = {
        'data': [
            go.Box(
                y=spei_filtrado[spei_filtrado.index.year == ano].values,
                name=str(ano),
                marker=dict(color='purple')
            ) for ano in spei_filtrado.index.year.unique()
        ],
        'layout': go.Layout(
            yaxis={'title': 'SPEI', 'range': [-3, 3]},
            xaxis={'title': 'Ano'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30),
        )
    }

    return linha_figure, barras_figure, media_mensal_figure, histograma_figure, scatter_figure, boxplot_figure  # Removido area_figure

if __name__ == "__main__":
    app.run_server(debug=True, port=8888)
