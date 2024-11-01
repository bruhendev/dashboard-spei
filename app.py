import dash
import os
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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Card de controles atualizado
controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Selecionar intervalo de anos"),
                dcc.Dropdown(
                    id='intervalo-dropdown',
                    options=[
                        {'label': '5 anos', 'value': '5'},
                        {'label': '10 anos', 'value': '10'},
                        {'label': 'Todos os anos', 'value': 'all'}
                    ],
                    value='10',  # Padrão para 10 anos
                    clearable=False,
                ),
                # Definindo o dropdown de ano
                dbc.Label("Selecionar ano"),
                dcc.Dropdown(
                    id='ano-dropdown',
                    options=[],  # Inicialmente vazio
                    value=None,  # Inicialmente None
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
                            dcc.Graph(id='spei-graph', config={'responsive': True}, style={'width': '100%', 'height': '400px'})
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
                            dcc.Graph(id='barras-empilhadas-graph', config={'responsive': True}, style={'width': '100%', 'height': '250px'}),
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
                            dcc.Graph(id='media-mensal-graph', config={'responsive': True}, style={'height': '250px'}),
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
                            dcc.Graph(id='histograma-graph', config={'responsive': True}, style={'height': '250px'}),
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
                            dcc.Graph(id='scatter-graph', config={'responsive': True}, style={'height': '280px'}),
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
                            dcc.Graph(id='boxplot-graph', config={'responsive': True}, style={'height': '280px'}),
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
    [Output('ano-dropdown', 'options'),
     Output('ano-dropdown', 'value')],  # Adicionando value aqui
    Input('intervalo-dropdown', 'value')
)
def atualizar_ano_dropdown(intervalo):
    anos_disponiveis = list(range(1981, 2023))  # Supondo que os dados vão até 2022
    opcoes = []
    
    if intervalo == '5':
        for ano in range(1981, 2023, 5):
            ano_final = ano + 4
            if ano_final <= anos_disponiveis[-1]:
                opcoes.append({'label': f'{ano} a {ano_final}', 'value': f'{ano}-{ano_final}'})
        if anos_disponiveis[-1] > 1981:
            opcoes.append({'label': f'{anos_disponiveis[-2]} a {anos_disponiveis[-1]}', 'value': f'{anos_disponiveis[-2]}-{anos_disponiveis[-1]}'})
            
    elif intervalo == '10':
        for ano in range(1981, 2023, 10):
            ano_final = ano + 9
            if ano_final <= anos_disponiveis[-1]:
                opcoes.append({'label': f'{ano} a {ano_final}', 'value': f'{ano}-{ano_final}'})
        if anos_disponiveis[-1] > 2020:
            opcoes.append({'label': f'{anos_disponiveis[-2]} a {anos_disponiveis[-1]}', 'value': f'{anos_disponiveis[-2]}-{anos_disponiveis[-1]}'})

    elif intervalo == 'all':
        opcoes = [{'label': '1981 a 2022', 'value': '1981-2022'}]

    # Define o value como a primeira opção se houver opções
    valor_default = opcoes[0]['value'] if opcoes else None

    return opcoes, valor_default  # Retornando as opções e o valor padrão


