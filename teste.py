import spei as si
import pandas as pd
import scipy.stats as scs
from scipy.stats import fisk, norm
import matplotlib.pyplot as plt
# import numpy as np

file_path_etp = 'dados/ETP_HARVREAVES_TERRACLIMATE.xlsx'
file_path_prp = 'dados/PRP_TERRACLIMATE.xlsx'

def extrair_dados(path_etp, path_prp, acumulado=1):
    # Leitura dos dados de evapotranspiração potencial (ETP)
    df_etp = pd.read_excel(path_etp)
    df_etp = df_etp.rename(columns={'Hargreaves Potential Evapotranspiration (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_etp = df_etp.iloc[1:].reset_index(drop=True)

    # Leitura dos dados de precipitação (PRP)
    df_prp = pd.read_excel(file_path_prp)
    df_prp = df_prp.rename(columns={'Precipitation (TerraClimate)': 'data', 'Unnamed: 1': 'dados'})
    df_prp = df_prp.iloc[1:].reset_index(drop=True)

    # Mesclando os dados
    df_merged = pd.merge(df_etp, df_prp, on='data', suffixes=('_etp', '_prp'))

    # Calculando o balanço hídrico
    df_merged['balanco_hidrico'] = df_merged['dados_prp'] - df_merged['dados_etp']
    df_merged['data'] = pd.to_datetime(df_merged['data'], format='%Y-%m-%d')

    # Criando o DataFrame com os dados do balanço hídrico
    df = pd.DataFrame({'data': df_merged['data'], 'dados': df_merged['balanco_hidrico']})

    df.set_index('data', inplace = True)

    return df

dados = extrair_dados(file_path_etp, file_path_prp)

spei_modelado = si.spei(pd.Series(dados['dados']))

teste = pd.DataFrame({'data': spei_modelado.index, 'values': spei_modelado.values})
print(teste)
