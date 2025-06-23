import pandas

import pandas as pd
import pyomo.environ as pe
import math
import matplotlib.pyplot as plt
import os
import re
from collections import defaultdict
import numpy as np
import networkx as nx


def load_power_network_data(file_path="System_data33.xlsx"):
    df_lines = pd.read_excel(file_path, sheet_name="Lines")
    df_nodes = pd.read_excel(file_path, sheet_name="Nodes")
    df_network_profile = pd.read_excel(file_path, sheet_name="network_profile")

    # Reading lines
    lines = list(zip(df_lines["From"], df_lines["To"]))
    R_ohm = dict(zip(lines, df_lines["R(ohm)"]))
    X_ohm = dict(zip(lines, df_lines["X(ohm)"]))
    Imax = dict(zip(lines, df_lines["Imax"]))  # em A

    # Reading building-to-node mapping
    building_to_node = dict(zip(df_nodes["building"].astype(str), df_nodes["Node"].astype(int)))
    return {
        "lines": lines,
        "R_ohm": R_ohm,
        "X_ohm": X_ohm,
        "building_to_node": building_to_node,
        "Imax": Imax,
        "slack_node": int(df_network_profile["slack_node"].iloc[0]),
        "V_base": float(df_network_profile["V_base"].iloc[0]),
        "S_base": float(df_network_profile["S_base"].iloc[0]),
        "V_min_pu": float(df_network_profile["V_min_pu"].iloc[0]),
        "V_max_pu": float(df_network_profile["V_max_pu"].iloc[0])
    }


def define_power_flow_parameters(m, network_data):
    m.S_base = pe.Param(initialize=network_data["S_base"], within=pe.PositiveReals)  # in VA
    S_base_va = network_data["S_base"] * 1000  # in VA
    V_base_volts = (network_data["V_base"] * 1000)
    I_base = (network_data["S_base"] * 1000) / (math.sqrt(3) * V_base_volts)
    # Conversion to impedance base
    Z_base = (V_base_volts ** 2) / S_base_va
    fp = 0.95
    phi_rad = math.acos(fp)
    tan_phi = math.tan(phi_rad)
    m.tan_phi = pe.Param(initialize=tan_phi)
    m.P_pu = pe.Var(m.node, m.hours, within=pe.Reals)
    m.Q_pu = pe.Var(m.node, m.hours, within=pe.Reals)

    m.Slack = pe.Param(initialize=network_data["slack_node"], within=pe.NonNegativeIntegers, mutable=True)
    m.V_0 = pe.Param(initialize=1.0)
    m.V_min_sq = pe.Param(initialize=network_data["V_min_pu"] ** 2, within=pe.NonNegativeReals)
    m.V_max_sq = pe.Param(initialize=network_data["V_max_pu"] ** 2, within=pe.NonNegativeReals)
    R_pu = {l: r / Z_base for l, r in network_data["R_ohm"].items()}
    X_pu = {l: x / Z_base for l, x in network_data["X_ohm"].items()}

    # Stores it back in the dictionary
    network_data["R_pu"] = R_pu
    network_data["X_pu"] = X_pu

    m.R_pu = pe.Param(m.line, initialize=network_data["R_pu"], within=pe.NonNegativeReals)
    m.X_pu = pe.Param(m.line, initialize=network_data["X_pu"], within=pe.NonNegativeReals)
    m.Imax_sq = pe.Param(m.line, initialize={k: (v / I_base) ** 2 for k, v in network_data["Imax"].items()})

    # -------------------------------Variables-------------------------------------------------------------------
    m.U = pe.Var(m.node, m.hours, within=pe.NonNegativeReals)
    m.P_line = pe.Var(m.line, m.hours, within=pe.Reals)
    m.Q_line = pe.Var(m.line, m.hours, within=pe.Reals)
    m.U_aux = pe.Var(m.node, m.hours, within=pe.NonNegativeReals)
    m.P_hat = pe.Var(m.line, m.hours, within=pe.Reals)  # Auxiliary active power flow
    m.Q_hat = pe.Var(m.line, m.hours, within=pe.Reals)  # Auxiliary reactive power flow
    m.U_hat = pe.Var(m.node, m.hours, within=pe.NonNegativeReals) # Auxiliary squared voltage
    def I_sq_bounds_rule(m, i, j, t):
        return (0, m.Imax_sq[i, j])

    m.I_sq = pe.Var(m.line, m.hours, within=pe.NonNegativeReals, bounds=I_sq_bounds_rule)
    m.P_slack = pe.Var(m.hours, within=pe.Reals)
    m.Q_slack = pe.Var(m.hours, within=pe.Reals)
    # Voltage violations (upper or lower limits)
    m.V_viol_lower = pe.Var(m.node, m.hours, within=pe.NonNegativeReals)
    m.V_viol_upper = pe.Var(m.node, m.hours, within=pe.NonNegativeReals)
    # Current violations
    m.I_viol = pe.Var(m.line, m.hours, within=pe.NonNegativeReals)

    return m


