import dash
import os
from dash import Input, Output, dcc, html
import spei as si
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import dash_bootstrap_components as dbc
from datetime import datetime

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

# Função para categorizar o SPEI com as novas categorias
def categorizar_spei(spei_value):
    if spei_value >= 2.00:
        return 'Umidade extrema'
    elif 1.50 <= spei_value < 2.00:
        return 'Umidade severa'
    elif 1.00 <= spei_value < 1.50:
        return 'Umidade moderada'
    elif 0 <= spei_value < 1.00:
        return 'Umidade fraca'
    elif -0.99 <= spei_value < 0:
        return 'Seca fraca'
    elif -1.50 <= spei_value < -1.00:
        return 'Seca moderada'
    elif -1.99 <= spei_value < -1.50:
        return 'Seca severa'
    else:
        return 'Seca extrema'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title='Variabilidade do clima em Paragominas')

# Definindo variáveis de estilo
CARD_STYLE = {
    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'borderRadius': '10px',
    'marginBottom': '20px',
    'border': 'none'
}

TITLE_STYLE = {
    'color': '#2C3E50',
    'fontWeight': '600',
    'textAlign': 'center',
    'marginBottom': '20px'
}

DROPDOWN_STYLE = {
    'marginBottom': '15px',
    'borderRadius': '5px'
}

# Define modern footer styles
FOOTER_STYLE = {
    'backgroundColor': '#1e3a8a',  # Dark blue background
    'color': '#ffffff',
    'padding': '60px 0 40px 0',
    'marginTop': '50px',
    'width': '100%'
}

FOOTER_HEADING_STYLE = {
    'fontSize': '28px',
    'fontWeight': '700',
    'marginBottom': '24px',
    'color': '#ffffff'
}

FOOTER_LINK_STYLE = {
    'color': '#60a5fa',  # Light blue for links
    'textDecoration': 'none',
    'fontSize': '16px',
    'display': 'block',
    'marginBottom': '12px',
    'transition': 'color 0.3s ease'
}

CONTACT_ITEM_STYLE = {
    'marginBottom': '16px',
    'fontSize': '16px',
    'color': '#cbd5e1'  # Light gray text
}

SOCIAL_ICON_STYLE = {
    'color': '#60a5fa',
    'fontSize': '24px',
    'marginRight': '20px',
    'transition': 'color 0.3s ease'
}

# Create modern footer component
footer = html.Footer(
    dbc.Container(
        [
            dbc.Row(
                [
                    # Left Column - About
                    dbc.Col(
                        [
                            html.H2("VARIABILIDADE DA SECA NA REGIÃO DE PARAGOMINAS", style=FOOTER_HEADING_STYLE),
                            html.P(
                                "Desenvolvido no âmbito do Programa de Pós-Graduação em Gestão de Riscos "
                                "e Desastres Naturais na Amazônia (PPGGRD).",
                                style={'color': '#cbd5e1', 'fontSize': '16px', 'maxWidth': '400px', 'lineHeight': '1.6'}
                            )
                        ],
                        md=4,
                        className="mb-4 mb-md-0"
                    ),
                    
                    # Middle Column - Links
                    dbc.Col(
                        [
                            html.H3("Links Úteis", style={'fontSize': '20px', 'fontWeight': '600', 'marginBottom': '20px', 'color': '#ffffff'}),
                            html.A("Universidade Federal do Pará - UFPA", href="https://portal.ufpa.br/", target="_blank", style=FOOTER_LINK_STYLE),
                            html.A("Instituto de Geociências  - IG", href="https://ig.ufpa.br/", target="_blank", style=FOOTER_LINK_STYLE),
                            html.A(" Programa de Pós-Graduação em Gestão de Risco e Desastre na Amazônia - PPGGRD", href="https://ppggrd.propesp.ufpa.br/", target="_blank", style=FOOTER_LINK_STYLE),
                        ],
                        md=4,
                        className="mb-4 mb-md-0"
                    ),
                    
                    # Right Column - Contact
                    dbc.Col(
                        [
                            html.H3("Contato", style={'fontSize': '20px', 'fontWeight': '600', 'marginBottom': '20px', 'color': '#ffffff'}),
                            html.Div([
                                html.P("Email", style={'color': '#ffffff', 'fontWeight': '600', 'marginBottom': '4px'}),
                                html.A("ppggrd@ufpa.br", href="mailto:ppggrd@ufpa.br", style=FOOTER_LINK_STYLE)
                            ], style=CONTACT_ITEM_STYLE),
                            html.Div([
                                html.P("Endereço", style={'color': '#ffffff', 'fontWeight': '600', 'marginBottom': '4px'}),
                                html.P("Universidade Federal do Pará", style=CONTACT_ITEM_STYLE),
                                html.P("Instituto de Geociências", style=CONTACT_ITEM_STYLE),
                            ]),
                            # Social Media Icons
                            html.Div(
                                [
                                    html.A(html.I(className="fab fa-instagram"), href="https://www.instagram.com/ppggrd_ufpa?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==", style=SOCIAL_ICON_STYLE),
                                ],
                                style={'marginTop': '24px'}
                            )
                        ],
                        md=4
                    ),
                ],
                className="mb-4"
            ),
            # Copyright row
            dbc.Row(
                dbc.Col(
                    html.P(
                        f"© {datetime.now().year} PPGGRD - UFPA. Todos os direitos reservados.",
                        className="text-center",
                        style={'borderTop': '1px solid #2d4a8c', 'paddingTop': '20px', 'marginTop': '20px', 'color': '#cbd5e1'}
                    )
                )
            )
        ],
        fluid=True
    ),
    style=FOOTER_STYLE
)

