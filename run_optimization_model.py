import pyomo.environ as pe
import logging
from pyomo.environ import SolverFactory, value, SolverStatus, TerminationCondition
from pyomo.util.infeasible import log_infeasible_constraints
from optimal_power_flow import(
    optimal_power_flow,
    define_power_flow_parameters,

)
import  math
def run_optimization(m, solver_name="cplex"):
    # electric energy balance equation
    for t in m.hours:
        m.c1.add(
            m.E_E[t] == (
                    sum(
                        m.P_ILE[j, t]  # Interruptible Load
                       + m.P_HP[j, t]  # HP
                       - m.P_PV[j, t]  #PV
                       - m.P_CHPE[j, t]  # CHP
                        for j in m.building
                    )
                  + sum(m.P_charge[b, t] - m.P_discharge[b, t] for b in m.building) # Storage
                      + sum(m.P2G_E[k, t] for k in m.building)   # Power to Gas
                    + sum(m.P_FC_E[fc, t] for fc in m.building)   # Fuel Cell
                    + sum(m.P_EV_E_charge[ve, t] - m.P_EV_E_discharge[ve, t] for ve in m.building) # EV
                    - sum(m.P_wind_E[wt, t] for wt in m.building)   #wind turbine
                    +  sum(m.P_boiler_E[b, t] for b in m.building) #boiler
            )
        )
    optimal_power_flow(m)

    # Gas Consumption
    for t in m.hours:
        m.c1.add(
            m.E_G[t] == sum(m.P_CHPG[j, t] + m.P_ILG[j, t] for j in m.building)
        )

    for t in m.hours:
        # Upward secondary reserve bids for electricity
        m.c1.add(
            m.U_E[t] == sum(
                m.U_PV[j, t]
                + m.U_HP[j, t]
                 + m.U_CHPE[j, t]
                for j in m.building
            )

            +sum(
                m.U_reserve_charge[b, t] + m.U_reserve_discharge[b, t] for b in m.building)
            +
            sum( m.U_P2G_E[b, t] for b in m.building)
            + sum(m.U_FC_E[fc, t] for fc in m.building)
            + sum(m.U_EV_E_up[d, t] + m.U_EV_E_down[d, t] for d in m.building)
            +sum(m.U_wind[wt, t] for wt in m.building)
            +sum(m.U_boiler_E[b, t] for b in m.building)

        )

    for t in m.hours:
        # Downward secondary reserve bids for electricity
        m.c1.add(
            m.D_E[t] == (
                    sum(m.D_PV[j, t]
                         + m.D_HP[j, t]
                         + m.D_CHPE[j, t]
                        for j in m.building)
            )

             +sum(m.D_reserve_charge[b, t] + m.D_reserve_discharge[b, t] for b in m.building)
            +
            sum(m.D_P2G_E[b, t] for b in m.building)
            + sum(m.D_FC_E[fc, t] for fc in m.building)
            + sum(m.D_EV_E_up[f, t] + m.D_EV_E_down[f, t] for f in m.building)
            +  sum(m.D_wind[wt, t] for wt in m.building)
            +  sum(m.D_boiler_E[b, t] for b in m.building)
        )

    # Enforce the distribution of the secondary reserve band: 2/3 for upward regulation and 1/3 for downward regulation
    for t in m.hours:
        m.c1.add(m.U_E[t] == 2 * m.D_E[t])

    # Upward secondary reserve bids for gas
    for t in m.hours:
        m.c1.add(m.U_G[t] == sum(m.U_CHPG[j, t] for j in m.building))
    # Downward secondary reserve bids for gas
    for t in m.hours:
        m.c1.add(m.D_G[t] == sum(m.D_CHPG[j, t] for j in m.building))

    for t in m.hours:
        m.c1.add(
            m.F_reserve[t] == (
                    - m.lambda_B[t] * (m.U_E[t] + m.D_E[t])
                    + (m.lambda_DE[t] * m.phi_D[t] * m.D_E[t]
                       - m.lambda_UE[t] * m.phi_U[t] * m.U_E[t])
            )
        )

    for t in m.hours:
        # Constraint for electricity cost
        m.c1.add(
            m.Fe[t] == (m.electricity_price[t] * m.E_E[t] + m.F_reserve[t])
        )

    for t in m.hours:
        m.c1.add(m.Fe_electric_cost[t] == m.electricity_price[t] * m.E_E[t])

    # Constraint for natural gas cost
    for t in m.hours:
        m.c1.add(m.Fg_gas_cost[t] == m.natural_gas_price[t] * m.E_G[t])
    for t in m.hours:

        m.c1.add(
            m.Fg[t] == m.natural_gas_price[t] * m.E_G[t] + (
                    m.lambda_UG[t] * m.phi_U[t] * m.U_G[t] - m.lambda_DG[t] * m.phi_D[t] * m.D_G[t])

        )
    # Upward secondary reserve bids for hydrogen imbalances due to P2G activation
    for t in m.hours:
        m.c1.add(m.U_H2[t] == sum(m.U_P2G_Net_H2[j, t] for j in m.building))

    # Downward secondary reserve bids for hydrogen imbalances due to P2G activation
    for t in m.hours:
        m.c1.add(m.D_H2[t] == sum(m.D_P2G_Net_H2[j, t] for j in m.building))

    # Hydrogen delivery scenario: sum of hydrogen injected by P2G and HSS into the gas network
    for t in m.hours:
        m.c1.add(
            m.E_H2[t] == sum(m.P2G_Net_H2[j, t] + m.P_Sto_Net_H2[j, t] for j in m.building))

    # Upward secondary reserve bids for biomass fuel imbalances due to biomass boiler activation
    for t in m.hours:
        m.c1.add(m.U_B[t] == sum(m.U_boiler_F[b, t] for b in m.building))

    # Downward secondary reserve bids for biomass fuel imbalances due to biomass boiler activation
    for t in m.hours:
        m.c1.add(m.D_B[t] == sum(m.D_boiler_F[b, t] for b in m.building))

    # Biomass consumption scenario: sum of fuel used by all biomass boilers in the system
    for t in m.hours:
        m.c1.add(m.E_B[t] == sum(m.P_boiler_F[b, t] for b in m.building))

    # Cost of purchasing biomass for boilers, including energy generation and reserve costs
    for t in m.hours:
        m.c1.add(m.F_Boiler[t] == m.lambda_B[t] * m.E_B[t] + (
                    m.lambda_DB[t] * m.phi_D[t] * m.D_B[t] - m.lambda_UB[t] * m.phi_U[t] * m.U_B[t]))

    # Cost of selling hydrogen in the green hydrogen market, including costs for upward and downward reserve participation
    for t in m.hours:
        m.c1.add(
            m.F_H2[t] == (
                    -m.green_hydrogen * m.E_H2[t]
                    + m.hydrogen_imbalance * m.phi_U[t] * m.U_H2[t]
                    - m.hydrogen_imbalance * m.phi_D[t] * m.D_H2[t]
            )
        )

    # Cost of purchasing water for hydrogen electrolysis, including reserve participation costs
    for t in m.hours:
        m.c1.add(
            m.F_H2O[t] == m.water_price * sum(
                m.P2G_E[j, t] + m.D_P2G_E[j, t] * m.phi_D[t] - m.U_P2G_E[j, t] * m.phi_U[t] for j in m.building
            ) * m.factor_water
        )

    # Heat delivery scenario: sum of heat consumed by heating loads and generated by CHPs, minus biomass heat
    for t in m.hours:
        m.c1.add(
            m.E_H[t] == sum(
                m.P_ILH[j, t] -  # Inflexible Load Heating (ILH)
                #  m.P_DH[j, t] -  # District Heating Load (DH)
                m.P_CHPH[j, t]  # Heat produced by CHP
                for j in m.building
            )
            + sum(m.P_boiler_H[b, t] for b in m.building)  # Heat produced by the biomass boiler

        )

       # Minimize net cost of electricity, gas, hydrogen and secondary reserve trading
    penalty_voltage = 1e9  # Penalidade alta para violações de tensão
    penalty_current = 1e9 # Penalidade alta para violações de corrente
    m.objective = pe.Objective(
        expr=(
                sum(m.Fe[t] + m.Fg[t] + m.F_Boiler[t] + m.F_H2O[t] + m.F_H2[t] for t in m.hours) +
                penalty_voltage * sum(m.V_viol_lower[j, t] + m.V_viol_upper[j, t] for j in m.node for t in m.hours) +
                penalty_current * sum(m.I_viol[i, j, t] for (i, j) in m.line for t in m.hours)
        ),
        sense=pe.minimize
    )

    # m.objective = pe.Objective(
    #     expr=sum(m.Fe[t] + m.Fg[t]+m.F_Boiler[t] + m.F_H2O[t]+m.F_H2[t]
    #              for t in m.hours),
    #     sense=pe.minimize
    # )

    # Call the solver to solve the optimization model
    solver = SolverFactory(solver_name)
    results = solver.solve(m, tee=True,options={"timelimit": 120})

    print("\n🔍 Carga total acumulada por nó nas 24 horas (em kW):")

    for n in m.node:
        carga_total = 0
        for t in m.hours:
            carga_total += sum(
                pe.value(
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
                )
                for b in m.building if m.building_node[b] == n
            )
        print(f"Nó {n}: {carga_total:.2f} kW")

    for j in m.node:
        tensoes = []
        for t in m.hours:
            U_sq = pe.value(m.U[j, t])
            if U_sq is not None:
                U_real = math.sqrt(U_sq)
                tensoes.append(f"{U_real:.4f}")
            else:
                tensoes.append("nan")
        print(f"Nó {j}: U = [{', '.join(tensoes)}]")
    slack_node = next(iter(m.Slack))

    total_penalidade_tensao = sum(
        pe.value(m.V_viol_lower[j, t] + m.V_viol_upper[j, t])
        for j in m.node if j != slack_node
        for t in m.hours
    )

    total_penalidade_corrente = sum(
        pe.value(m.I_viol[i, j, t])
        for (i, j) in m.line
        for t in m.hours
    )

    print(f"Soma total da penalidade por tensão: {total_penalidade_tensao:.6f}")
    print(f"Soma total da penalidade por corrente: {total_penalidade_corrente:.6f}")

    # Check solver status
    if (results.solver.status == SolverStatus.ok) and \
            (results.solver.termination_condition == TerminationCondition.optimal):
        print("Optimization solved successfully!")

    elif results.solver.termination_condition == TerminationCondition.infeasible:
        print("Infeasible solution detected.")

        # Enable logs at the INFO level
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('pyomo.core').setLevel(logging.INFO)

        # Display infeasible constraints
        log_infeasible_constraints(m, log_expression=True)

    else:
        print("Solver Status:", results.solver.status)
        print("Termination Condition:", results.solver.termination_condition)