def compute_downstream_nodes(lines, root=None, incluir_no=True):
    from collections import defaultdict

    filhos = defaultdict(list)
    for i, j in lines:
        filhos[i].append(j)

    def dfs(no):
        stack = [no]
        visited = set()
        while stack:
            atual = stack.pop()
            if atual not in visited:
                visited.add(atual)
                stack.extend(filhos[atual])
        if not incluir_no:
            visited.discard(no)
        return visited

    todos_os_nos = set(i for i, _ in lines) | set(j for _, j in lines)

    downstream = {}
    for no in todos_os_nos:
        downstream[no] = dfs(no)

    return downstream


def optimal_power_flow(m):
    slack = pe.value(m.Slack)
    # Net active power at the nodes
    m.active_power_from_buildings = pe.ConstraintList()
    for n in m.node:
        for t in m.hours:
            m.active_power_from_buildings.add(
                m.P_pu[n, t] ==
                sum(
                    m.P_ILE[b, t] +
                    m.P_HP[b, t] -
                    m.P_CHPE[b, t] -
                    m.P_PV[b, t] -
                    m.P_wind_E[b, t] +
                    m.P_EV_E_charge[b, t] -
                    m.P_EV_E_discharge[b, t] +
                    m.P_charge[b, t] -
                    m.P_discharge[b, t] +
                    m.P2G_E[b, t] +
                    m.P_FC_E[b, t] +
                    m.P_boiler_E[b, t]
                    for b in m.building
                    if m.building_node[b] == n
                ) / m.S_base
            )

    m.reactive_power_from_buildings = pe.ConstraintList()
    for n in m.node:
        for t in m.hours:
            m.reactive_power_from_buildings.add(
                m.Q_pu[n, t] == m.P_pu[n, t] * m.tan_phi
            )

    # 1. Fix voltage at the slack bus
    m.slack_voltage = pe.ConstraintList()
    for t in m.hours:
        m.slack_voltage.add(m.U[slack, t] == 1.0)

    m.slack_voltage_hat = pe.ConstraintList()
    for t in m.hours:
        m.slack_voltage_hat.add(m.U_hat[slack, t] == 1.0)  # Fix U_hat at the slack

    # 2. Active power balance

    # ----------Slack bus--------------------------
    m.active_power_balance_P_slack = pe.ConstraintList()
    for t in m.hours:
        outgoing_P = sum(m.P_line[slack, k, t] for (i, k) in m.line if i == slack)
        losses = sum(m.R_pu[slack, k] * m.I_sq[slack, k, t] for (i, k) in m.line if i == slack)
        m.active_power_balance_P_slack.add(
            m.P_slack[t] == m.P_pu[slack, t] + outgoing_P + losses
        )
    #----------------Other nodes--------------------
    m.active_power_balance_P = pe.ConstraintList()
    for j in m.node:
        if j == slack:
            continue  # No slack already enforced

        for t in m.hours:
            incoming_P = sum(m.P_line[i, j, t] for (i, jj) in m.line if jj == j)
            outgoing_P = sum(m.P_line[j, k, t] for (jj, k) in m.line if jj == j)
            losses = sum(m.R_pu[j, k] * m.I_sq[j, k, t] for (jj, k) in m.line if jj == j)

            m.active_power_balance_P.add(
                incoming_P == m.P_pu[j, t] + outgoing_P + losses
            )

    # 3. Reactive power balance

    #--------- Slack Bus---------------------------
    m.reactive_power_balance_Q_slack = pe.ConstraintList()
    for t in m.hours:
        outgoing_Q = sum(m.Q_line[slack, k, t] for (i, k) in m.line if i == slack)
        losses_Q = sum(m.X_pu[slack, k] * m.I_sq[slack, k, t] for (i, k) in m.line if i == slack)
        m.reactive_power_balance_Q_slack.add(
            m.Q_slack[t] == m.Q_pu[slack, t] + outgoing_Q + losses_Q
        )

    #----------------Other nodes--------------------
    m.reactive_power_balance_Q = pe.ConstraintList()
    for j in m.node:
        if j == slack:
            continue
        for t in m.hours:
            incoming_Q = sum(m.Q_line[i, j, t] for (i, jj) in m.line if jj == j)
            outgoing_Q = sum(m.Q_line[j, k, t] for (jj, k) in m.line if jj == j)
            losses_Q = sum(m.X_pu[j, k] * m.I_sq[j, k, t] for (jj, k) in m.line if jj == j)
            m.reactive_power_balance_Q.add(
                incoming_Q == m.Q_pu[j, t] + outgoing_Q + losses_Q
            )

    # 4. Voltage drop along the lines

    m.voltage_drop = pe.ConstraintList()
    for (i, j) in m.line:
        for t in m.hours:
            R = m.R_pu[i, j]
            X = m.X_pu[i, j]
            term_RX = 2 * (R * m.P_line[i, j, t] + X * m.Q_line[i, j, t])
            term_loss = (R ** 2 + X ** 2) * m.I_sq[i, j, t]

            m.voltage_drop.add(
                m.U[j, t] == m.U[i, t] - term_RX + term_loss
            )
    # 5. Thermal limit SOCP relaxation
    m.current_power_relation = pe.ConstraintList()
    for (i, j) in m.line:
        for t in m.hours:
            m.current_power_relation.add(
                m.I_sq[i, j, t] * m.U[i, t] >= m.P_line[i, j, t] ** 2 + m.Q_line[i, j, t] ** 2
            )

    # 6. Voltage limits for all nodes except the slack
    m.voltage_bounds_lower = pe.ConstraintList()
    m.voltage_bounds_upper = pe.ConstraintList()

    for j in m.node:
        if j in m.Slack:
            continue
        for t in m.hours:
            m.voltage_bounds_lower.add(m.U[j, t] + m.V_viol_lower[j, t] >= m.V_min_sq)
            m.voltage_bounds_upper.add(m.U[j, t] - m.V_viol_upper[j, t] <= m.V_max_sq)

    # 7. Voltage equality at the slack bus

    m.aux_voltage_slack = pe.ConstraintList()
    for t in m.hours:
        m.aux_voltage_slack.add(m.U[slack, t] == m.U_hat[slack, t])

    # 8. Auxiliary voltage drop (LinDistFlow)

    lines_list = list(m.line.data())  # Compute radial descendants based on m.line
    downstream = compute_downstream_nodes(lines_list, root=0, incluir_no=True)

    m.link_aux_power = pe.ConstraintList()
    for (i, j) in m.line:
        for t in m.hours:
            nos_jusantes = downstream[j]
            m.link_aux_power.add(
                m.P_hat[i, j, t] == sum(m.P_pu[k, t] for k in nos_jusantes)
            )
            m.link_aux_power.add(
                m.Q_hat[i, j, t] == sum(m.Q_pu[k, t] for k in nos_jusantes)
            )
    m.aux_voltage_drop = pe.ConstraintList()
    for (i, j) in m.line:
        for t in m.hours:
            R = m.R_pu[i, j]
            X = m.X_pu[i, j]
            m.aux_voltage_drop.add(
                m.U_hat[j, t] == m.U_hat[i, t] - 2 * (R * m.P_hat[i, j, t] + X * m.Q_hat[i, j, t])
            )

    # 9. Upper bound of auxiliary voltage

    m.voltage_upper_hat = pe.ConstraintList()
    for j in m.node:
        if j != 0:
            for t in m.hours:
                m.voltage_upper_hat.add(
                    m.U_hat[j, t] <= m.V_max_sq
                )

    # 10.  Voltage limits including the slack bus
    m.voltage_bounds_soft = pe.ConstraintList()
    for j in m.node:
        if j in m.Slack:
            continue
        for t in m.hours:
            m.voltage_bounds_soft.add(
                m.U[j, t] >= m.V_min_sq - m.V_viol_lower[j, t]
            )
            m.voltage_bounds_soft.add(
                m.U[j, t] <= m.V_max_sq + m.V_viol_upper[j, t]
            )

    # 11. Current limit including the slack bus
    m.current_limit_soft = pe.ConstraintList()
    for (i, j) in m.line:
        for t in m.hours:
            m.current_limit_soft.add(
                m.I_sq[i, j, t] <= m.Imax_sq[i, j] + m.I_viol[i, j, t]
            )

    return m


