from pathlib import Path
import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)  # Exibir todas as colunas
pd.set_option('display.max_rows', None)     # Exibir todas as linhas
pd.set_option('display.width', None)

def get_resources(file_path="Input Data - Resources 1.xlsx"):

    data = pd.read_excel(file_path, sheet_name=None)
    resources = {}
    # Definir quais abas têm o mesmo formato
    similar_sheets = ["Electrical load", "Gas load", "Heat load"]
    # Processar as abas que têm a mesma estrutura
    for sheet_name in similar_sheets:
        if sheet_name in data:
            df = data[sheet_name]

            # Remover a primeira coluna vazia (se existir)
            if df.iloc[:, 0].isna().all():
                df = df.iloc[:, 1:]

            # Definir os nomes das colunas
            df.columns = ["Load/Building/Resource"] + list(range(1, 25))

            # Remover a primeira linha se estiver repetindo os cabeçalhos
            if df.iloc[0, 0] == "Load/Building/Resource":
                df = df.iloc[1:]

            # Definir o índice corretamente
            df = df.set_index("Load/Building/Resource")

            # Converter os valores para float
            df = df.apply(pd.to_numeric, errors='coerce')

            # Salvar no dicionário
            resources[sheet_name] = df.to_dict(orient="index")

    # if "Thermal Resources Params" in data:
    #     df = data["Thermal Resources Params"].dropna(how="all")  # Remove linhas vazias
    #
    #     # Preencher os valores NaN na coluna "Resources" com o último valor válido (tratar células mescladas)
    #     df.iloc[:, 0] = df.iloc[:, 0].ffill()
    #     thermal_resources = {}
    #
    #     for _, row in df.iterrows():
    #         resource = row.iloc[0]  # Primeira coluna (Resource) -> Categoria principal (HP, CHP, etc.)
    #         parameter = row.iloc[1]  # Segunda coluna (Parameter) -> Nome do parâmetro
    #         value = row.iloc[2]  # Terceira coluna (Value) -> Valor numérico
    #
    #         # Adiciona ao dicionário estruturado
    #         if resource not in thermal_resources:
    #             thermal_resources[resource] = {}
    #
    #         thermal_resources[resource][parameter] = value
    #
    #     resources["Thermal Resources Params"] = thermal_resources
    #
    #
        # Processar as outras abas individualmente
    for sheet_name in data.keys():
        if sheet_name not in similar_sheets and sheet_name != "Thermal Resources Params":
            resources[sheet_name] = data[sheet_name]





    return resources

