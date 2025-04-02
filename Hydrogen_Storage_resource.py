import pyomo.environ as pe


def hydrogen_storage_constraints(m):
    for j in m.building:
        for t in m.hours:
            if int(m.Installed_HSS[j]) == 1:
                m.c1.add(
                    m.SOC_H2[j, t + 1] ==
                    m.SOC_H2[j, t] +
                    (
                            m.P_Sto_charge_H2[j, t] * m.eta_H2_plus[j]
                            - (m.P_Sto_discharge_H2[j, t] / m.eta_H2_minus[j])
                    )
                    - m.gamma_H2[j] * m.SOC_H2[j, t]
                )
                m.c1.add(m.SOC_H2[j, t] >= m.SOC_H2_min[j])
                m.c1.add(m.SOC_H2[j, t] <= m.SOC_H2_max[j])
                m.c1.add(m.P_Sto_charge_H2[j, t] == m.P2G_Sto_H2[j, t])
                m.c1.add(m.P_Sto_discharge_H2[j, t] == m.P_Sto_Net_H2[j, t] + m.P_Sto_FC_H2[j, t])
                m.c1.add(m.P_Sto_charge_H2[j, t] <= m.mode_charge_H2[j, t] * m.P_Sto_H2_max_up[j])
                m.c1.add(m.P_Sto_discharge_H2[j, t] <= m.mode_discharge_H2[j, t] * m.P_Sto_H2_max_down[j])
                m.c1.add(m.mode_charge_H2[j, t] + m.mode_discharge_H2[j, t] <= 1)
            else:
                m.c1.add(m.SOC_H2[j, t + 1] ==m.SOC_H2[j, t])
                m.c1.add(m.SOC_H2[j, t] ==0)
                m.c1.add(m.P_Sto_charge_H2[j, t] == 0)
                m.c1.add(m.P_Sto_discharge_H2[j, t] == 0)
                m.c1.add(m.mode_charge_H2[j, t] + m.mode_discharge_H2[j, t] ==0)
                m.c1.add(m.P_Sto_Net_H2[j, t]==0)


        m.c1.add(m.SOC_H2[j, min(m.hours)] == m.SOC_H2[j, max(m.hours)+1])


    for j in m.building:
        for t in m.hours:
            if m.Installed_HSS[j] == 1:
                m.c1.add(m.D_P2G_Sto_H2[j, t] >= 0)
                m.c1.add(m.D_P2G_Sto_H2[j, t] <= m.P_Sto_H2_max_up[j] - m.P_Sto_charge_H2[j, t])
                m.c1.add(m.U_P2G_Sto_H2[j, t] >= 0)
                m.c1.add(m.U_P2G_Sto_H2[j, t] <= m.P_Sto_charge_H2[j, t])
                m.c1.add(m.D_Sto_FC_H2[j, t] >= 0)
                m.c1.add(m.D_Sto_FC_H2[j, t] <= m.P_Sto_FC_H2[j, t])

                m.c1.add(m.U_Sto_FC_H2[j, t] >= 0)
                m.c1.add(m.U_Sto_FC_H2[j, t] <= m.P_Sto_H2_max_up[j] - m.P_Sto_discharge_H2[j, t])

                m.c1.add(
                    m.D_P2G_Sto_H2[j, t] + m.D_Sto_FC_H2[j, t]
                    <= (m.SOC_H2_max[j] - m.SOC_H2[j, t + 1]))
                m.c1.add(
                    m.U_P2G_Sto_H2[j, t] + m.U_Sto_FC_H2[j, t]
                    <= (m.SOC_H2[j, t + 1] - m.SOC_H2_min[j])
                )
            else:
                m.c1.add(m.D_P2G_Sto_H2[j, t] == 0)
                m.c1.add(m.U_P2G_Sto_H2[j, t] == 0)
                m.c1.add(m.D_Sto_FC_H2[j, t] == 0)
                m.c1.add(m.U_Sto_FC_H2[j, t] == 0)
                m.c1.add( m.D_P2G_Sto_H2[j, t] + m.D_Sto_FC_H2[j, t]==0)
                m.c1.add(m.U_P2G_Sto_H2[j, t] + m.U_Sto_FC_H2[j, t]==0)