# Card de controles atualizado
controls = dbc.Card(
    [
        html.Div(
            [
                html.H4("Filtros", style=TITLE_STYLE),
                dbc.Label("Intervalo de Anos", style={'fontWeight': '500'}),
                dcc.Dropdown(
                    id='intervalo-dropdown',
                    options=[
                        {'label': '5 anos', 'value': '5'},
                        {'label': '10 anos', 'value': '10'},
                        {'label': 'Todos os anos', 'value': 'all'}
                    ],
                    value='10',
                    clearable=False,
                    style=DROPDOWN_STYLE
                ),
                dbc.Label("Ano", style={'fontWeight': '500', 'marginTop': '10px'}),
                dcc.Dropdown(
                    id='ano-dropdown',
                    options=[],
                    value=None,
                    clearable=False,
                    style=DROPDOWN_STYLE
                ),
            ]
        ),
    ],
    body=True,
    style=CARD_STYLE
)

# Coordenadas de Paragominas
lat = -3.0551
lon = -47.3497

# Criando um mapa com Plotly
mapa_paragominas = px.scatter_mapbox(
    lat=[lat], 
    lon=[lon], 
    hover_name=["Paragominas"],
    color=["Paragominas"], 
    size=[10],  # Tamanho do marcador
    title="Localização de Paragominas - PA",  # Título do mapa
)

# Atualizando o layout do mapa
mapa_paragominas.update_layout(
    mapbox_style="open-street-map",  # Estilo do mapa
    mapbox_zoom=6,  # Zoom ajustado para abrir mais a área
    mapbox_center={"lat": lat, "lon": lon},  # Centraliza Paragominas
    showlegend=False,  # Remover legenda
    margin={"r":0,"t":40,"l":0,"b":0}  # Remover margens do gráfico
)