def load_resources_params(m, data):
    # Verificar se a aba "buildings, resources" existe nos dados
    if "buildings, resources" in data:  # Nome da aba em minúsculas
        df = data["buildings, resources"].dropna(how="all")  # Remove linhas vazias

        # Verificar se a primeira linha contém os cabeçalhos corretos
        if df.iloc[0, 0] == "Load/Building/Resource":
            df.columns = df.iloc[0]  # Definir a primeira linha como cabeçalho
            df = df.iloc[1:]  # Remover a primeira linha agora que é cabeçalho

        # Preencher células mescladas na primeira coluna
        df.iloc[:, 0] = df.iloc[:, 0].ffill()

        # Renomear colunas
        df.columns = ["Resource", "Parameter"] + list(df.columns[2:])

        # Verificar se as colunas dos edifícios são numéricas
        building_columns = df.columns[2:]  # Colunas dos edifícios
        try:
            building_columns = [int(col) for col in building_columns]  # Converter para inteiros
        except ValueError as e:
            print(f"Erro ao converter colunas para inteiros: {e}")
            print("Colunas dos edifícios:", df.columns[2:])
            return data

        # Criar um dicionário estruturado para os dados de todos os recursos
        all_resources_data = {}

        # Lista dos recursos a serem processados (nomes exatos)
        resources = [
            "Electric vehicle",  # Nome exato
            "Hydrogen Storage",  # Nome exato
            "PV",
            "Storage",
            "Electrolyzer P2G",
            "Fuel Cell",
            "Wind Turbine",
            "Biomass Boiler",
            "Heat Pump",
            "CHP",
            "District Heating",
        ]

        # Processar as linhas da planilha para organizar os dados dos recursos
        for _, row in df.iterrows():
            resource = row["Resource"]  # Nome do recurso
            if pd.isna(resource):  # Se for nan, ignorar esta linha
                continue
            parameter = row["Parameter"]  # Nome do parâmetro
            values = row.iloc[2:].to_dict()  # Dicionário {building: value}

            # Verificar se o recurso está na lista de recursos e adicionar ao dicionário
            if resource in resources:
                if resource not in all_resources_data:
                    all_resources_data[resource] = {}

                all_resources_data[resource][parameter] = values

        # Adicionar os dados de todos os recursos ao dicionário principal
        for resource, data_dict in all_resources_data.items():
            data[resource] = data_dict

        for resource in resources:
            if resource in data:
                print(f"\nDados do recurso: {resource}")
                resource_data = data[resource]

                # Criar um DataFrame para o recurso atual
                df = pd.DataFrame(resource_data)

                # Transpor o DataFrame para que os edifícios sejam colunas
                df = df.transpose()

                # Renomear as colunas para "Parâmetro" e os edifícios
                df.index.name = "Parâmetro"
                df.columns.name = "Edifício"

                # Imprimir o DataFrame formatado
                print(df)
            else:
                print(f"\nRecurso '{resource}' não encontrado nos dados.")

    return data


def Buildings_max_temp(m, data):
    sheet_name = "Buildings - Max temperature"

    # Verificar se a aba existe no dicionário
    if sheet_name not in data:
        print(f"Aba '{sheet_name}' não encontrada no dicionário de dados.")
        return data

    # Carregar o DataFrame e remover linhas totalmente vazias
    df = data[sheet_name].dropna(how="all")

    # ───────────── Ajustes de cabeçalho ─────────────
    # 1) Vamos assumir que a primeira linha útil do DataFrame (df.iloc[0]) contém
    #    os nomes das colunas, incluindo "Load/Building/Resource" e os IDs dos edifícios.
    df.columns = df.iloc[0]  # Define a linha 0 como cabeçalho
    df = df.iloc[1:]  # Remove a linha de cabeçalho que acabamos de usar

    # 2) Remover colunas completamente vazias, se houver
    df = df.dropna(axis=1, how="all")

    # 3) Agora renomear a primeira coluna para "Load/Building/Resource"
    #    e as demais colunas (que devem ser 1, 2, 3, ..., 39) para inteiros.
    colunas_originais = list(df.columns)
    # Exemplo: colunas_originais pode ser algo como [NaN, 1, 2, 3, ..., 39]
    # ou ["Load/Building/Resource", 1, 2, 3, ..., 39].
    # Precisamos garantir que a primeira seja "Load/Building/Resource" e as demais sejam int.
    novas_colunas = ["Load/Building/Resource"]

    # Para as colunas restantes, convertemos para int, se possível
    for c in colunas_originais[1:]:
        try:
            novas_colunas.append(int(c))
        except ValueError:
            # Se não conseguir converter para int, você pode decidir o que fazer
            # Ex.: deixar como string ou descartar. Aqui, deixamos como string mesmo.
            novas_colunas.append(str(c))

    df.columns = novas_colunas

    # 4) Se a primeira linha do DataFrame duplicar o cabeçalho, removemos
    #    (às vezes ocorre quando a planilha tem cabeçalho repetido).
    #    Verifica se a primeira célula é "Load/Building/Resource".
    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    # 5) Definir "Load/Building/Resource" como índice
    df = df.set_index("Load/Building/Resource")

    # 6) Converter todos os valores para float (ou int), ignorando erros
    df = df.apply(pd.to_numeric, errors="coerce")

    # ───────────── Salvar no dicionário data ─────────────
    # Se quiser guardar como DataFrame:
    # data["inside_max_temp_df"] = df

    # Se quiser guardar como dicionário aninhado (cada linha vira chave, etc.):
    data["inside_max_temp"] = df.to_dict(orient="index")

    # df_print = pd.DataFrame.from_dict(data["inside_max_temp"], orient="index")
    #
    # print("\n--- Dados da aba 'Buildings - Max temperature' ---")
    # print(df_print)
    # print("--- Fim dos dados ---\n")
    return data


