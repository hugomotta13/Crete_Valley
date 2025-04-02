import pyomo.environ as pe


def define_wind_turbine_constraints(m):
    for j in m.building:
        if pe.value(m.Installed_WT[j]) == 1:
            P_nom = m.P_nominal[j]
            VI = m.VI[j]
            VR = m.VR[j]
            VO = m.VO[j]

            for t in m.hours:
                V = m.wind_speed[j, t]

                if V < VI or V >= VO:
                    m.c1.add(m.P_wind_E[j, t] <= 0)  # Sem geração
                elif VI <= V < VR:
                    m.c1.add(m.P_wind_E[j, t] <= (P_nom / (VR - VI)) * V + P_nom * (
                                1 - (VR / (VR - VI))))  # Crescimento linear
                elif VR <= V < VO:
                    m.c1.add(m.P_wind_E[j, t] <= P_nom)  # Potência nominal

                if V < VI or V >= VO:
                    m.c1.add(m.U_wind[j, t] == 0)  # Sem reserva ascendente se a turbina estiver desligada
                    m.c1.add(m.D_wind[j, t] == 0)
                elif VI <= V < VR:
                    m.c1.add(
                        m.U_wind[j, t] <= ((P_nom / (VR - VI)) * V + P_nom * (1 - (VR / (VR - VI)))) - m.P_wind_E[
                            j, t])  # Flexibilidade ascendente
                    m.c1.add(m.D_wind[j, t] <= m.P_wind_E[j, t])
                elif VR <= V < VO:
                    m.c1.add(m.U_wind[j, t] <= P_nom - m.P_wind_E[j, t])  # Flexibilidade ascendente
                    m.c1.add(m.D_wind[j, t] <= m.P_wind_E[j, t])

        else:
            for t in m.hours:
              m.c1.add(m.P_wind_E[j, t]==0)
              m.c1.add(m.U_wind[j, t] == 0)  # Sem reserva ascendente se a turbina estiver desligada
              m.c1.add(m.D_wind[j, t] == 0)