import pandas as pd
import pyomo.environ as pe
import numpy as np
import os

import matplotlib.pyplot as plt


def save_results_to_excel(m, output_file="final_results_crete_valley.xlsx"):
    hours = list(m.hours)
    building = list(m.building)

    with pd.ExcelWriter(output_file) as writer:
        # Global results
        df = pd.DataFrame({
            "Hour": hours,
            "Electric Energy Balance": [pe.value(m.E_E[t]) for t in hours],
            "Natural Gas Consumption": [pe.value(m.E_G[t])  for t in hours],
            "Hydrogen Consumption": [pe.value(m.E_H2[t])  for t in hours],
            "Boiler Energy Consumption": [pe.value(m.E_B[t])  for t in hours],
            "Thermal Energy Consumption": [pe.value(m.E_H[t])  for t in hours],

        })
        df.to_excel(writer, sheet_name='Results', index=False)
        if all(hasattr(m, attr) for attr in ['Fe', 'Fg', 'F_H2', 'F_H2O', 'F_reserve', 'F_Boiler']):
            df_costs = pd.DataFrame({
                "Hour": list(m.hours),
                "Electricity Cost (Fe)": [pe.value(m.Fe[t]) / 1000 for t in m.hours],
                "Reserve Cost (F_reserve)": [pe.value(m.F_reserve[t]) / 1000 for t in m.hours],
                "Natural Gas Cost (Fg)": [pe.value(m.Fg[t]) / 1000 for t in m.hours],
                "Hydrogen Cost (F_H2)": [pe.value(m.F_H2[t]) / 1000 for t in m.hours],
                "Water Cost (F_H2O)": [pe.value(m.F_H2O[t]) / 1000 for t in m.hours],
                "Boiler Cost (F_Boiler)": [pe.value(m.F_Boiler[t]) / 1000 for t in m.hours],
            })

            df_costs["Total Cost per Hour"] = df_costs[
                ["Electricity Cost (Fe)", "Natural Gas Cost (Fg)",
                 "Hydrogen Cost (F_H2)", "Water Cost (F_H2O)", "Boiler Cost (F_Boiler)"]
            ].sum(axis=1)

            # Calcula o total acumulado
            total_cost = df_costs["Total Cost per Hour"].sum()

            # Escreve no Excel
            df_costs.to_excel(writer, sheet_name="Energy_Costs_Overview", index=False)

            # Agora escreve o total abaixo da tabela
            worksheet = writer.sheets["Energy_Costs_Overview"]
            start_row = len(df_costs) + 2  # duas linhas abaixo da tabela

            worksheet.cell(row=start_row, column=1, value="Total System Cost (€)")
            worksheet.cell(row=start_row, column=2, value=round(total_cost, 4))

        # Save results PV
        pd.DataFrame().to_excel(writer, sheet_name="PV_Results")

        start_col = 0

        for j in m.building:
            if pe.value(m.Installed_PV[j]) == 1:
                df_pv = pd.DataFrame({
                    f"P_PV_{j}": [pe.value(m.P_PV[j, t]) for t in m.hours],
                    f"PV_Downward_{j}": [pe.value(m.D_PV[j, t]) for t in m.hours],
                    f"PV_Upward_{j}": [pe.value(m.U_PV[j, t]) for t in m.hours],
                })

                if start_col == 0:
                    df_pv.insert(0, "Hour", list(m.hours))

                df_pv.to_excel(
                    writer,
                    sheet_name="PV_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )

                start_col += len(df_pv.columns) + 1  # pula uma coluna entre os blocos

        # Save results HP
        pd.DataFrame().to_excel(writer, sheet_name="HP_Results")

        start_col = 0

        hp_buildings = [j for j in m.building if pe.value(m.Installed_HP[j]) == 1]

        for j in hp_buildings:
            df_hp = pd.DataFrame({
                f"P_HP_{j}": [pe.value(m.P_HP[j, t]) for t in m.hours],
                f"HP_Upward_{j}": [pe.value(m.U_HP[j, t]) for t in m.hours],
                f"HP_Downward_{j}": [pe.value(m.D_HP[j, t]) for t in m.hours],
            })

            if start_col == 0:
                df_hp.insert(0, "Hour", list(m.hours))

            df_hp.to_excel(
                writer,
                sheet_name="HP_Results",
                startrow=0,
                startcol=start_col,
                index=False
            )

            start_col += len(df_hp.columns) + 1  # Skip one column between blocks

        # Heat pump temperatures
        pd.DataFrame().to_excel(writer, sheet_name="Temperatures_HP")  # Create an empty sheet
        start_col = 0
        for j in m.building:
            if pe.value(m.Installed_HP[j]) == 1:
                df_temp = pd.DataFrame({
                    f"Theta_E_{j}": [pe.value(m.Theta_E[j, t]) for t in m.hours],
                    f"Theta_U_{j}": [pe.value(m.Theta_U[j, t]) for t in m.hours],
                    f"Theta_D_{j}": [pe.value(m.Theta_D[j, t]) for t in m.hours],
                })

                if start_col == 0:
                    df_temp.insert(0, "Hour", list(m.hours))

                df_temp.to_excel(
                    writer,
                    sheet_name="Temperatures_HP",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )
                start_col += len(df_temp.columns) + 1  # Skip one column between blocks

        # CHP
        pd.DataFrame().to_excel(writer, sheet_name="CHP_Results")
        start_col = 0
        for j in m.building:
            if pe.value(m.Installed_CHP[j]) == 1:
                df_chp = pd.DataFrame({
                    f"P_CHPH_{j}": [pe.value(m.P_CHPH[j, t]) for t in m.hours],
                    f"U_CHPH_{j}": [pe.value(m.U_CHPH[j, t]) for t in m.hours],
                    f"D_CHPH_{j}": [pe.value(m.D_CHPH[j, t]) for t in m.hours],
                    f"P_CHPE_{j}": [pe.value(m.P_CHPE[j, t]) for t in m.hours],
                    f"U_CHPE_{j}": [pe.value(m.U_CHPE[j, t]) for t in m.hours],
                    f"D_CHPE_{j}": [pe.value(m.D_CHPE[j, t]) for t in m.hours],
                    f"P_CHPG_{j}": [pe.value(m.P_CHPG[j, t]) for t in m.hours],
                    f"D_CHPG_{j}": [pe.value(m.D_CHPG[j, t]) for t in m.hours],
                    f"U_CHPG_{j}": [pe.value(m.U_CHPG[j, t]) for t in m.hours],
                })
                # Add the hour column only once (in the first iteration)
                if start_col == 0:
                    df_chp.insert(0, "Hour", list(m.hours))
                df_chp.to_excel(
                    writer,
                    sheet_name="CHP_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )
                start_col += len(df_chp.columns) + 1

        # Battery
        pd.DataFrame().to_excel(writer, sheet_name="Battery_Results")
        start_col = 0

        for j in m.building:
            if pe.value(m.Installed_ESS[j]) == 1:
                df_battery = pd.DataFrame({
                    f"SOC_{j}": [pe.value(m.SOC[j, t]) for t in m.hours],
                    f"P_charge_{j}": [pe.value(m.P_charge[j, t]) for t in m.hours],
                    f"P_discharge_{j}": [pe.value(m.P_discharge[j, t]) for t in m.hours],
                    f"U_charge_{j}": [pe.value(m.U_reserve_charge[j, t]) for t in m.hours],
                    f"D_charge_{j}": [pe.value(m.D_reserve_charge[j, t]) for t in m.hours],
                    f"U_discharge_{j}": [pe.value(m.U_reserve_discharge[j, t]) for t in m.hours],
                    f"D_discharge_{j}": [pe.value(m.D_reserve_discharge[j, t]) for t in m.hours],
                })

                # Add "Hour" only once
                if start_col == 0:
                    df_battery.insert(0, "Hour", list(m.hours))

                df_battery.to_excel(
                    writer,
                    sheet_name="Battery_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )

                start_col += len(df_battery.columns) + 1  # Skip one column between blocks

        # P2G (Power to Gas)
        pd.DataFrame().to_excel(writer, sheet_name="P2G_Results")
        start_col = 0

        for j in m.building:
            if pe.value(m.Installed_P2G[j]) == 1:
                df_p2g = pd.DataFrame({
                    f"P2G_E_{j}": [pe.value(m.P2G_E[j, t]) for t in m.hours],
                    f"P2G_H2_{j}": [pe.value(m.P2G_H2[j, t]) for t in m.hours],
                    f"U_P2G_E_{j}": [pe.value(m.U_P2G_E[j, t]) for t in m.hours],
                    f"D_P2G_E_{j}": [pe.value(m.D_P2G_E[j, t]) for t in m.hours],

                })
                if start_col == 0:
                    df_p2g.insert(0, "Hour", list(m.hours))

                df_p2g.to_excel(
                    writer,
                    sheet_name="P2G_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )

                # Skip one column between the building blocks
                start_col += len(df_p2g.columns) + 1
        # Hydrogen Storage
        pd.DataFrame().to_excel(writer, sheet_name="Hydrogen_Storage_Results")
        start_col = 0
        for j in m.building:
            if pe.value(m.Installed_ESS[j]) == 1:
                df_h2 = pd.DataFrame({
                    f"P_Sto_charge_H2_{j}": [pe.value(m.P_Sto_charge_H2[j, t]) for t in m.hours],
                    f"P_Sto_discharge_H2_{j}": [pe.value(m.P_Sto_discharge_H2[j, t]) for t in m.hours],
                    f"SOC_H2_{j}": [pe.value(m.SOC_H2[j, t]) for t in m.hours],
                    f"U_reserve_charge_{j}": [pe.value(m.U_reserve_charge[j, t]) for t in m.hours],
                    f"D_reserve_charge_{j}": [pe.value(m.D_reserve_charge[j, t]) for t in m.hours],
                    f"U_reserve_discharge_{j}": [pe.value(m.U_reserve_discharge[j, t]) for t in m.hours],
                    f"D_reserve_discharge_{j}": [pe.value(m.D_reserve_discharge[j, t]) for t in m.hours],
                })
                if start_col == 0:
                    df_h2.insert(0, "Hour", list(m.hours))
                df_h2.to_excel(
                    writer,
                    sheet_name="Hydrogen_Storage_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )
                start_col += len(df_h2.columns) + 1
        # Fuel Cell
        pd.DataFrame().to_excel(writer, sheet_name="FC_Results")
        start_col = 0
        for j in m.building:
            if pe.value(m.Installed_FC[j]) == 1:
                df_fc = pd.DataFrame({
                    f"P_FC_E_{j}": [pe.value(m.P_FC_E[j, t]) for t in m.hours],
                    f"U_FC_E_{j}": [pe.value(m.U_FC_E[j, t]) for t in m.hours],
                    f"D_FC_E_{j}": [pe.value(m.D_FC_E[j, t]) for t in m.hours],
                    f"P_Sto_FC_H2_{j}": [pe.value(m.P_Sto_FC_H2[j, t]) for t in m.hours],
                })
                if start_col == 0:
                    df_fc.insert(0, "Hour", list(m.hours))
                df_fc.to_excel(
                    writer,
                    sheet_name="FC_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )
                start_col += len(df_fc.columns) + 1

        # EV results
        pd.DataFrame().to_excel(writer, sheet_name="EV_Results")
        start_col = 0

        for j in m.building:
            if pe.value(m.Installed_EV[j]) == 1:
                df_ev = pd.DataFrame({
                    f"P_EV_E_charge_{j}": [pe.value(m.P_EV_E_charge[j, t]) for t in m.hours],
                    f"P_EV_E_discharge_{j}": [pe.value(m.P_EV_E_discharge[j, t]) for t in m.hours],
                    f"U_EV_E_up_{j}": [pe.value(m.U_EV_E_up[j, t]) for t in m.hours],
                    f"U_EV_E_down_{j}": [pe.value(m.U_EV_E_down[j, t]) for t in m.hours],
                    f"D_EV_E_up_{j}": [pe.value(m.D_EV_E_up[j, t]) for t in m.hours],
                    f"D_EV_E_down_{j}": [pe.value(m.D_EV_E_down[j, t]) for t in m.hours],
                    f"SOC_EV_{j}": [pe.value(m.SOC_EV_E[j, t]) for t in m.hours],
                })

                if start_col == 0:
                    df_ev.insert(0, "Hour", list(m.hours))

                df_ev.to_excel(
                    writer,
                    sheet_name="EV_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )

                start_col += len(df_ev.columns) + 1
        # --- Wind Turbine ---
        pd.DataFrame().to_excel(writer, sheet_name="Wind_Turbine_Results")
        start_col = 0
        for j in m.building:
            if pe.value(m.Installed_WT[j]) == 1:
                df_wind = pd.DataFrame({
                    f"P_wind_E_{j}": [pe.value(m.P_wind_E[j, t]) for t in m.hours],
                    f"U_wind_{j}": [pe.value(m.U_wind[j, t]) for t in m.hours],
                    f"D_wind_{j}": [pe.value(m.D_wind[j, t]) for t in m.hours],
                })

                if start_col == 0:
                    df_wind.insert(0, "Hour", list(m.hours))

                df_wind.to_excel(
                    writer,
                    sheet_name="Wind_Turbine_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )
                start_col += len(df_wind.columns) + 1
        # Boiler
        pd.DataFrame().to_excel(writer, sheet_name="Boiler_Results")
        start_col = 0
        for j in m.building:
            if pe.value(m.Installed_BB[j]) == 1:
                df_boiler = pd.DataFrame({
                    f"P_Boiler_F_{j}": [pe.value(m.P_boiler_F[j, t]) for t in m.hours],
                    f"U_Boiler_F_{j}": [pe.value(m.U_boiler_F[j, t]) for t in m.hours],
                    f"D_Boiler_F_{j}": [pe.value(m.D_boiler_F[j, t]) for t in m.hours],
                    f"P_Boiler_H_{j}": [pe.value(m.P_boiler_H[j, t]) for t in m.hours],
                    f"U_Boiler_H_{j}": [pe.value(m.U_boiler_H[j, t]) for t in m.hours],
                    f"D_Boiler_H_{j}": [pe.value(m.D_boiler_H[j, t]) for t in m.hours],
                    f"P_Boiler_E_{j}": [pe.value(m.P_boiler_E[j, t]) for t in m.hours],
                    f"U_Boiler_E_{j}": [pe.value(m.U_boiler_E[j, t]) for t in m.hours],
                    f"D_Boiler_E_{j}": [pe.value(m.D_boiler_E[j, t]) for t in m.hours],
                })

                if start_col == 0:
                    df_boiler.insert(0, "Hour", list(m.hours))

                df_boiler.to_excel(
                    writer,
                    sheet_name="Boiler_Results",
                    startrow=0,
                    startcol=start_col,
                    index=False
                )
                start_col += len(df_boiler.columns) + 1

    return m


def plot_results(m, output_folder="plot_result"):
    # Ensures the output folder exists and is clean
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for f in os.listdir(output_folder):
        fp = os.path.join(output_folder, f)
        if os.path.isfile(fp):
            os.remove(fp)

    hours = list(m.hours)

    # --- Natural Gas Consumption ---
    plt.figure(figsize=(10, 6))
    plt.bar(hours, [pe.value(m.E_G[t]) for t in hours], color='#808080')
    plt.xlabel('Hour of the Day')
    plt.ylabel('Natural Gas Consumption (kW)')
    plt.title('Natural Gas Consumption')
    plt.xticks(hours)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "natural_gas_consumption.png"), dpi=300)
    plt.close()

    # --- Electricity Balance ---
    plt.figure(figsize=(10, 6))
    plt.bar(hours, [pe.value(m.E_E[t]) for t in hours], color='blue')
    plt.xlabel('Hour')
    plt.ylabel('Electricity Balance (kW)')
    plt.title('Electric Energy Balance')
    plt.xticks(hours)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "electric_energy_balance.png"), dpi=300)
    plt.close()

    # --- Temperatures for buildings with HP ---
    for b in m.building:
        if pe.value(m.Installed_HP[b]) == 1:
            Theta_E = [pe.value(m.Theta_E[b, t]) for t in hours]
            Theta_U = [pe.value(m.Theta_U[b, t]) for t in hours]
            Theta_D = [pe.value(m.Theta_D[b, t]) for t in hours]

            plt.figure(figsize=(10, 6))
            x = np.array(hours)
            plt.bar(x - 0.2, Theta_E, width=0.2, label='Theta_E')
            plt.bar(x, Theta_U, width=0.2, label='Theta_U')
            plt.bar(x + 0.2, Theta_D, width=0.2, label='Theta_D')
            plt.title(f"Temperatures for Building {b}")
            plt.xlabel("Hour")
            plt.ylabel("Temperature (°C)")
            plt.xticks(hours)
            plt.yticks(np.arange(0, 30, 1))
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"building_{b}_temperatures.png"), dpi=300)
            plt.close()

    # --- PV Generation ---
    for j in m.building:
        if pe.value(m.Installed_PV[j]) == 1:
            P_PV = [pe.value(m.P_PV[j, t]) for t in hours]

            plt.figure(figsize=(10, 5))
            plt.bar(hours, P_PV, color="orange")
            plt.xlabel("Hour")
            plt.ylabel("Power (kW)")
            plt.title(f"PV Generation - Building {j}")
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.savefig(os.path.join(output_folder, f"P_PV_{j}.png"), dpi=300)
            plt.close()

    # --- Heat Pump Power ---
    for j in m.building:
        if pe.value(m.Installed_HP[j]) == 1:
            P_HP = [pe.value(m.P_HP[j, t]) for t in hours]

            plt.figure(figsize=(10, 5))
            plt.bar(hours, P_HP, color="green")
            plt.xlabel("Hour")
            plt.ylabel("Power (kW)")
            plt.title(f"Heat Pump Power - Building {j}")
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.savefig(os.path.join(output_folder, f"P_HP_{j}.png"), dpi=300)
            plt.close()

    # --- CHP Electricity & Gas Consumption ---
    for j in m.building:
        if pe.value(m.Installed_CHP[j]) == 1:
            P_CHPE = [pe.value(m.P_CHPE[j, t]) for t in hours]
            P_CHPG = [pe.value(m.P_CHPG[j, t]) for t in hours]

            plt.figure(figsize=(10, 5))
            plt.bar(hours, P_CHPE, color="red")
            plt.xlabel("Hour")
            plt.ylabel("Power (kW)")
            plt.title(f"CHP Electricity Generation - Building {j}")
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.savefig(os.path.join(output_folder, f"P_CHPE_{j}.png"), dpi=300)
            plt.close()

            plt.figure(figsize=(10, 5))
            plt.bar(hours, P_CHPG, color="#1f77b4")
            plt.xlabel("Hour")
            plt.ylabel("Gas Consumption (kW)")
            plt.title(f"CHP Gas Consumption - Building {j}")
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.savefig(os.path.join(output_folder, f"P_CHPG_{j}.png"), dpi=300)
            plt.close()
    # Battery charge/discharge plots
    for j in m.building:
        if pe.value(m.Installed_ESS[j]) == 1:
            df_battery = pd.DataFrame({
                'Hour': list(m.hours),
                'Charge Power': [pe.value(m.P_charge[j, t]) for t in m.hours],
                'Discharge Power': [pe.value(m.P_discharge[j, t]) for t in m.hours],
            })

            x = np.array(df_battery['Hour'])
            plt.figure(figsize=(10, 6))
            plt.bar(x, df_battery['Charge Power'], width=0.4, color='orange', label='Charge Power', align='center')
            plt.bar(x, df_battery['Discharge Power'], width=0.4, color='#000080', label='Discharge Power',
                    align='center', alpha=0.8)
            plt.xlabel("Hour")
            plt.ylabel("Power (kW)")
            plt.title(f"Battery {j} Charge and Discharge Power Over Time")
            plt.xticks(x)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"battery_{j}_charge_discharge.png"), dpi=300)
            plt.close()
    #  P2G Electricity and Hydrogen Bids
    for j in m.building:
        if pe.value(m.Installed_P2G[j]) == 1:
            hours = list(m.hours)
            P2G_E = [pe.value(m.P2G_E[j, t]) for t in hours]
            P2G_H2 = [pe.value(m.P2G_H2[j, t]) for t in m.hours]

            plt.figure(figsize=(10, 5))
            plt.bar(hours, P2G_E, color="brown")
            plt.xlabel("Hour")
            plt.ylabel("Power (kW)")
            plt.title(f"P2G Electricity Consumption - Building {j}")
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"P2G_E_building_{j}.png"), dpi=300)
            plt.close()

            plt.figure(figsize=(10, 6))
            bar_width = 0.2  # Bar width
            x = range(len(hours))  # Positions on the X-axis
            plt.bar([i - 0.5 * bar_width for i in x], P2G_H2, bar_width, color='orange', label='Hydrogen Bids (P2G_H2)')
            plt.xlabel('Hour ')
            plt.ylabel('Power (kW)')
            plt.title('P2G')
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            # Position the legend outside the chart
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))

            plt.tight_layout()

            # Save the chart
            plt.savefig(os.path.join(output_folder, f"p2g_{j}_plot.png"), dpi=300, bbox_inches='tight')
            plt.close()
    for j in m.building:
        if pe.value(m.Installed_FC[j]) == 1:
            df_fc_j = pd.DataFrame({
                "Hour": list(m.hours),
                "P_FC_E": [pe.value(m.P_FC_E[j, t]) for t in m.hours]
            })

            plt.figure(figsize=(10, 5))
            plt.bar(df_fc_j["Hour"], df_fc_j["P_FC_E"], color="purple")
            plt.xlabel("Hour")
            plt.ylabel("Power (kW)")
            plt.title(f"Fuel Cell Electricity Generation - Building {j}")
            plt.xticks(list(m.hours))
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"P_FC_E_{j}.png"), dpi=300)
            plt.close()
    #  EV
    for j in m.building:
        if pe.value(m.Installed_EV[j]) == 1:
            plt.figure(figsize=(10, 6))
            # Charging and discharging values
            P_up = [pe.value(m.P_EV_E_charge[j, t]) for t in m.hours]
            P_down = [pe.value(m.P_EV_E_discharge[j, t]) for t in m.hours]

            plt.bar(hours, P_up, label='Charging Power (P_EV_E_charge)', color='#1f77b4')
            plt.bar(hours, P_down, bottom=P_up, label='Discharging Power (P_EV_E_discharge)', color='#ff7f0e')

            # Visual settings
            plt.xlabel('Hour of the Day')
            plt.ylabel('Power (kW)')
            plt.title(f'EV Charging & Discharging - Building {j}')
            plt.xticks(hours)
            plt.ylim(0, max([a + b for a, b in zip(P_up, P_down)]) * 1.2)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"EV_{j}_power.png"), dpi=300)
            plt.close()
    # --- Plot Wind Turbine Power Generation ---
    for j in m.building:
        if pe.value(m.Installed_WT[j]) == 1:
            plt.figure(figsize=(10, 6))

            P_wind = [pe.value(m.P_wind_E[j, t]) for t in m.hours]

            plt.bar(hours, P_wind, color='b', label='P_wind_E (Power Generated)')

            plt.xlabel('Hour of the Day')
            plt.ylabel('Power (kW)')
            plt.title(f'Wind Turbine {j} Power Generation')
            plt.xticks(hours)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()

            plt.savefig(os.path.join(output_folder, f"wind_turbine_{j}_power.png"), dpi=300)
            plt.close()
    # Biomass Boiler
    for j in m.building:
        if pe.value(m.Installed_BB[j]) == 1:
            hours = list(m.hours)

            # Heat power generated
            P_H = [pe.value(m.P_boiler_H[j, t]) for t in m.hours]

            # Eletricidade consumida
            P_E = [pe.value(m.P_boiler_E[j, t]) for t in m.hours]

            # Electricity consumed
            plt.figure(figsize=(10, 6))
            plt.bar(hours, P_H, color='#1f77b4', label='Thermal Power Generated (P_Boiler_H)')
            plt.xlabel('Hour of the Day')
            plt.ylabel('Power (kW)')
            plt.title(f'Boiler {j} - Thermal Power Generated')
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"boiler_{j}_thermal_power.png"), dpi=300)
            plt.close()

            # Chart of electricity consumed
            plt.figure(figsize=(10, 6))
            plt.bar(hours, P_E, color='#ff7f0e', label='Electricity Consumed (P_Boiler_E)')
            plt.xlabel('Hour of the Day')
            plt.ylabel('Power (kW)')
            plt.title(f'Boiler {j} - Electricity Consumption')
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"boiler_{j}_electricity_consumption.png"), dpi=300)
            plt.close()