def Buildings_min_temp(m,data):
    sheet_name = "Buildings - Min temperature"

    # Verificar se a aba existe no dicionário
    if sheet_name not in data:
        print(f"Aba '{sheet_name}' não encontrada no dicionário de dados.")
        return data

    # Carregar o DataFrame e remover linhas totalmente vazias
    df = data[sheet_name].dropna(how="all")

    # ───────────── Ajustes de cabeçalho ─────────────
    # 1) Vamos assumir que a primeira linha útil do DataFrame (df.iloc[0]) contém
    #    os nomes das colunas, incluindo "Load/Building/Resource" e os IDs dos edifícios.
    df.columns = df.iloc[0]  # Define a linha 0 como cabeçalho
    df = df.iloc[1:]  # Remove a linha de cabeçalho que acabamos de usar

    # 2) Remover colunas completamente vazias, se houver
    df = df.dropna(axis=1, how="all")

    # 3) Agora renomear a primeira coluna para "Load/Building/Resource"
    #    e as demais colunas (que devem ser 1, 2, 3, ..., 39) para inteiros.
    colunas_originais = list(df.columns)
    # Exemplo: colunas_originais pode ser algo como [NaN, 1, 2, 3, ..., 39]
    # ou ["Load/Building/Resource", 1, 2, 3, ..., 39].
    # Precisamos garantir que a primeira seja "Load/Building/Resource" e as demais sejam int.
    novas_colunas = ["Load/Building/Resource"]

    # Para as colunas restantes, convertemos para int, se possível
    for c in colunas_originais[1:]:
        try:
            novas_colunas.append(int(c))
        except ValueError:
            # Se não conseguir converter para int, você pode decidir o que fazer
            # Ex.: deixar como string ou descartar. Aqui, deixamos como string mesmo.
            novas_colunas.append(str(c))

    df.columns = novas_colunas

    # 4) Se a primeira linha do DataFrame duplicar o cabeçalho, removemos
    #    (às vezes ocorre quando a planilha tem cabeçalho repetido).
    #    Verifica se a primeira célula é "Load/Building/Resource".
    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    # 5) Definir "Load/Building/Resource" como índice
    df = df.set_index("Load/Building/Resource")

    # 6) Converter todos os valores para float (ou int), ignorando erros
    df = df.apply(pd.to_numeric, errors="coerce")

    # ───────────── Salvar no dicionário data ─────────────
    # Se quiser guardar como DataFrame:
    # data["inside_min_temp_df"] = df

    # Se quiser guardar como dicionário aninhado (cada linha vira chave, etc.):
    data["inside_min_temp"] = df.to_dict(orient="index")

    df_print = pd.DataFrame.from_dict(data["inside_min_temp"], orient="index")

    # Exemplo: Imprimir as temperaturas para o Edifício 1
    # edificio = 15  # Altere o número do edifício conforme necessário
    #
    # print(f"Temperaturas para o Edifício {edificio}:")
    # for hora in range(1, 25):  # Horas de 1 a 24
    #     print(f"Hora {hora}: {data['inside_min_temp'][edificio][hora]}")

    # print("\n--- Dados da aba 'Buildings - Min temperature' ---")
    # print(df_print)
    # print("--- Fim dos dados ---\n")
    return data



