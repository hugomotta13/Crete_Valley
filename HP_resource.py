import pyomo.environ as pe


def define_hp_constraints(m):

    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_HP[j]) == 1:
                m.c1.add(
                    m.P_HP[j, t] >= (
                            (m.Min_Temperature[j, t] - m.Outside_Temperature[j, t]) / m.Thermal_Resistance[j]
                            - m.Heat_Gains_Losses[j, t]
                    ) / m.Efficiency_HP[j]
                )


            else:
                m.c1.add(m.P_HP[j, t] == 0)


    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_HP[j]) == 1:
                m.c1.add(
                    m.Theta_E[j, t + 1] ==
                    m.Thermal_Constant[j] * m.Theta_E[j, t] +
                    (1 - m.Thermal_Constant[j]) * (
                            m.Outside_Temperature[j, t] +
                            m.Thermal_Resistance[j] * m.Efficiency_HP[j] * m.P_HP[j, t]
                    ) +
                    m.Heat_Gains_Losses[j, t]
                )

                if t == 1:
                    m.c1.add(m.Theta_E[j, t] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_E[j, t] >= m.Min_Temperature[j, t])
                    m.c1.add(m.Theta_E[j, t + 1] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_E[j, t + 1] >= m.Min_Temperature[j, t])
                else:
                    m.c1.add(m.Theta_E[j, t + 1] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_E[j, t + 1] >= m.Min_Temperature[j, t])
            else:
               m.c1.add( m.Theta_E[j, t + 1]==0)

    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_HP[j]) == 1:
                # Upward reserves
                m.c1.add(m.U_HP[j, t] >= 0)
                m.c1.add(m.U_HP[j, t] <= 0.2 * m.P_HP[j, t])


                # Downward reserves
                m.c1.add(m.D_HP[j, t] >= 0)
                m.c1.add(m.D_HP[j, t] <= 0.2 * m.P_HP[j, t])

            else:
                m.c1.add(m.U_HP[j, t] == 0)
                m.c1.add(m.U_DH[j, t] == 0)


    for j in m.building:
        if pe.value(m.Installed_HP[j]) == 1:

            for t in m.hours:

                m.c1.add(
                    m.Theta_U[j, t + 1] ==
                    m.Thermal_Constant[j] * m.Theta_U[j, t] +
                    (1 - m.Thermal_Constant[j]) * (
                            m.Outside_Temperature[j, t] +
                            m.Thermal_Resistance[j] * (
                                    m.Efficiency_HP[j] * m.P_HP[j, t] -
                                    m.Efficiency_HP[j] * m.U_HP[j, t]
                            )
                    ) +
                    m.Heat_Gains_Losses[j, t]
                )
                if t == 1:
                    m.c1.add(m.Theta_U[j, t] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_U[j, t] >= m.Min_Temperature[j, t])
                    m.c1.add(m.Theta_U[j, t + 1] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_U[j, t + 1] >= m.Min_Temperature[j, t])
                else:
                    m.c1.add(m.Theta_U[j, t + 1] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_U[j, t + 1] >= m.Min_Temperature[j, t])

    for j in m.building:
        if pe.value(m.Installed_HP[j]) == 1:
            for t in m.hours:
                m.c1.add(
                    m.Theta_D[j, t + 1] ==
                    m.Thermal_Constant[j] * m.Theta_D[j, t] +
                    (1 - m.Thermal_Constant[j]) * (
                            m.Outside_Temperature[j, t] +
                            m.Thermal_Resistance[j] * (
                                    m.Efficiency_HP[j] * m.P_HP[j, t] +
                                    m.Efficiency_HP[j] * m.D_HP[j, t]
                            )
                    ) +
                    m.Heat_Gains_Losses[j, t]
                )
                if t == 1:
                    m.c1.add(m.Theta_D[j, t] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_D[j, t] >= m.Min_Temperature[j, t])
                    m.c1.add(m.Theta_D[j, t + 1] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_D[j, t + 1] >= m.Min_Temperature[j, t])
                else:
                    m.c1.add(m.Theta_D[j, t + 1] <= m.Max_Temperature[j, t])
                    m.c1.add(m.Theta_D[j, t + 1] >= m.Min_Temperature[j, t])