def export_results_to_excel(m, output_path="power_flow_results.xlsx"):
    # Voltages: one column per node
    voltage_data = {}
    for n in m.node:
        tensoes = []
        for t in m.hours:
            val = pe.value(m.U[n, t])
            if val is not None and val >= 0:
                U_pu = round(math.sqrt(val), 6)
            else:
                U_pu = None  # ou use 0, se preferir forçar visualização
            tensoes.append(U_pu)
        voltage_data[f"Node {n}"] = tensoes

    df_voltage = pd.DataFrame(voltage_data)
    df_voltage.insert(0, "Hour", list(m.hours))

    # Currents: one column per line (i,j)
    current_data = {
        f"{i}->{j}": [round(np.sqrt(pe.value(m.I_sq[i, j, t]) or 0), 6) for t in m.hours]
        for (i, j) in m.line
    }
    df_current = pd.DataFrame(current_data)
    df_current.insert(0, "Hour", list(m.hours))

    # Active power per line
    P_data = {}
    for (i, j) in m.line:
        P_data[f"{i}->{j}"] = [round(pe.value(m.P_line[i, j, t]) * m.S_base, 6) for t in m.hours]
    df_P = pd.DataFrame(P_data)
    df_P.insert(0, "Hour", list(m.hours))

    # Reactive power per line
    Q_data = {}
    for (i, j) in m.line:
        Q_data[f"{i}->{j}"] = [round(pe.value(m.Q_line[i, j, t]) * m.S_base, 6) for t in m.hours]
    df_Q = pd.DataFrame(Q_data)
    df_Q.insert(0, "Hour", list(m.hours))

    # Net active power per bus
    P_pu_data = {}
    for n in m.node:
        P_pu_data[f"Node {n}"] = [round(pe.value(m.P_pu[n, t]) * m.S_base, 6) for t in m.hours]
    df_P_pu = pd.DataFrame(P_pu_data)
    df_P_pu.insert(0, "Hour", list(m.hours))

    Q_pu_data = {}
    for n in m.node:
        Q_pu_data[f"Node {n}"] = [round(pe.value(m.Q_pu[n, t]) * m.S_base, 6) for t in m.hours]
    df_Q_pu = pd.DataFrame(Q_pu_data)
    df_Q_pu.insert(0, "Hour", list(m.hours))
    # Totals
    total_gen_kW = sum(
        pe.value(m.P_PV[b, t]) +
        pe.value(m.P_CHPE[b, t]) +
        pe.value(m.P_wind_E[b, t]) +
        pe.value(m.P_EV_E_discharge[b, t]) +
        pe.value(m.P_discharge[b, t])
        for b in m.building for t in m.hours
    )

    # Total active power consumption (in kW)
    total_load_kW = sum(
        pe.value(m.P_ILE[b, t]) +
        pe.value(m.P_HP[b, t]) +
        pe.value(m.P_EV_E_charge[b, t]) +
        pe.value(m.P_charge[b, t]) +
        pe.value(m.P2G_E[b, t]) +
        pe.value(m.P_FC_E[b, t]) +
        pe.value(m.P_boiler_E[b, t])
        for b in m.building for t in m.hours
    )

    # Net active power injected into the grid
    net_P_injected_kW = total_load_kW - total_gen_kW

    # Active power losses (I²R)
    total_losses_kW = sum(
        pe.value(m.I_sq[i, j, t]) * pe.value(m.R_pu[i, j]) * m.S_base
        for (i, j) in m.line for t in m.hours
    )

    # Reactive power (from slack bus)
    total_Q_gen_kVAr = sum(pe.value(m.Q_slack[t]) for t in m.hours) * m.S_base
    total_Q_demand_kVAr = total_load_kW * math.tan(math.acos(0.95))  # PF = 0.95
    total_Q_losses_kVAr = total_Q_gen_kVAr - total_Q_demand_kVAr

    # Create summary DataFrame
    df_summary = pd.DataFrame([
        ["Total active power generation", total_gen_kW, "kW"],
        ["Total active power consumption", total_load_kW, "kW"],
        ["Net active power injected (load - gen)", net_P_injected_kW, "kW"],
        ["Active losses (I²R)", total_losses_kW, "kW"],
        ["Total reactive power generated (slack)", total_Q_gen_kVAr, "kVAr"],
        ["Estimated reactive power demand (PF=0.95)", total_Q_demand_kVAr, "kVAr"],
        ["Estimated reactive losses", total_Q_losses_kVAr, "kVAr"]
    ], columns=["Description", "Value", "Unit"])

    #  Export
    with pd.ExcelWriter(output_path) as writer:
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        # Save voltage matrix
        df_voltage.to_excel(writer, sheet_name="Voltages in pu (per unit)", index=False)

        # Find violations and append below the table
        violation_limit = 0.92
        violations = [("Hour", "Node", "Voltage (pu)")]

        for t in m.hours:
            for n in m.node:
                U_sq = pe.value(m.U[n, t])
                if U_sq is not None and U_sq >= 0:
                    U_pu = math.sqrt(U_sq)
                    if U_pu < violation_limit:
                        violations.append((t, n, round(U_pu, 6)))

        # Write violations below the voltage matrix
        start_row = len(df_voltage) + 3  # leave 2 blank rows after the voltage table

        # Write header and each violation row
        for row_idx, row_data in enumerate(violations):
            for col_idx, value in enumerate(row_data):
                writer.sheets["Voltages in pu (per unit)"].cell(
                    row=start_row + row_idx + 1, column=col_idx + 1, value=value
                )

        # Add total count line
        total_violations = len(violations) - 1  # exclude header
        writer.sheets["Voltages in pu (per unit)"].cell(
            row=start_row + len(violations) + 2, column=1,
            value=f"Total number of voltage violations below {violation_limit} pu: {total_violations}"
        )

        df_current.to_excel(writer, sheet_name="Currents in pu (per unit)", index=False)
        df_P.to_excel(writer, sheet_name="Active power on the lines", index=False)
        df_Q.to_excel(writer, sheet_name="Reactive power on the lines", index=False)
        df_P_pu.to_excel(writer, sheet_name="Active power at the nodes", index=False)
        df_Q_pu.to_excel(writer, sheet_name="Reactive power at the nodes", index=False)
    return df_voltage, df_P_pu, df_current, df_Q_pu