def Outside_temp(m, data):
    sheet_name = "Outside_temperature"

    # Verificar se a aba existe no dicionário
    if sheet_name not in data:
        print(f"Aba '{sheet_name}' não encontrada no dicionário de dados.")
        return data

    # Carregar o DataFrame e remover linhas totalmente vazias
    df = data[sheet_name].dropna(how="all")

    # ───────────── Ajustes de cabeçalho ─────────────
    # 1) Vamos assumir que a primeira linha útil do DataFrame (df.iloc[0]) contém
    #    os nomes das colunas, incluindo "Load/Building/Resource" e os IDs dos edifícios.
    df.columns = df.iloc[0]  # Define a linha 0 como cabeçalho
    df = df.iloc[1:]  # Remove a linha de cabeçalho que acabamos de usar

    # 2) Remover colunas completamente vazias, se houver
    df = df.dropna(axis=1, how="all")

    # 3) Agora renomear a primeira coluna para "Load/Building/Resource"
    #    e as demais colunas (que devem ser 1, 2, 3, ..., 39) para inteiros.
    colunas_originais = list(df.columns)
    # Exemplo: colunas_originais pode ser algo como [NaN, 1, 2, 3, ..., 39]
    # ou ["Load/Building/Resource", 1, 2, 3, ..., 39].
    # Precisamos garantir que a primeira seja "Load/Building/Resource" e as demais sejam int.
    novas_colunas = ["Load/Building/Resource"]

    # Para as colunas restantes, convertemos para int, se possível
    for c in colunas_originais[1:]:
        try:
            novas_colunas.append(int(c))
        except ValueError:
            # Se não conseguir converter para int, você pode decidir o que fazer
            # Ex.: deixar como string ou descartar. Aqui, deixamos como string mesmo.
            novas_colunas.append(str(c))

    df.columns = novas_colunas

    # 4) Se a primeira linha do DataFrame duplicar o cabeçalho, removemos
    #    (às vezes ocorre quando a planilha tem cabeçalho repetido).
    #    Verifica se a primeira célula é "Load/Building/Resource".
    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    # 5) Definir "Load/Building/Resource" como índice
    df = df.set_index("Load/Building/Resource")

    # 6) Converter todos os valores para float (ou int), ignorando erros
    df = df.apply(pd.to_numeric, errors="coerce")

    # ───────────── Salvar no dicionário data ─────────────
    # Se quiser guardar como DataFrame:
    # data["outside_temp_df"] = df

    # Se quiser guardar como dicionário aninhado (cada linha vira chave, etc.):
    data["outside_temp"] = df.to_dict(orient="index")

    # df_print = pd.DataFrame.from_dict(data["outside_temp"], orient="index")
    #
    # print("\n--- Dados da aba 'Outside_temperature' ---")
    # print(df_print)
    # print("--- Fim dos dados ---\n")
    return data


def Heat_Gains_losses(m,data):
    sheet_name = "Heat_Gains_Losses"

    # Verificar se a aba existe no dicionário
    if sheet_name not in data:
        print(f"Aba '{sheet_name}' não encontrada no dicionário de dados.")
        return data

    # Carregar o DataFrame e remover linhas totalmente vazias
    df = data[sheet_name].dropna(how="all")

    # ───────────── Ajustes de cabeçalho ─────────────
    # 1) Vamos assumir que a primeira linha útil do DataFrame (df.iloc[0]) contém
    #    os nomes das colunas, incluindo "Load/Building/Resource" e os IDs dos edifícios.
    df.columns = df.iloc[0]  # Define a linha 0 como cabeçalho
    df = df.iloc[1:]  # Remove a linha de cabeçalho que acabamos de usar

    # 2) Remover colunas completamente vazias, se houver
    df = df.dropna(axis=1, how="all")

    # 3) Agora renomear a primeira coluna para "Load/Building/Resource"
    #    e as demais colunas (que devem ser 1, 2, 3, ..., 39) para inteiros.
    colunas_originais = list(df.columns)
    # Exemplo: colunas_originais pode ser algo como [NaN, 1, 2, 3, ..., 39]
    # ou ["Load/Building/Resource", 1, 2, 3, ..., 39].
    # Precisamos garantir que a primeira seja "Load/Building/Resource" e as demais sejam int.
    novas_colunas = ["Load/Building/Resource"]

    # Para as colunas restantes, convertemos para int, se possível
    for c in colunas_originais[1:]:
        try:
            novas_colunas.append(int(c))
        except ValueError:
            # Se não conseguir converter para int, você pode decidir o que fazer
            # Ex.: deixar como string ou descartar. Aqui, deixamos como string mesmo.
            novas_colunas.append(str(c))

    df.columns = novas_colunas

    # 4) Se a primeira linha do DataFrame duplicar o cabeçalho, removemos
    #    (às vezes ocorre quando a planilha tem cabeçalho repetido).
    #    Verifica se a primeira célula é "Load/Building/Resource".
    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    # 5) Definir "Load/Building/Resource" como índice
    df = df.set_index("Load/Building/Resource")

    # 6) Converter todos os valores para float (ou int), ignorando erros
    df = df.apply(pd.to_numeric, errors="coerce")

    # ───────────── Salvar no dicionário data ─────────────
    # Se quiser guardar como DataFrame:
    # data["loss_temp_df"] = df

    # Se quiser guardar como dicionário aninhado (cada linha vira chave, etc.):
    data["loss_temp"] = df.to_dict(orient="index")

    df_print = pd.DataFrame.from_dict(data["loss_temp"], orient="index")

    # print("\n--- Dados da aba 'Heat_Gains_Losses' ---")
    # print(df_print)
    # print("--- Fim dos dados ---\n")
    return data