@app.callback(
    [Output('spei-graph', 'figure'),
     Output('barras-empilhadas-graph', 'figure'),
     Output('media-mensal-graph', 'figure'),
     Output('histograma-graph', 'figure'),
     Output('scatter-graph', 'figure'),
     Output('boxplot-graph', 'figure')],
    Input('ano-dropdown', 'value')
)
def atualizar_graficos(intervalo):
    if not intervalo:  # Se não houver intervalo selecionado
        raise dash.exceptions.PreventUpdate

    if intervalo == '1981-2022':
        ano_inicial, ano_final = 1981, 2022
    else:
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
            line=dict(color='gray', width=2)  # Espessura da linha
        )
    ],
    'layout': go.Layout(
        xaxis={
            'title': 'Data',
            'title_font': dict(color='black', size=14),
            'tickfont': dict(color='black', size=12),
            'showgrid': True,
            'gridcolor': 'lightgrey',
        },
        yaxis={
            'title': 'SPEI',
            'range': [-3, 3],
            'title_font': dict(color='black', size=14),
            'tickfont': dict(color='black', size=12),
            'showgrid': True,
            'gridcolor': 'lightgrey',
        },
        plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
        paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
        font=dict(color='black', size=12),  # Tamanho da fonte,
        margin=dict(t=40, l=50, r=40, b=50),  # Margens
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
        xaxis={
            'title': 'Ano',
            'title_font': dict(color='black', size=8),
            'tickfont': dict(color='black', size=8),
            'showgrid': True,
            'gridcolor': 'lightgrey',
        },
        yaxis={
            'title': 'Porcentagem',
            'title_font': dict(color='black', size=8),
            'tickfont': dict(color='black', size=8),
            'showgrid': True,
            'gridcolor': 'lightgrey',
        },
        plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
        paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
        font=dict(color='black', size=12),  # Tamanho da fonte
        legend=dict(traceorder='normal', font=dict(size=8)),  # Tamanho da fonte da legenda
        margin=dict(t=20, l=40, r=40, b=40),  # Margens
        bargap=0.1  # Espaçamento entre as barras
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
            marker=dict(color='gray', opacity=0.7)  # Adicionando opacidade
        )
    ],
    'layout': go.Layout(
        xaxis={
            'title': 'Meses',
            'title_font': dict(color='black', size=8),
            'tickfont': dict(color='black', size=8),
            'showgrid': True,
            'gridcolor': 'lightgrey',  # Cor da grade
        },
        yaxis={
            'title': 'SPEI',
            'title_font': dict(color='black', size=8),
            'tickfont': dict(color='black', size=8),
            'showgrid': True,
            'gridcolor': 'lightgrey',
        },
        plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
        paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
        font=dict(color='black', size=8),  # Tamanho da fonte
        margin=dict(t=20, l=40, r=25, b=40),  # Margens
    )
}

    # Gráfico de histograma
    histograma_figure = {
        'data': [
            go.Histogram(
                x=spei_filtrado.values,
                marker=dict(color='gray', opacity=0.75)  # Adicionando opacidade
            )
        ],
        'layout': go.Layout(
            xaxis={
                'title': 'SPEI',
                'title_font': dict(color='black', size=8),
                'tickfont': dict(color='black', size=8),
                'showgrid': True,
                'gridcolor': 'lightgrey',  # Cor da grade
            },
            yaxis={
                'title': 'Frequência',
                'title_font': dict(color='black', size=8),
                'tickfont': dict(color='black', size=8),
                'showgrid': True,
                'gridcolor': 'lightgrey',
            },
            plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
            paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
            font=dict(color='black', size=8),  # Tamanho da fonte
            margin=dict(t=20, l=40, r=25, b=40),  # Margens
        )
    }


    # Gráfico de dispersão
    scatter_figure = {
    'data': [
        go.Scatter(
            x=spei_filtrado.index,
            y=spei_filtrado.values,
            mode='markers',
            marker=dict(color='gray', size=7, opacity=0.8)  # Aumentando o tamanho e adicionando opacidade
        )
    ],
    'layout': go.Layout(
        xaxis={
            'title': 'Data',
            'title_font': dict(color='black', size=8),  # Tamanho da fonte do título
            'tickfont': dict(color='black', size=8),
            'showgrid': True,
            'gridcolor': 'lightgrey'  # Cor da grade
        },
        yaxis={
            'title': 'SPEI',
            'range': [-3, 3],
            'title_font': dict(color='black', size=8),  # Tamanho da fonte do título
            'tickfont': dict(color='black', size=8),
            'showgrid': True,
            'gridcolor': 'lightgrey'  # Cor da grade
        },
        plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
        paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
        margin=dict(t=20, l=40, r=25, b=40),  # Margens
        font=dict(color='black', size=8)  # Tamanho da fonte
    )
}


    # Gráfico de boxplot por ano
    boxplot_figure = {
        'data': [
            go.Box(
                y=spei_filtrado[spei_filtrado.index.year == ano].values,
                name=str(ano),
                marker=dict(color='gray'),
                boxmean='sd'  # Adiciona a média e desvio padrão
            ) for ano in spei_filtrado.index.year.unique()
        ],
        'layout': go.Layout(
            yaxis={
                'title': 'SPEI',
                'range': [-3, 3],
                'title_font': dict(color='black', size=8),  # Tamanho da fonte do título
                'tickfont': dict(color='black', size=8),
                'showgrid': True,
                'gridcolor': 'lightgrey'  # Cor da grade
            },
            xaxis={
                'title': 'Ano',
                'title_font': dict(color='black', size=8),  # Tamanho da fonte do título
                'tickfont': dict(color='black', size=8),
                'showgrid': True,
                'gridcolor': 'lightgrey'  # Cor da grade
            },
            plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
            paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
            margin=dict(t=30, l=40, r=25, b=40),  # Margens
            font=dict(color='black', size=8)  # Tamanho da fonte
        )
    }

    return linha_figure, barras_figure, media_mensal_figure, histograma_figure, scatter_figure, boxplot_figure 

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))
