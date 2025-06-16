from pathlib import Path
import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)  # Display all columns
pd.set_option('display.max_rows', None)     # Display all rows
pd.set_option('display.width', None)

def get_resources(file_path="Input Data - Resources 1.xlsx"):

    data = pd.read_excel(file_path, sheet_name=None)
    resources = {}
    # Define which sheets have the same format
    similar_sheets = ["Electrical load", "Gas load", "Heat load"]
    # Process the sheets with the same structure
    for sheet_name in similar_sheets:
        if sheet_name in data:
            df = data[sheet_name]

            # Remove the first empty column (if it exists)
            if df.iloc[:, 0].isna().all():
                df = df.iloc[:, 1:]

            # Define the column names
            df.columns = ["Load/Building/Resource"] + list(range(1, 25))

            # Remove the first row if it is repeating the headers
            if df.iloc[0, 0] == "Load/Building/Resource":
                df = df.iloc[1:]

            # Set the index correctly
            df = df.set_index("Load/Building/Resource")

            # Convert the values to float
            df = df.apply(pd.to_numeric, errors='coerce')

            # Save in the dictionary
            resources[sheet_name] = df.to_dict(orient="index")

    # Process the other sheets individually
    for sheet_name in data.keys():
        if sheet_name not in similar_sheets and sheet_name != "Thermal Resources Params":
            resources[sheet_name] = data[sheet_name]

    return resources