def Weather_forecasts(m, data):
    # Caminho do arquivo fixo dentro da função
    file_path = "Input Data - Other.xlsx"

    # Carregar o arquivo Excel
    df = pd.read_excel(file_path, sheet_name="Weather forecasts")



    # A primeira linha contém as "Hours", então pegamos essas colunas
    hours = df.columns[1:].values  # Extrai as horas (primeira linha sem o índice da coluna)

    # Agora, pegamos as linhas para as variáveis solares, velocidade do vento e temperatura externa
    solar_profile = df.iloc[0, 1:].apply(pd.to_numeric, errors='coerce').values
    wind_speed = df.iloc[1, 1:].apply(pd.to_numeric, errors='coerce').values


    # Organizando os dados em um dicionário
    weather_data = {
        "hours": hours,  # As horas
        "solar_profile": solar_profile,  # Perfil solar
        "wind_speed": wind_speed,  # Velocidade do vento

    }

    # Adicionar os dados processados ao dicionário de dados
    data["weather_forecasts"] = weather_data

    # print("\n--- Dados de Weather Forecasts ---")
    #
    # # Dados solares
    # solar_data = data["weather_forecasts"]["solar_profile"]
    # print("\nPerfil Solar para as 24 horas:")
    # for h in range(1, 25):
    #     print(f"Hora {h}: {solar_data[h - 1]}")
    #
    # # Dados de velocidade do vento
    # wind_data = data["weather_forecasts"]["wind_speed"]
    # print("\nVelocidade do Vento para as 24 horas:")
    # for h in range(1, 25):
    #     print(f"Hora {h}: {wind_data[h - 1]}")
    #
    # print("\n--- Fim dos dados ---")

    return data


def process_prices(m, data):
    file_path = "Input Data - Other.xlsx"  # Caminho correto do arquivo
    sheet_name = "Prices"  # Nome exato da aba

    # Ler a planilha, garantindo que o primeiro cabeçalho seja tratado corretamente
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Definir a primeira coluna como índice corretamente
    df = df.set_index(df.columns[0])

    # Renomear o índice para "Parameters" para evitar problemas
    df.index.name = "Parameters"

    # Converter valores para float (evitar erros de formatação)
    df = df.apply(pd.to_numeric, errors="coerce")

    # Salvar os preços no dicionário `data`
    data["prices"] = df.to_dict(orient="index")

    # # Impressão correta, garantindo que o índice apareça como "Parameters"
    # print("\n--- Dados da aba 'Prices' ---")
    # print(df.to_string(index=True))
    # print("--- Fim dos dados ---\n")

    return data