def generate_plots_per_node(df_voltage, df_P_pu, df_current, output_dir="Plots per node"):
    os.makedirs(output_dir, exist_ok=True)

    # Voltage plots per node
    for coluna in df_voltage.columns:
        if coluna == "Hour":
            continue
        serie = df_voltage[coluna].dropna()
        if not serie.empty:
            plt.figure()
            plt.plot(df_voltage["Hour"], serie, marker="o")
            plt.title(f"Voltage at Node {coluna}")
            plt.xticks(ticks=range(1, 25))
            plt.xlabel("Hour")
            plt.ylabel("Voltage [p.u.]")
            min_y = min(serie)
            ymin = max(0.83, min_y - 0.01)
            plt.ylim(ymin, 1.05)
            plt.yticks([round(y, 3) for y in np.arange(ymin, 1.051, 0.01)])
            plt.grid(True)
            plt.savefig(f"{output_dir}/{coluna}_voltage.png")
            plt.close()
    # Calculate the minimum voltage value per node
    minimos_por_no = {
        coluna: serie.min()
        for coluna, serie in df_voltage.items()
        if coluna != "Hour"
    }

    # Sort by node number (optional, if the names are "1", "2", etc.)
    minimos_ordenados = dict(sorted(minimos_por_no.items(), key=lambda x: int(re.findall(r'\d+', x[0])[0])))

    # Create the plot
    plt.figure(figsize=(12, 5))
    node_labels = [re.findall(r'\d+', nome)[0] for nome in minimos_ordenados.keys()]
    plt.bar(node_labels, minimos_ordenados.values())
    plt.axhline(0.92, color='r', linestyle='--', label='Voltage limit (0.92 p.u.)')
    plt.xlabel("Node")
    plt.ylabel("Minimum voltage [p.u.]")
    plt.title("Minimum voltage observed at each node")
    plt.xticks(rotation=90)
    plt.grid(True, axis='y')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{output_dir}/Summary_Minimum_Voltage_by_Node.png")
    plt.close()


    # Active power plots per node
    for coluna in df_P_pu.columns[1:]:
        plt.figure()
        plt.plot(df_P_pu["Hour"], df_P_pu[coluna], marker='s', color='green')
        plt.title(f"Net Active Power at Node {coluna}")
        plt.xticks(ticks=range(1, 25))
        plt.xlabel("Hour")
        plt.ylabel("Active Power [kW]")
        plt.grid(True)
        plt.tight_layout()
        safe_name = coluna.replace(">", "_")
        plt.savefig(f"{output_dir}/{safe_name}_Power.png")
        plt.close()

    # Current plots per line
    for coluna in df_current.columns[1:]:
        origem, destino = coluna.split("->")
        if origem.strip() == "0":
            continue  # Skip lines that start from node 0 (do not exist)

        plt.figure()
        plt.plot(df_current["Hour"], df_current[coluna], marker='x', color='red')
        plt.title(f"Current in Line {coluna}")
        plt.xticks(ticks=range(1, 25))
        plt.xlabel("Hour")
        plt.ylabel("Current  [p.u.]")
        plt.grid(True)
        plt.tight_layout()
        safe_name = coluna.replace(">", "_")
        plt.savefig(f"{output_dir}/{safe_name}_current.png")
        plt.close()