def plot_initial_loads(m, output_folder="plot_result/initial_loads"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Clear old files from the folder
    for file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    hours = list(m.hours)
    x = range(len(hours))
    bar_width = 0.25

    for j in m.building:
        has_electric = any(pe.value(m.P_ILE[j, t]) > 0 for t in hours)
        has_heat = any(pe.value(m.heat_load[j, t]) > 0 for t in hours)
        has_chp = any(pe.value(m.P_loadCHP[j, t]) > 0 for t in hours)

        if has_electric or has_heat or has_chp:
            plt.figure(figsize=(12, 6))

            if has_electric:
                P_ILE_vals = [pe.value(m.P_ILE[j, t]) for t in hours]
                plt.bar([h - bar_width for h in x], P_ILE_vals, width=bar_width, label='P_ILE', color='blue')

            if has_heat:
                heat_vals = [pe.value(m.heat_load[j, t]) for t in hours]
                plt.bar(x, heat_vals, width=bar_width, label='Heat Load', color='orange')

            if has_chp:
                chp_vals = [pe.value(m.P_loadCHP[j, t]) for t in hours]
                plt.bar([h + bar_width for h in x], chp_vals, width=bar_width, label='CHP Heat', color='green')

            plt.xlabel("Hour")
            plt.ylabel("Power (kWh)")
            plt.title(f"Loads for Building {j}")
            plt.xticks(x, hours)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"load_building_{j}.png"), dpi=300)
            plt.close()

    print(f"Charts saved in: {output_folder}")

