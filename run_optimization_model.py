import pyomo.environ as pe
import logging
from pyomo.environ import SolverFactory, value, SolverStatus, TerminationCondition
from pyomo.util.infeasible import log_infeasible_constraints

def run_optimization(m, solver_name="cplex"):
    for t in m.hours:
        m.c1.add(
            m.E_E[t] == (
                    sum(
                        m.P_ILE[j, t]
                       + m.P_HP[j, t]
                       - m.P_PV[j, t]
                       - m.P_CHPE[j, t]
                        for j in m.building
                    )
                  + sum(m.P_charge[b, t] - m.P_discharge[b, t] for b in m.building)
                      + sum(m.P2G_E[k, t] for k in m.building)   # Power to Gas
                    + sum(m.P_FC_E[fc, t] for fc in m.building)   # Fuel Cell
                    + sum(m.P_EV_E_charge[ve, t] - m.P_EV_E_discharge[ve, t] for ve in m.building)
                    - sum(m.P_wind_E[wt, t] for wt in m.building)   #wind turbine
                    +  sum(m.P_boiler_E[b, t] for b in m.building)
            )
        )

    for t in m.hours:
        m.c1.add(
            m.E_G[t] == sum(m.P_CHPG[j, t] + m.P_ILG[j, t] for j in m.building)
        )

    for t in m.hours:
        # Upward secondary reserve bids
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
        # Downward secondary reserve bids
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

    for t in m.hours:
        m.c1.add(m.U_E[t] == 2 * m.D_E[t])

    for t in m.hours:
        m.c1.add(m.U_G[t] == sum(m.U_CHPG[j, t] for j in m.building))

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
    for t in m.hours:
        m.c1.add(m.Fg_gas_cost[t] == m.natural_gas_price[t] * m.E_G[t])

    for t in m.hours:
        # Constraint for natural gas cost
        m.c1.add(
            m.Fg[t] == m.natural_gas_price[t] * m.E_G[t] + (
                    m.lambda_UG[t] * m.phi_U[t] * m.U_G[t] - m.lambda_DG[t] * m.phi_D[t] * m.D_G[t])

        )

    for t in m.hours:
        m.c1.add(m.U_H2[t] == sum(m.U_P2G_Net_H2[j, t] for j in m.building))

    for t in m.hours:
        m.c1.add(m.D_H2[t] == sum(m.D_P2G_Net_H2[j, t] for j in m.building))
    for t in m.hours:
        m.c1.add(
            m.E_H2[t] == sum(m.P2G_Net_H2[j, t] + m.P_Sto_Net_H2[j, t] for j in m.building))

    for t in m.hours:
        m.c1.add(m.U_B[t] == sum(m.U_boiler_F[b, t] for b in m.building))

    for t in m.hours:
        m.c1.add(m.D_B[t] == sum(m.D_boiler_F[b, t] for b in m.building))

    for t in m.hours:
        m.c1.add(m.E_B[t] == sum(m.P_boiler_F[b, t] for b in m.building))

    for t in m.hours:
        m.c1.add(m.F_Boiler[t] == m.lambda_B[t] * m.E_B[t] + (
                    m.lambda_DB[t] * m.phi_D[t] * m.D_B[t] - m.lambda_UB[t] * m.phi_U[t] * m.U_B[t]))

    for t in m.hours:
        m.c1.add(
            m.F_H2[t] == (
                    -m.green_hydrogen * m.E_H2[t]
                    + m.hydrogen_imbalance * m.phi_U[t] * m.U_H2[t]
                    - m.hydrogen_imbalance * m.phi_D[t] * m.D_H2[t]
            )
        )

    for t in m.hours:
        m.c1.add(
            m.F_H2O[t] == m.water_price * sum(
                m.P2G_E[j, t] + m.D_P2G_E[j, t] * m.phi_D[t] - m.U_P2G_E[j, t] * m.phi_U[t] for j in m.building
            ) * m.factor_water
        )
    for t in m.hours:
        m.c1.add(
            m.E_H[t] == sum(
                m.P_ILH[j, t] +  # Inflexible Load Heating (ILH)
                m.P_DH[j, t] -  # District Heating Load (DH)
                m.P_CHPH[j, t]  # Heat produced by CHP
                for j in m.building
            )
            + sum(m.P_boiler_H[b, t] for b in m.building)  # Heat produced by the biomass boiler

        )

        # Objective function: Minimize total cost
    m.objective = pe.Objective(
        expr=sum(m.Fe[t] + m.Fg[t]+m.F_Boiler[t] + m.F_H2O[t]+m.F_H2[t]
                 for t in m.hours),
        sense=pe.minimize
    )



    solver = SolverFactory(solver_name)
    results = solver.solve(m, tee=True)

    if (results.solver.status == SolverStatus.ok) and \
            (results.solver.termination_condition == TerminationCondition.optimal):
        print("Optimization solved successfully!")

    elif results.solver.termination_condition == TerminationCondition.infeasible:
        print("Infeasible solution detected.")

        # Habilitar logs no nível INFO
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('pyomo.core').setLevel(logging.INFO)

        # Exibir restrições inviáveis
        log_infeasible_constraints(m, log_expression=True)

    else:
        print("Solver Status:", results.solver.status)
        print("Termination Condition:", results.solver.termination_condition)

    # print("\n--- Resultados H2 ---")
    # for t in m.hours:
    #     try:
    #         print(f"Hora {t}:")
    #         print(f"  U_H2     = {pe.value(m.U_H2[t])}")
    #         print(f"  D_H2     = {pe.value(m.D_H2[t])}")
    #         print(f"  E_H2     = {pe.value(m.E_H2[t])}")
    #         print(f"  F_H2     = {pe.value(m.F_H2[t])}")
    #         print(f"  F_H2O    = {pe.value(m.F_H2O[t])}")
    #     except Exception as e:
    #         print(f"⚠️  Erro ao acessar variáveis da hora {t}: {e}")
    #
    # print("\n--- Energia consumida pelos P2G (Power to Gas) ---")
    # for t in m.hours:
    #     try:
    #         valor = sum(pe.value(m.P2G_E[k, t]) for k in m.building)
    #         print(f"Hora {t}: {valor:.2f} kW")
    #     except Exception as e:
    #         print(f"⚠️ Erro ao acessar P2G_E na hora {t}: {e}")