def load_resources_params(m, data):
    # Check if the "buildings, resources" sheet exists in the data
    if "buildings, resources" in data:  # Sheet name in lowercase
        df = data["buildings, resources"].dropna(how="all")  # Remove empty rows

        # Check if the first row contains the correct headers
        if df.iloc[0, 0] == "Load/Building/Resource":
            df.columns = df.iloc[0]  # Set the first row as header
            df = df.iloc[1:]  # Remove the first row now that it is the header

        # Fill merged cells in the first column
        df.iloc[:, 0] = df.iloc[:, 0].ffill()

        # Rename columns
        df.columns = ["Resource", "Parameter"] + list(df.columns[2:])

        # Check if the building columns are numeric
        building_columns = df.columns[2:]  # Building columns
        try:
            building_columns = [int(col) for col in building_columns]  # Convert to integers
        except ValueError as e:
            print(f"Erro ao converter colunas para inteiros: {e}")
            print("Colunas dos edifícios:", df.columns[2:])
            return data

        # Create a structured dictionary for all resources data
        all_resources_data = {}

        # List of resources to be processed (exact names)
        resources = [
            "Electric vehicle",   # Exact name
            "Hydrogen Storage",
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

        # Process the rows of the spreadsheet to organize the resource data
        for _, row in df.iterrows():
            resource = row["Resource"]  # Resource name
            if pd.isna(resource):  # If it is NaN, skip this row
                continue
            parameter = row["Parameter"]  # Parameter name
            values = row.iloc[2:].to_dict()  # Dictionary {building: value}

            # Check if the resource is in the list of resources and add to the dictionary
            if resource in resources:
                if resource not in all_resources_data:
                    all_resources_data[resource] = {}

                all_resources_data[resource][parameter] = values

        # Add all resource data to the main dictionary
        for resource, data_dict in all_resources_data.items():
            data[resource] = data_dict

        # for resource in resources:
        #     if resource in data:
        #         print(f"\nData for resource: {resource}")
        #         resource_data = data[resource]
        #
        #         # Create a DataFrame for the current resource
        #         df = pd.DataFrame(resource_data)
        #
        #         # Transpose the DataFrame so that buildings are columns
        #         df = df.transpose()
        #
        #         # Rename columns to "Parameter" and the buildings
        #         df.index.name = "Parameter"
        #         df.columns.name = "Building"
        #
        #         # Print the formatted DataFrame
        #         print(df)
        #     else:
        #         print(f"\nResource '{resource}' not found in the data.")

    return data


def Buildings_max_temp(m, data):
    sheet_name = "Buildings - Max temperature"

    # Check if the sheet exists in the data dictionary
    if sheet_name not in data:
        print(f"Sheet '{sheet_name}' not found in the data dictionary.")
        return data

    # Load the DataFrame and remove completely empty rows
    df = data[sheet_name].dropna(how="all")


    # We assume that the first useful row of the DataFrame (df.iloc[0]) contains
    #    the column names, including "Load/Building/Resource" and building IDs.
    df.columns = df.iloc[0]  # Set row 0 as the header
    df = df.iloc[1:]  # Remove the header row that we just used

    #  Remove completely empty columns, if any
    df = df.dropna(axis=1, how="all")

    #  Now rename the first column to "Load/Building/Resource"
    #    and the remaining columns (which should be 1, 2, 3, ..., 39) to integers.
    original_columns = list(df.columns)
    # We need to ensure that the first one is "Load/Building/Resource" and the rest are integers.
    new_columns = ["Load/Building/Resource"]

    # For the remaining columns, we convert to int if possible
    for c in original_columns[1:]:
        try:
            new_columns.append(int(c))
        except ValueError:
            # If unable to convert to int, you can decide what to do
            new_columns.append(str(c))

    df.columns = new_columns

    #  If the first row of the DataFrame duplicates the header, remove it
    #    (sometimes happens when the sheet has a repeated header).
    #    Check if the first cell is "Load/Building/Resource".
    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    #  Set "Load/Building/Resource" as the index
    df = df.set_index("Load/Building/Resource")

    #  Convert all values to float (or int), ignoring errors
    df = df.apply(pd.to_numeric, errors="coerce")

    # ───────────── Save to the data dictionary ─────────────
    # If you want to store as a nested dictionary (each row becomes a key, etc.):
    data["inside_max_temp"] = df.to_dict(orient="index")

    # df_print = pd.DataFrame.from_dict(data["inside_max_temp"], orient="index")
    #
    # print("\n--- Data from the 'Buildings - Max temperature' sheet ---")
    # print(df_print)
    # print("--- End of data ---\n")
    return data



def Buildings_min_temp(m, data):
    sheet_name = "Buildings - Min temperature"

    # Check if the sheet exists in the data dictionary
    if sheet_name not in data:
        print(f"Sheet '{sheet_name}' not found in the data dictionary.")
        return data

    # Load the DataFrame and remove completely empty rows
    df = data[sheet_name].dropna(how="all")

    df.columns = df.iloc[0]  # Set row 0 as header
    df = df.iloc[1:]  # Remove the header row that we just used

    #  Remove completely empty columns, if any
    df = df.dropna(axis=1, how="all")

    #  Now rename the first column to "Load/Building/Resource"

    original_columns = list(df.columns)
    # We need to ensure that the first one is "Load/Building/Resource" and the rest are integers.
    new_columns = ["Load/Building/Resource"]

    # For the remaining columns, we convert to int if possible
    for c in original_columns[1:]:
        try:
            new_columns.append(int(c))
        except ValueError:
            # If unable to convert to int, you can decide what to do

            new_columns.append(str(c))

    df.columns = new_columns

    #  If the first row of the DataFrame duplicates the header, remove it

    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    #  Set "Load/Building/Resource" as the index
    df = df.set_index("Load/Building/Resource")

    #  Convert all values to float (or int), ignoring errors
    df = df.apply(pd.to_numeric, errors="coerce")
    data["inside_min_temp"] = df.to_dict(orient="index")

    df_print = pd.DataFrame.from_dict(data["inside_min_temp"], orient="index")
    # print(f"Temperatures for Building {building}:")
    # for hour in range(1, 25):  # Hours from 1 to 24
    #     print(f"Hour {hour}: {data['inside_min_temp'][building][hour]}")

    # print("\n--- Data from the 'Buildings - Min temperature' sheet ---")
    # print(df_print)
    # print("--- End of data ---\n")
    return data




def Outside_temp(m, data):
    sheet_name = "Outside_temperature"
    # Check if the sheet exists in the data dictionary
    if sheet_name not in data:
        print(f"Sheet '{sheet_name}' not found in the data dictionary.")
        return data

    # Load the DataFrame and remove completely empty rows
    df = data[sheet_name].dropna(how="all")


    #  We assume that the first useful row of the DataFrame (df.iloc[0]) contains

    df.columns = df.iloc[0]  # Set row 0 as header
    df = df.iloc[1:]  # Remove the header row that we just used

    #  Remove completely empty columns, if any
    df = df.dropna(axis=1, how="all")

    #  Now rename the first column to "Load/Building/Resource"
    original_columns = list(df.columns)
    new_columns = ["Load/Building/Resource"]

    # For the remaining columns, we convert to int if possible
    for c in original_columns[1:]:
        try:
            new_columns.append(int(c))
        except ValueError:
            # If unable to convert to int, you can decide what to do
            new_columns.append(str(c))

    df.columns = new_columns

    #  If the first row of the DataFrame duplicates the header, remove it

    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    #  Set "Load/Building/Resource" as the index
    df = df.set_index("Load/Building/Resource")

    #  Convert all values to float (or int), ignoring errors
    df = df.apply(pd.to_numeric, errors="coerce")
    data["outside_temp"] = df.to_dict(orient="index")
    # df_print = pd.DataFrame.from_dict(data["outside_temp"], orient="index")
    #
    # print("\n--- Data from the 'Outside_temperature' sheet ---")
    # print(df_print)
    # print("--- End of data ---\n")
    return data



def Heat_Gains_losses(m, data):
    sheet_name = "Heat_Gains_Losses"

    # Check if the sheet exists in the data dictionary
    if sheet_name not in data:
        print(f"Sheet '{sheet_name}' not found in the data dictionary.")
        return data

    # Load the DataFrame and remove completely empty rows
    df = data[sheet_name].dropna(how="all")

    # Set the first row as header
    df.columns = df.iloc[0]  # Set row 0 as header
    df = df.iloc[1:]  # Remove the header row that we just used
    df = df.dropna(axis=1, how="all")  # Remove completely empty columns

    original_columns = list(df.columns)
    new_columns = ["Load/Building/Resource"]

    # Try to convert columns to integers if possible
    for c in original_columns[1:]:
        try:
            new_columns.append(int(c))
        except ValueError:
            # If unable to convert to int, leave as string
            new_columns.append(str(c))

    df.columns = new_columns

    # If the first row duplicates the header, remove it
    if df.iloc[0, 0] == "Load/Building/Resource":
        df = df.iloc[1:]

    # Set "Load/Building/Resource" as the index
    df = df.set_index("Load/Building/Resource")

    # Convert all values to float (or int), ignoring errors
    df = df.apply(pd.to_numeric, errors="coerce")

    # Save the data to the dictionary
    data["loss_temp"] = df.to_dict(orient="index")

    # Optional: Print the DataFrame (for debugging purposes)
    # df_print = pd.DataFrame.from_dict(data["loss_temp"], orient="index")
    # print("\n--- Data from the 'Heat_Gains_Losses' sheet ---")
    # print(df_print)
    # print("--- End of data ---\n")

    return data


def Weather_forecasts(m, data):
    # Fixed file path inside the function
    file_path = "Input Data - Other.xlsx"

    # Load the Excel file
    df = pd.read_excel(file_path, sheet_name="Weather forecasts")

    # The first row contains the "Hours", so we get these columns
    hours = df.columns[1:].values  # Extracts the hours (first row without the column index)

    # Now, get the rows for solar variables, wind speed, and outside temperature
    solar_profile = df.iloc[0, 1:].apply(pd.to_numeric, errors='coerce').values
    wind_speed = df.iloc[1, 1:].apply(pd.to_numeric, errors='coerce').values

    # Organizing the data into a dictionary
    weather_data = {
        "hours": hours,  # The hours
        "solar_profile": solar_profile,  # Solar profile
        "wind_speed": wind_speed,  # Wind speed
    }

    # Add the processed data to the data dictionary
    data["weather_forecasts"] = weather_data

    # print("\n--- Weather Forecast Data ---")
    #
    # # Solar data
    # solar_data = data["weather_forecasts"]["solar_profile"]
    # print("\nSolar Profile for the 24 hours:")
    # for h in range(1, 25):
    #     print(f"Hour {h}: {solar_data[h - 1]}")
    #
    # # Wind speed data
    # wind_data = data["weather_forecasts"]["wind_speed"]
    # print("\nWind Speed for the 24 hours:")
    # for h in range(1, 25):
    #     print(f"Hour {h}: {wind_data[h - 1]}")
    #
    # print("\n--- End of data ---")

    return data



def process_prices(m, data):
    file_path = "Input Data - Other.xlsx"  # Correct file path
    sheet_name = "Prices"  # Sheet name

    # Read the sheet, ensuring the first header is treated correctly
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Set the first column as the index correctly
    df = df.set_index(df.columns[0])

    # Rename the index to "Parameters" to avoid issues
    df.index.name = "Parameters"

    # Convert values to float (to avoid formatting errors)
    df = df.apply(pd.to_numeric, errors="coerce")

    # Save the prices in the 'data' dictionary
    data["prices"] = df.to_dict(orient="index")

    # # Correct printing, ensuring the index appears as "Parameters"
    # print("\n--- Data from the 'Prices' sheet ---")
    # print(df.to_string(index=True))
    # print("--- End of data ---\n")

    return data

import pandas as pd