def plot_secondary_reserves_separate(m, hours,output_folder):


    os.makedirs(output_folder, exist_ok=True)

    bar_width = 0.4
    x = np.arange(len(hours))

    # --- PV ---
    for j in m.building:
        if pe.value(m.Installed_PV[j]) == 1:
            U_PV = [pe.value(m.U_PV[j, t]) for t in m.hours]
            D_PV = [pe.value(m.D_PV[j, t]) for t in m.hours]
            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_PV, width=bar_width, label='Upward Reserve', color='purple')
            plt.bar(x + bar_width / 2, D_PV, width=bar_width, label='Downward Reserve', color='orange')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'PV Reserves - Building {j}')
            plt.xticks(x, hours)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"PV_{j}_reserves.png"))
            plt.close()

    # --- HP ---
    for j in m.building:
        if pe.value(m.Installed_HP[j]) == 1:
            U_HP = [pe.value(m.U_HP[j, t]) for t in m.hours]
            D_HP = [pe.value(m.D_HP[j, t]) for t in m.hours]
            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_HP, width=bar_width, label='Upward Reserve', color='purple')
            plt.bar(x + bar_width / 2, D_HP, width=bar_width, label='Downward Reserve', color='orange')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'HP Reserves - Building {j}')
            plt.xticks(x, hours)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"HP_{j}_reserves.png"))
            plt.close()

    # --- CHP ---
    for j in m.building:
        if pe.value(m.Installed_CHP[j]) == 1:
            U_CHPG = [pe.value(m.U_CHPG[j, t]) for t in m.hours]
            D_CHPG = [pe.value(m.D_CHPG[j, t]) for t in m.hours]
            U_CHPE = [pe.value(m.U_CHPE[j, t]) for t in m.hours]
            D_CHPE = [pe.value(m.D_CHPE[j, t]) for t in m.hours]

            # Plot for CHPG (gás)
            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_CHPG, width=bar_width, color='orange', label='Upward Reserve (CHPG)')
            plt.bar(x + bar_width / 2, D_CHPG, width=bar_width, color='green', label='Downward Reserve (CHPG)')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'CHP GAS Reserves - Building {j}')
            plt.xticks(x, hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"CHP_{j}_CHPG_reserves.png"), dpi=300)
            plt.close()

            # Plot for CHPE (elétrico)
            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_CHPE, width=bar_width, color='blue', label='Upward Reserve (CHPE)')
            plt.bar(x + bar_width / 2, D_CHPE, width=bar_width, color='red', label='Downward Reserve (CHPE)')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'CHP ELECTRIC Reserves - Building {j}')
            plt.xticks(x, hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"CHP_{j}_CHPE_reserves.png"), dpi=300)
            plt.close()

    #ESS
    for j in m.building:
        if pe.value(m.Installed_ESS[j]) == 1:
            hours = np.array(list(m.hours))
            width = 0.4

            U_reserve_charge = [pe.value(m.U_reserve_charge[j, t]) for t in m.hours]
            D_reserve_charge = [pe.value(m.D_reserve_charge[j, t]) for t in m.hours]
            U_reserve_discharge = [pe.value(m.U_reserve_discharge[j, t]) for t in m.hours]
            D_reserve_discharge = [pe.value(m.D_reserve_discharge[j, t]) for t in m.hours]

            # Charge reserves
            plt.figure(figsize=(10, 6))
            plt.bar(hours - width / 2, U_reserve_charge, width=width, color='purple',
                    label='Upward Bids Charge')
            plt.bar(hours + width / 2, D_reserve_charge, width=width, color='orange',
                    label='Downward Bids Charge')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'Battery {j} - Charge Reserve Bids')
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"battery_{j}_charge_reserve.png"), dpi=300,
                        bbox_inches='tight')
            plt.close()

            # Discharge reserves
            plt.figure(figsize=(10, 6))
            plt.bar(hours - width / 2, U_reserve_discharge, width=width, color='purple',
                    label='Upward Bids Discharge')
            plt.bar(hours + width / 2, D_reserve_discharge, width=width, color='orange',
                    label='Downward Bids Discharge')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'Battery {j} - Discharge Reserve Bids')
            plt.xticks(hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"battery_{j}_discharge_reserve.png"), dpi=300,
                        bbox_inches='tight')
            plt.close()

    # --- P2G ---
    for j in m.building:
        if pe.value(m.Installed_P2G[j]) == 1:
            U_P2G_E = [pe.value(m.U_P2G_E[j, t]) for t in m.hours]
            D_P2G_E = [pe.value(m.D_P2G_E[j, t]) for t in m.hours]

            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_P2G_E, width=bar_width, color='purple', label='Upward Reserve (P2G_E)')
            plt.bar(x + bar_width / 2, D_P2G_E, width=bar_width, color='orange',
                    label='Downward Reserve (P2G_E)')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'P2G Reserves - Building {j}')
            plt.xticks(x, hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"P2G_{j}_reserves.png"), dpi=300)
            plt.close()

    # --- Fuel Cell (FC) ---
    threshold = 0.5
    for j in m.building:
        if pe.value(m.Installed_FC[j]) == 1:
            U_FC_E = [pe.value(m.U_FC_E[j, t]) for t in m.hours]
            D_FC_E = [pe.value(m.D_FC_E[j, t]) for t in m.hours]
            if max(U_FC_E + D_FC_E) < threshold:
                continue
            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_FC_E, width=bar_width, color='purple', label='Upward Reserve (FC_E)')
            plt.bar(x + bar_width / 2, D_FC_E, width=bar_width, color='orange', label='Downward Reserve (FC_E)')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'Fuel Cell Reserves - Building {j}')
            plt.xticks(x, hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"FC_{j}_reserves.png"), dpi=300)
            plt.close()
    for j in m.building:
        if pe.value(m.Installed_EV[j]) == 1:
            plt.figure(figsize=(12, 6))

            U_EV = [pe.value(m.U_EV_E_up[j, t]) for t in m.hours]
            D_EV = [pe.value(m.D_EV_E_down[j, t]) for t in m.hours]
            plt.bar(x - bar_width / 2, U_EV, width=bar_width, label='Upward Reserve (U_EV_E_up)',
                    color='purple')
            plt.bar(x + bar_width / 2, D_EV, width=bar_width, label='Downward Reserve (D_EV_E_down)',
                    color='orange')
            plt.xlabel('Hour')
            plt.ylabel('Reserve Power (kW)')
            plt.title(f'EV Reserve - Building {j}')
            plt.xticks(x, hours)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()

            plt.savefig(os.path.join(output_folder, f"EV_{j}_Reserve.png"), dpi=300)
            plt.close()

    # --- Plot Wind Turbine Secondary Reserves ---
    for j in m.building:
        if pe.value(m.Installed_WT[j]) == 1:
            U_vals = [pe.value(m.U_wind[j, t]) for t in m.hours]
            D_vals = [pe.value(m.D_wind[j, t]) for t in m.hours]

            plt.figure(figsize=(12, 6))
            plt.bar(x - bar_width / 2, U_vals, width=bar_width, label='Upward Reserve (U_wind)', color='orange')
            plt.bar(x + bar_width / 2, D_vals, width=bar_width, label='Downward Reserve (D_wind)', color='purple')

            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'Wind Turbine {j} - Secondary Reserves')
            plt.xticks(x, hours)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()

            plt.savefig(os.path.join(output_folder, f"wind_turbine_{j}_reserves.png"), dpi=300)
            plt.close()
    # --- Boiler (Electricity) ---
    for j in m.building:
        if pe.value(m.Installed_BB[j]) == 1:
            U_boiler_E = [pe.value(m.U_boiler_E[j, t]) for t in m.hours]
            D_boiler_E = [pe.value(m.D_boiler_E[j, t]) for t in m.hours]
            U_boiler_F = [pe.value(m.U_boiler_F[j, t]) for t in m.hours]
            D_boiler_F = [pe.value(m.D_boiler_F[j, t]) for t in m.hours]
            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_boiler_E, width=bar_width, color='purple',
                    label='Upward Reserve (Boiler_E)')
            plt.bar(x + bar_width / 2, D_boiler_E, width=bar_width, color='orange',
                    label='Downward Reserve (Boiler_E)')
            plt.xlabel('Hour')
            plt.ylabel('Power (kW)')
            plt.title(f'Boiler {j} - Secondary Reserves (Electricity)')
            plt.xticks(x, hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"boiler_{j}_reserves_E.png"), dpi=300)
            plt.close()

            plt.figure(figsize=(10, 6))
            plt.bar(x - bar_width / 2, U_boiler_F, width=bar_width, color='green',
                    label='Upward Reserve (Boiler_Fuel)')
            plt.bar(x + bar_width / 2, D_boiler_F, width=bar_width, color='brown',
                    label='Downward Reserve (Boiler_Fuel)')
            plt.xlabel('Hour')
            plt.ylabel('Fuel Power (kW)')
            plt.title(f'Boiler {j} - Secondary Reserves (Fuel)')
            plt.xticks(x, hours)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, f"boiler_{j}_reserves_F.png"), dpi=300)
            plt.close()

def plot_aggregated_secondary_reserves(m, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    # Clear old files from the folder
    for file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    tecnologias = []
    up_values = []
    down_values = []

    def soma_reserva(var):
        return sum(pe.value(var[j, t]) for j in m.building for t in m.hours if (j, t) in var)

    # Coleta dos dados
    recursos = [
        ("EV", "U_EV_E_up", "D_EV_E_down"),
        ("Battery Discharge", "U_reserve_discharge", "D_reserve_discharge"),
        ("Battery charge", "U_reserve_charge", "D_reserve_charge"),
        ("HP", "U_HP", "D_HP"),
        ("CHP", "U_CHPE", "D_CHPE"),
        ("PV", "U_PV", "D_PV"),
        ("P2G", "U_P2G_E", "D_P2G_E"),
        ("Fuel Cell", "U_FC_E", "D_FC_E"),
        ("Boiler", "U_boiler_E", "D_boiler_E"),
        ("Wind", "U_wind", "D_wind"),
    ]

    for nome, up_var, down_var in recursos:
        if hasattr(m, up_var) and hasattr(m, down_var):
            tecnologias.append(nome)
            up_values.append(soma_reserva(getattr(m, up_var)))
            down_values.append(soma_reserva(getattr(m, down_var)))

