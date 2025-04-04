import pyomo.environ as pe


def define_biomassas_boiler_constraints(m):
    for j in m.building:
        if pe.value(m.Installed_BB[j]) == 1:
            for t in m.hours:
                # Set the fuel consumption range for the biomass boiler within the specified minimum and maximum limits
                m.c1.add(m.P_boiler_F[j, t] <= m.P_boiler_max_F[j] )
                m.c1.add(m.P_boiler_F[j, t] >= m.P_boiler_min_F[j] )

                # Heat generation from biomass based on the fuel consumption and efficiency
                m.c1.add(m.P_boiler_H[j, t] == m.eta_H[j] * m.P_boiler_F[j, t])
                m.c1.add(m.P_boiler_H[j, t] == m.eta_H[j] * m.P_boiler_F[j, t] )

                # Electricity generation from biomass based on the fuel consumption and efficiency
                m.c1.add(m.P_boiler_E[j, t] == m.eta_E[j] * m.P_boiler_F[j, t] )

                # if t > min(m.hours):
                #     m.c1.add(m.P_boiler_F[j, t] - m.P_boiler_F[j, t - 1] <= 15 )
                #     m.c1.add(m.P_boiler_F[j, t - 1] - m.P_boiler_F[j, t] <= 10 )

                # Define flexibility limits for biomass fuel, heat, and electricity generation
                m.c1.add(m.U_boiler_F[j, t] <= (m.P_boiler_F[j, t] - m.P_boiler_min_F[j]) )
                m.c1.add(m.D_boiler_F[j, t] <= 0.2 * (m.P_boiler_max_F[j] - m.P_boiler_F[j, t]) )
                m.c1.add(m.U_boiler_H[j, t] == m.eta_H[j] * m.U_boiler_F[j, t] )
                m.c1.add(m.D_boiler_H[j, t] == m.eta_H[j] * m.D_boiler_F[j, t] )
                m.c1.add(m.U_boiler_E[j, t] == m.eta_E[j] * m.U_boiler_F[j, t] )
                m.c1.add(m.D_boiler_E[j, t] == m.eta_E[j] * m.D_boiler_F[j, t] )

                m.c1.add(m.U_boiler_F[j, t] <= m.mi_biomass[j] * m.P_boiler_max_F[j])
                m.c1.add(m.D_boiler_F[j, t] <= m.mi_biomass[j] * m.P_boiler_max_F[j] )
        else:
            # Set all boiler-related variables to zero when the boiler is not installed
            for t in m.hours:
                 m.c1.add(m.P_boiler_F[j, t] ==0)
                 m.c1.add(m.P_boiler_H[j, t] == 0)
                 m.c1.add(m.P_boiler_E[j, t] == 0)
                 m.c1.add(m.U_boiler_H[j, t] == 0)
                 m.c1.add(m.D_boiler_H[j, t] == 0)
                 m.c1.add(m.U_boiler_E[j, t] == 0)
                 m.c1.add(m.D_boiler_E[j, t] == 0)
                 m.c1.add(m.U_boiler_F[j, t] <= 0)
                 m.c1.add(m.D_boiler_F[j, t] <= 0)