import pyomo.environ as pe


def define_biomassas_boiler_constraints(m):
    for j in m.building:
        for t in m.hours:
            m.c1.add(m.P_boiler_F[j, t] <= m.P_boiler_max_F[j] * m.Installed_BB[j])
            m.c1.add(m.P_boiler_F[j, t] >= m.P_boiler_min_F[j] * m.Installed_BB[j])
            m.c1.add(m.P_boiler_H[j, t] == m.eta_H[j] * m.P_boiler_F[j, t]* m.Installed_BB[j])
            m.c1.add(m.P_boiler_E[j, t] == m.eta_E[j] * m.P_boiler_F[j, t]* m.Installed_BB[j])

            if t > min(m.hours):
                m.c1.add(m.P_boiler_F[j, t] - m.P_boiler_F[j, t - 1] <= 15 * m.Installed_BB[j])
                m.c1.add(m.P_boiler_F[j, t - 1] - m.P_boiler_F[j, t] <= 10 * m.Installed_BB[j])

            m.c1.add(m.U_boiler_F[j, t] <= (m.P_boiler_F[j, t] - m.P_boiler_min_F[j]) * m.Installed_BB[j])
            m.c1.add(m.D_boiler_F[j, t] <= 0.2 * (m.P_boiler_max_F[j] - m.P_boiler_F[j, t]) * m.Installed_BB[j])

            m.c1.add(m.U_boiler_H[j, t] == m.eta_H[j] * m.U_boiler_F[j, t]* m.Installed_BB[j])
            m.c1.add(m.D_boiler_H[j, t] == m.eta_H[j] * m.D_boiler_F[j, t]* m.Installed_BB[j])
            m.c1.add(m.U_boiler_E[j, t] == m.eta_E[j] * m.U_boiler_F[j, t]* m.Installed_BB[j])
            m.c1.add(m.D_boiler_E[j, t] == m.eta_E[j] * m.D_boiler_F[j, t]* m.Installed_BB[j])

            m.c1.add(m.U_boiler_F[j, t] <= m.mi_biomass[j] * m.P_boiler_max_F[j] * m.Installed_BB[j])
            m.c1.add(m.D_boiler_F[j, t] <= m.mi_biomass[j] * m.P_boiler_max_F[j] * m.Installed_BB[j])