app.layout = dbc.Container(
    [
        html.Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
    ),

        # Banner (Logo no topo)
        # Navbar com título
        dbc.Navbar(
            dbc.Container(
                [
                    dbc.Row(
                        dbc.Col(
                            html.H1("VARIABILIDADE DA SECA NA REGIÃO DE PARAGOMINAS", 
                                    style={
                                        'color': '#FFFFFF',  # Cor do título na navbar
                                        'fontWeight': '600',  # Negrito
                                        'fontSize': '24px',  # Tamanho da fonte
                                    }),
                        ),
                        align="center",  # Centraliza o conteúdo
                    ),
                ]
            ),
            color="primary",  # Cor de fundo da navbar (pode ser 'primary', 'secondary', etc.)
            dark=True,  # Para garantir que o texto fique visível (fundo escuro e texto claro)
            style={'marginBottom': '30px'},  # Adiciona margem inferior para descolar a navbar
        ),
        
        # Layout com duas colunas principais (esquerda para controles, direita para gráficos)
        dbc.Row(
            [
                # Coluna para os controles
                dbc.Col(
                    [
                        controls,
                         html.H3(
                            "Dashboard SPEI", 
                            style={
                                'fontWeight': '600',  # Negrito
                                'fontSize': '24px',  # Tamanho maior
                                'marginBottom': '15px',  # Espaço abaixo do título
                                'color': '#007bff',  # Cor azul para o título
                            }
                        ),
                        # Descrição do produto
                        html.P(
                            "Este produto apresenta os resultados de uma análise da variabilidade climática no município de Paragominas, no estado do Pará, Brasil, entre 1981 e 2022. O foco está na avaliação do índice SPEI (Standardized Precipitation Evapotranspiration Index).",
                            style={'fontSize': '16px', 'lineHeight': '1.6', 'color': '#555555'}
                        ),
                        dcc.Graph(
                            id="mapa-paragominas",
                            figure=mapa_paragominas,
                            config={"responsive": True},
                        ),
                    ],  # Coloque o controle aqui novamente se precisar, ou defina conforme o layout desejado
                    md=3,  # A coluna de configurações ocupa 3 das 12 colunas do grid
                    style={'backgroundColor': '#FFFFFF', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}
                ),
                
                # Coluna para os gráficos (com vários gráficos empilhados verticalmente)
                dbc.Col(
                    [
                        # Card de "Análise SPEI"
                        dbc.Card(
                            [
                                dbc.CardHeader("Análise SPEI", style={'backgroundColor': '#F8F9FA', 'fontWeight': '600'}),
                                dcc.Graph(id="spei-graph", config={'responsive': True}, style={'width': '100%', 'height': '400px'}),
                            ],
                            className="card-shadow",
                            style={'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'marginBottom': '20px'}  # Adicionando margem inferior
                        ),
                        # Card de "Distribuição de Categorias"
                        dbc.Card(
                            [
                                dbc.CardHeader("Distribuição de Categorias", style={'backgroundColor': '#F8F9FA', 'fontWeight': '600'}),
                                dcc.Graph(id="barras-empilhadas-graph", config={'responsive': True}, style={'width': '100%', 'height': '400px'}),
                            ],
                            className="card-shadow",
                            style={'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'marginBottom': '20px'}  # Adicionando margem inferior
                        ),
                        # Card de "Média Mensal"
                        dbc.Card(
                            [
                                dbc.CardHeader("Média Mensal", style={'backgroundColor': '#F8F9FA', 'fontWeight': '600'}),
                                dcc.Graph(id="media-mensal-graph", config={'responsive': True}, style={'width': '100%', 'height': '400px'}),
                            ],
                            className="card-shadow",
                            style={'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'marginBottom': '20px'}  # Adicionando margem inferior
                        ),
                        # Card de "Histograma de SPEI"
                        dbc.Card(
                            [
                                dbc.CardHeader("Histograma de SPEI", style={'backgroundColor': '#F8F9FA', 'fontWeight': '600'}),
                                dcc.Graph(id="histograma-graph", config={'responsive': True}, style={'width': '100%', 'height': '400px'}),
                            ],
                            className="card-shadow",
                            style={'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'marginBottom': '20px'}  # Adicionando margem inferior
                        ),
                        # Card de "Dispersão SPEI"
                        dbc.Card(
                            [
                                dbc.CardHeader("Dispersão SPEI", style={'backgroundColor': '#F8F9FA', 'fontWeight': '600'}),
                                dcc.Graph(id="scatter-graph", config={'responsive': True}, style={'width': '100%', 'height': '400px'}),
                            ],
                            className="card-shadow",
                            style={'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'marginBottom': '20px'}  # Adicionando margem inferior
                        ),
                        # Card de "Boxplot SPEI por Ano"
                        dbc.Card(
                            [
                                dbc.CardHeader("Boxplot SPEI por Ano", style={'backgroundColor': '#F8F9FA', 'fontWeight': '600'}),
                                dcc.Graph(id="boxplot-graph", config={'responsive': True}, style={'width': '100%', 'height': '400px'}),
                            ],
                            className="card-shadow",
                            style={'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'marginBottom': '20px'}  # Adicionando margem inferior
                        ),
                    ],
                    md=9,  # A coluna de gráficos ocupa 9 das 12 colunas do grid
                ),
            ],
            align="start",
            style={'marginBottom': '20px'},
        ),
        
        # Add the footer at the bottom
        footer
    ],
    fluid=True,  # Para que o layout seja fluido e ocupe toda a largura da tela
    style={'backgroundColor': '#F4F6F7'}  # Fundo levemente acinzentado
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

    font_style = dict(family='Arial, sans-serif', size=12, color='black')

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

    # Dicionário de cores atualizado
    cores_categorias = {
        'Umidade extrema': '#1e3a8a',
        'Umidade severa': '#1d4ed8',
        'Umidade moderada': '#0ea5e9',
        'Umidade fraca': '#93c5fd',
        'Seca fraca': '#fca5a5',
        'Seca moderada': '#ef4444',
        'Seca severa': '#b91c1c',
        'Seca extrema': '#7f1d1d',
    }

    # Gráfico de barras empilhadas atualizado
    barras_figure = {
        'data': [
            go.Bar(
                x=dados_ano.index,
                y=dados_ano.get(categoria, pd.Series([0] * len(dados_ano.index))),
                name=categoria,
                marker=dict(color=cores_categorias[categoria])  # Usando as cores atualizadas
            ) for categoria in [
                'Umidade extrema',
                'Umidade severa',
                'Umidade moderada',
                'Umidade fraca',
                'Seca fraca',
                'Seca moderada',
                'Seca severa',
                'Seca extrema',             
            ]
        ],
        'layout': go.Layout(
            barmode='stack',
            xaxis={
                'title': 'Ano',
                'title_font': dict(color='black', size=12),
                'tickfont': dict(color='black', size=12),
                'showgrid': True,
                'gridcolor': 'lightgrey',
            },
            yaxis={
                'title': 'Porcentagem',
                'title_font': dict(color='black', size=12),
                'tickfont': dict(color='black', size=12),
                'showgrid': True,
                'gridcolor': 'lightgrey',
            },
            plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
            paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
            font=dict(color='black', size=12),  # Tamanho da fonte
            legend=dict(traceorder='normal', font=dict(size=12)),  # Tamanho da fonte da legenda
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
            'title_font': dict(color='black', size=12),
            'tickfont': dict(color='black', size=12),
            'showgrid': True,
            'gridcolor': 'lightgrey',  # Cor da grade
        },
        yaxis={
            'title': 'SPEI',
            'title_font': dict(color='black', size=12),
            'tickfont': dict(color='black', size=12),
            'showgrid': True,
            'gridcolor': 'lightgrey',
        },
        plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
        paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
        font=dict(color='black', size=12),  # Tamanho da fonte
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
                'title_font': dict(color='black', size=12),
                'tickfont': dict(color='black', size=12),
                'showgrid': True,
                'gridcolor': 'lightgrey',  # Cor da grade
            },
            yaxis={
                'title': 'Frequência',
                'title_font': dict(color='black', size=12),
                'tickfont': dict(color='black', size=12),
                'showgrid': True,
                'gridcolor': 'lightgrey',
            },
            plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
            paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
            font=dict(color='black', size=12),  # Tamanho da fonte
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
            'title_font': dict(color='black', size=12),  # Tamanho da fonte do título
            'tickfont': dict(color='black', size=12),
            'showgrid': True,
            'gridcolor': 'lightgrey'  # Cor da grade
        },
        yaxis={
            'title': 'SPEI',
            'range': [-3, 3],
            'title_font': dict(color='black', size=12),  # Tamanho da fonte do título
            'tickfont': dict(color='black', size=12),
            'showgrid': True,
            'gridcolor': 'lightgrey'  # Cor da grade
        },
        plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
        paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
        margin=dict(t=20, l=40, r=25, b=40),  # Margens
        font=dict(color='black', size=12)  # Tamanho da fonte
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
                'title_font': dict(color='black', size=12),  # Tamanho da fonte do título
                'tickfont': dict(color='black', size=12),
                'showgrid': True,
                'gridcolor': 'lightgrey'  # Cor da grade
            },
            xaxis={
                'title': 'Ano',
                'title_font': dict(color='black', size=12),  # Tamanho da fonte do título
                'tickfont': dict(color='black', size=12),
                'showgrid': True,
                'gridcolor': 'lightgrey'  # Cor da grade
            },
            plot_bgcolor='rgba(255, 255, 255, 1)',  # Fundo do gráfico
            paper_bgcolor='rgba(255, 255, 255, 1)',  # Fundo da área do gráfico
            margin=dict(t=30, l=40, r=25, b=40),  # Margens
            font=dict(color='black', size=12)  # Tamanho da fonte
        )
    }

    return linha_figure, barras_figure, media_mensal_figure, histograma_figure, scatter_figure, boxplot_figure 

if __name__ == "__main__":
    app.run_server(debug=True, host='127.0.0.1', port=int(os.environ.get('PORT', 8050)))
