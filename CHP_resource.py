import pyomo.environ as pe


def define_chp_constraints(m):
    for j in m.building:
        if pe.value(m.Installed_CHP[j]) == 1:
            for t in m.hours:
                # Main CHP operation
                m.c1.add(m.P_CHPG[j, t] >= m.P_CHPG_min[j])
                m.c1.add(m.P_CHPG[j, t] <= m.P_CHPG_max[j])
                m.c1.add(m.P_CHPE[j, t] == m.N_CHP_E_efficiency[j] * m.P_CHPG[j, t])



                m.c1.add(m.P_CHPH[j, t] <= m.P_loadCHP[j, t])
                m.c1.add(m.P_CHPH[j, t] == m.N_CHP_H_efficiency[j] * m.P_CHPG[j, t])

                # Reserves (Up and Down)
                m.c1.add(m.U_CHPG[j, t] >= 0)
                m.c1.add(m.U_CHPG[j, t] <= m.P_CHPG_max[j] - m.P_CHPG[j, t])
                m.c1.add(m.U_CHPE[j, t] == m.N_CHP_E_efficiency[j] * m.U_CHPG[j, t])
                m.c1.add(m.U_CHPH[j, t] == m.N_CHP_H_efficiency[j] * m.U_CHPG[j, t])

                m.c1.add(m.D_CHPG[j, t] >= 0)
                m.c1.add(m.D_CHPG[j, t] <= m.P_CHPG[j, t] - m.P_CHPG_min[j])
                m.c1.add(m.D_CHPE[j, t] == m.N_CHP_E_efficiency[j] * m.D_CHPG[j, t])
                m.c1.add(m.D_CHPH[j, t] == m.N_CHP_H_efficiency[j] * m.D_CHPG[j, t])

                # Flex constraints
                m.c1.add(m.U_CHPG[j, t] <= m.N_CHP_flexibility_coe[j] * m.P_CHPG_max[j])
                m.c1.add(m.D_CHPG[j, t] <= m.N_CHP_flexibility_coe[j] * m.P_CHPG_max[j])

        else:
          for t in m.hours:
            # Force all CHP-related variables to zero if not installed
            m.c1.add(m.P_CHPG[j, t] == 0)
            m.c1.add(m.P_CHPE[j, t] == 0)
            m.c1.add(m.P_CHPH[j, t] == 0)
            m.c1.add(m.U_CHPG[j, t] == 0)
            m.c1.add(m.U_CHPE[j, t] == 0)
            m.c1.add(m.U_CHPH[j, t] == 0)
            m.c1.add(m.D_CHPG[j, t] == 0)
            m.c1.add(m.D_CHPE[j, t] == 0)
            m.c1.add(m.D_CHPH[j, t] == 0)