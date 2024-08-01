import pandas as pd

file_path = 'dados/ETP_HARVREAVES_TERRACLIMATE.xlsx'
df = pd.read_excel(file_path)
df = df.rename(columns={'Hargreaves Potential Evapotranspiration (TerraClimate)':'date', 'Unnamed: 1': 'value'})

df = df.iloc[1:].reset_index(drop=True)
df
