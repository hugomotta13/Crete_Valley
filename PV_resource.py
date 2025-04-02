import pyomo.environ as pe


def define_pv_constraints(m):
    for j in m.building:
        for t in m.hours:
            if float(m.Installed_PV[j]) == 1:
                m.c1.add(m.P_PV[j, t] >= 0)
                m.c1.add(m.P_PV[j, t] <= m.alpha[j, t] * m.PV_max[j])
                m.c1.add(m.D_PV[j, t] >= 0)
                m.c1.add(m.D_PV[j, t] <= m.P_PV[j, t])
                m.c1.add(m.U_PV[j, t] >= 0)
                m.c1.add(m.U_PV[j, t] <= m.alpha[j, t] * m.PV_max[j] - m.P_PV[j, t])


            else:
                m.c1.add(m.P_PV[j, t] == 0)
                m.c1.add(m.U_PV[j, t] == 0)
                m.c1.add(m.D_PV[j, t] == 0)
