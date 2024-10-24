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
        options=[{'label': f'{ano} a {ano + 10}', 'value': f'{ano}-{ano + 9}'} for ano in range(1981, 2012, 10)] +
                 [{'label': '2021 a 2022', 'value': '2021-2022'}],
        value='1981-1990',  # Valor padrão
        clearable=False
    ),

    dcc.Graph(id='spei-1-graph'),
    dcc.Graph(id='boxplot-graph'),
    dcc.Graph(id='barras-graph'),
    dcc.Graph(id='heatmap-graph'),
    dcc.Graph(id='anomalia-graph'),  # Gráfico de anomalias
    dcc.Graph(id='tendencia-graph'),  # Novo gráfico para tendência
    dcc.Graph(id='bar-graph')  # Gráfico de barras para ETP e Precipitação
])

# Callback para atualizar os gráficos
@app.callback(
    [Output('spei-1-graph', 'figure'),
     Output('boxplot-graph', 'figure'),
     Output('barras-graph', 'figure'),
     Output('heatmap-graph', 'figure'),
     Output('anomalia-graph', 'figure'),
     Output('tendencia-graph', 'figure'),
     Output('bar-graph', 'figure')],  # Gráfico de barras
    Input('ano-dropdown', 'value')
)
def atualizar_graficos(intervalo):
    ano_inicial, ano_final = map(int, intervalo.split('-'))
    
    # Filtrando SPEI
    spei_filtrado = filtrarPorAno(spei_1, ano_inicial, ano_final)
    
    # Filtrando ETP e Precipitação
    df_etp_prp_filtrado = df_etp_prp[(df_etp_prp.index.year >= ano_inicial) & (df_etp_prp.index.year <= ano_final)]

    # Gráfico de linha SPEI
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
            xaxis={'title': 'Data', 'range': [spei_filtrado.index.min() - pd.DateOffset(months=1), spei_filtrado.index.max() + pd.DateOffset(months=1)]},
            yaxis={'title': 'SPEI', 'range': [-3, 3]},
            hovermode='closest'
        )
    }

    # Gráfico de barras para ETP e Precipitação
    bar_figure = {
        'data': [
            go.Bar(
                x=df_etp_prp_filtrado.index,
                y=df_etp_prp_filtrado['ETP'],
                name='Evapotranspiração (ETP)',
                marker=dict(color='blue')
            ),
            go.Bar(
                x=df_etp_prp_filtrado.index,
                y=df_etp_prp_filtrado['Precipitação'],
                name='Precipitação',
                marker=dict(color='green')
            )
        ],
        'layout': go.Layout(
            title='ETP e Precipitação por Período',
            xaxis={'title': 'Data'},
            yaxis={'title': 'Valor'},
            barmode='group',  # Agrupando barras
            hovermode='closest'
        )
    }

    # Gráfico de boxplot por ano
    anos = range(ano_inicial, ano_final + 1)
    boxplot_data = []
    for ano in anos:
        dados_ano = spei_filtrado[spei_filtrado.index.year == ano]
        boxplot_data.append(go.Box(y=dados_ano.values, name=str(ano), boxmean='sd'))

    boxplot_figure = {
        'data': boxplot_data,
        'layout': go.Layout(
            title=f'Boxplot de SPEI de {ano_inicial} a {ano_final}',
            yaxis={'title': 'SPEI', 'range': [-3, 3]}
        )
    }

    # Gráfico de barras acumuladas por ano
    totais_por_ano = spei_filtrado.resample('Y').sum()
    barras_figure = {
        'data': [
            go.Bar(
                x=totais_por_ano.index.year,
                y=totais_por_ano.values,
                name='Total SPEI Acumulado'
            )
        ],
        'layout': go.Layout(
            title='Total de SPEI Acumulado por Ano',
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Total SPEI'}
        )
    }

    # Gráfico de calor (heatmap) de SPEI por mês e ano
    heatmap_data = spei_1.resample('M').mean().reset_index()
    heatmap_data['year'] = heatmap_data['data'].dt.year
    heatmap_data['month'] = heatmap_data['data'].dt.month
    heatmap_data['dados'] = heatmap_data[0]  # Ajuste se necessário

    heatmap_matrix = heatmap_data.pivot_table(index='month', columns='year', values='dados')

    heatmap_figure = {
        'data': [
            go.Heatmap(
                z=heatmap_matrix.values,
                x=heatmap_matrix.columns,
                y=heatmap_matrix.index,
                colorscale='Viridis'
            )
        ],
        'layout': go.Layout(
            title='Heatmap de SPEI por Mês e Ano',
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Mês', 'tickvals': list(range(1, 13)), 'ticktext': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
        )
    }

    # Gráfico de anomalia
    media_historica = spei_1.mean()
    anomalias = spei_1 - media_historica  # Calcula as anomalias
    anomalia_figure = {
        'data': [
            go.Scatter(
                x=anomalias.index,
                y=anomalias.values,
                mode='lines',
                name='Anomalias de SPEI',
                line=dict(color='orange')
            )
        ],
        'layout': go.Layout(
            title='Anomalias de SPEI ao longo do tempo',
            xaxis={'title': 'Data'},
            yaxis={'title': 'Anomalia SPEI'},
            hovermode='closest'
        )
    }

    # Gráfico de linha com tendência
    media_movel = spei_1.rolling(window=12).mean()  # Média móvel de 12 meses
    tendencia_figure = {
        'data': [
            go.Scatter(
                x=spei_1.index,
                y=spei_1.values,
                mode='lines',
                name='SPEI'
            ),
            go.Scatter(
                x=media_movel.index,
                y=media_movel.values,
                mode='lines',
                name='Tendência (Média Móvel)',
                line=dict(color='red', dash='dash')
            )
        ],
        'layout': go.Layout(
            title='Evolução do SPEI com Tendência',
            xaxis={'title': 'Data'},
            yaxis={'title': 'SPEI'},
            hovermode='closest'
        )
    }

    return linha_figure, boxplot_figure, barras_figure, heatmap_figure, anomalia_figure, tendencia_figure, bar_figure

# Executa o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
