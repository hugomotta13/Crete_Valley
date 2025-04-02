import pyomo.environ as pe


def P2G_electrolyzer_constraints(m):
    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_P2G[j]) == 1:
                m.c1.add(m.P2G_H2[j, t] == m.eta_P2G[j] * m.P2G_E[j, t])

                m.c1.add(
                    m.P2G_H2[j, t] == m.P2G_Net_H2[j, t] + m.P2G_Sto_H2[j, t]
                )
                m.c1.add(m.P2G_E[j, t] >= m.P2G_E_min[j])
                m.c1.add(m.P2G_E[j, t] <= m.P2G_E_max[j])
            else:
                m.c1.add(m.P2G_H2[j, t] == 0)
                m.c1.add(m.P2G_E[j, t] == 0)
                m.c1.add(m.P2G_Net_H2[j, t] == 0)
                m.c1.add(m.P2G_Sto_H2[j, t] == 0)


    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_P2G[j]) == 1:

                    m.c1.add(m.U_P2G_E[j, t] <= m.P2G_E[j, t] - m.P2G_E_min[j])

                    m.c1.add(m.D_P2G_E[j, t] <= m.P2G_E_max[j] - m.P2G_E[j, t])

                    m.c1.add(m.U_P2G_H2[j, t] == m.eta_P2G[j] * m.U_P2G_E[j, t])

                    m.c1.add(m.D_P2G_H2[j, t] == m.eta_P2G[j] * m.D_P2G_E[j, t])

                    m.c1.add(m.U_P2G_H2[j, t] == m.U_P2G_Net_H2[j, t] + m.U_P2G_Sto_H2[j, t])
                    m.c1.add(m.D_P2G_H2[j, t] == m.D_P2G_Net_H2[j, t] + m.D_P2G_Sto_H2[j, t])
            else:
                m.c1.add(m.U_P2G_E[j, t] == 0)
                m.c1.add(m.D_P2G_E[j, t] == 0)
                m.c1.add(m.U_P2G_H2[j, t] == 0)
                m.c1.add(m.D_P2G_H2[j, t] == 0)
                m.c1.add(m.U_P2G_Net_H2[j, t] == 0)
                m.c1.add(m.D_P2G_Net_H2[j, t] == 0)
                m.c1.add(m.U_P2G_Sto_H2[j, t] == 0)
                m.c1.add(m.D_P2G_Sto_H2[j, t] == 0)
