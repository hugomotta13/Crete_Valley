import pyomo.environ as pe
def define_battery_constraints(m):
    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_ESS[j]) == 1:
                m.c1.add(
                    m.SOC[j, t + 1] == (
                            m.SOC[j, t]
                            + (m.P_charge[j, t] * m.eta_Sto_E_plus[j]
                               - (m.P_discharge[j, t] / m.eta_Sto_E_minus[j]))

                    )
                )
                m.c1.add(m.SOC[j, t + 1] >= m.SOC_Sto_E_min[j])
                m.c1.add(m.SOC[j, t + 1] <= m.SOC_Sto_E_max[j])

                m.c1.add(
                    m.P_discharge[j, t] + m.P_discharge_plus[j, t] <=
                    (1 - m.operation_mode[j, t]) * m.P_Sto_min[j]
                )
                m.c1.add(m.P_discharge[j, t] + m.P_discharge_plus[j, t] >= 0)

                m.c1.add(
                    m.P_charge[j, t] + m.P_charge_plus[j, t] <= m.operation_mode[j, t] * m.P_Sto_max[j]
                )
                m.c1.add(m.P_charge[j, t] + m.P_charge_plus[j, t] >= 0)

                m.c1.add(
                    m.P_charge[j, t] + m.P_charge_plus[j, t] +
                    m.P_discharge[j, t] + m.P_discharge_plus[j, t] <= m.P_Sto_max[j]
                )

                m.c1.add(m.P_discharge[j, t] >= 0)
                m.c1.add(m.P_discharge_plus[j, t] >= 0)
                m.c1.add(m.P_charge[j, t] >= 0)
                m.c1.add(m.P_charge_plus[j, t] >= 0)


            else:

                m.c1.add(m.P_charge[j, t] == 0)
                m.c1.add(m.P_charge_plus[j, t] == 0)
                m.c1.add(m.P_discharge[j, t] == 0)
                m.c1.add(m.P_discharge_plus[j, t] == 0)
                m.c1.add(m.SOC[j, t + 1] == m.SOC[j, t])

        m.c1.add(m.SOC[j, min(m.hours)] == m.SOC[j, max(m.hours)+1])


    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_ESS[j]) == 1:
                    m.c1.add(0 <= m.U_reserve_discharge[j, t])
                    m.c1.add(m.U_reserve_discharge[j, t] <= m.P_Sto_max[j] - m.P_discharge[j, t])

                    m.c1.add(0 <= m.U_reserve_charge[j, t])
                    m.c1.add(m.U_reserve_charge[j, t] <= m.P_charge[j, t])

                    m.c1.add(0 <= m.D_reserve_charge[j, t])
                    m.c1.add(m.D_reserve_charge[j, t] <= m.P_Sto_max[j] - m.P_charge[j, t])

                    m.c1.add(0 <= m.D_reserve_discharge[j, t])
                    m.c1.add(m.D_reserve_discharge[j, t] <= m.P_discharge[j, t])

                    m.c1.add(
                        (m.U_reserve_discharge[j, t] / m.eta_Sto_E_minus[j] +
                         m.U_reserve_charge[j, t] * m.eta_Sto_E_plus[j])
                        <= m.SOC[j, t + 1] - m.SOC_Sto_E_min[j]
                    )

                    m.c1.add(
                        (m.D_reserve_discharge[j, t] / m.eta_Sto_E_minus[j] +
                         m.D_reserve_charge[j, t] * m.eta_Sto_E_plus[j])
                        <= m.SOC_Sto_E_max[j] - m.SOC[j, t + 1]
                    )

                    m.c1.add(
                        m.U_reserve_charge[j, t] +
                        m.U_reserve_discharge[j, t] +
                        m.D_reserve_charge[j, t] +
                        m.D_reserve_discharge[j, t]
                        <= m.P_charge_plus[j, t + 1] + m.P_discharge_plus[j, t + 1]
                    )

                    m.c1.add(
                        m.U_reserve_charge[j, t] +
                        m.U_reserve_discharge[j, t] +
                        m.D_reserve_charge[j, t] +
                        m.D_reserve_discharge[j, t]
                        <= m.operation_mode[j, t]
                    )

                    m.c1.add(
                        m.P_charge_plus[j, t] +
                        m.P_discharge_plus[j, t]
                        <= (1 - m.operation_mode[j, t]) * m.big_M
                    )
            else:
                m.c1.add(m.U_reserve_charge[j, t] == 0)
                m.c1.add(m.U_reserve_discharge[j, t] == 0)
                m.c1.add(m.D_reserve_charge[j, t] == 0)
                m.c1.add(m.D_reserve_discharge[j, t] == 0)
                m.c1.add(m.operation_mode[j, t] == 0)

    for j in m.building:
         if pe.value(m.Installed_ESS[j]) == 1:
             # Inicializar reservas para t = 1
             m.c1.add(m.U_reserve_charge[j, 1] == 0)
             m.c1.add(m.U_reserve_discharge[j, 1] == 0)
             m.c1.add(m.D_reserve_charge[j, 1] == 0)
             m.c1.add(m.D_reserve_discharge[j, 1] == 0)








