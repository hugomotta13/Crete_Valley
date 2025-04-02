import pyomo.environ as pe


def fuel_cell_storage_constraints(m):
    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_FC[j]) == 1:
                m.c1.add(m.P_FC_E[j, t] == m.eta_FC[j] * m.P_Sto_FC_H2[j, t])
                m.c1.add(0 <= m.P_Sto_FC_H2[j, t])
                m.c1.add(m.P_Sto_FC_H2[j, t] <= m.mode_discharge_H2[j, t] * m.P_FC_H2_max[j])

            else:
               m.c1.add(m.P_FC_E[j, t]==0)
               m.c1.add(m.P_Sto_FC_H2[j, t]==0)

    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_FC[j]) == 1:
                m.c1.add(m.U_Sto_FC_H2[j, t] <= m.mode_discharge_H2[j, t] * m.P_FC_H2_max[j] - m.P_Sto_FC_H2[j, t])
                m.c1.add(m.D_Sto_FC_H2[j, t] <= m.P_Sto_FC_H2[j, t])
                m.c1.add(m.U_FC_E[j, t] == m.eta_FC[j] * m.U_Sto_FC_H2[j, t])
                m.c1.add(m.D_FC_E[j, t] == m.eta_FC[j] * m.D_Sto_FC_H2[j, t])
                m.c1.add(m.D_FC_E[j, t] * m.U_FC_E[j, t] >= 0)
            else:
                m.c1.add(m.U_Sto_FC_H2[j, t]==0)
                m.c1.add(m.D_Sto_FC_H2[j, t]==0)
                m.c1.add(m.U_FC_E[j, t]==0)
                m.c1.add(m.D_FC_E[j, t]==0)
                m.c1.add(m.mode_discharge_H2[j, t] == 0)

