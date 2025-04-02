import pyomo.environ as pe


def define_Eletric_Vehicles_constraints(m):

    m.b_active = pe.Param(m.building, m.hours, initialize=0, mutable=True)

    for j in m.building:
        for t in m.hours:
            if pe.value(m.Installed_EV[j]) == 1:
                t_ar = pe.value(m.t_AR[j])
                t_de = pe.value(m.t_DE[j])

                # Define se o veículo está ativo nesse horário
                if t_ar <= t <= t_de:
                    m.b_active[j, t] = 1
                else:
                    m.b_active[j, t] = 0

                # Atualização do SOC
                m.c1.add(
                    m.SOC_EV_E[j, t + 1] == m.SOC_EV_E[j, t] +
                    (m.P_EV_E_charge[j, t] * m.eta_EV_up[j] - m.P_EV_E_discharge[j, t] / m.eta_EV_down[j]) * m.b_active[
                        j, t]
                )
                m.c1.add(m.SOC_EV_min[j] <= m.SOC_EV_E[j, t + 1])
                m.c1.add(m.SOC_EV_E[j, t + 1] <= m.SOC_EV_max[j])

                # Restrições de carga e descarga
                m.c1.add(m.P_EV_E_charge[j, t] <= m.P_EV_maxup[j] * m.b_active[j, t])
                m.c1.add(m.P_EV_E_discharge[j, t] <= m.P_EV_maxdown[j] * m.b_active[j, t])
                m.c1.add(m.P_EV_E_charge_dot[j, t] <= m.P_EV_maxup[j] * m.b_active[j, t])
                m.c1.add(m.P_EV_E_discharge_dot[j, t] <= m.P_EV_maxdown[j] * m.b_active[j, t])

                # Restrições adicionais
                m.c1.add(
                    m.P_EV_E_discharge[j, t] + m.P_EV_E_discharge_dot[j, t] <= (1 - m.b_EV_E[j, t]) * m.P_EV_maxdown[j])
                m.c1.add(m.P_EV_E_charge[j, t] + m.P_EV_E_charge_dot[j, t] <= m.b_EV_E[j, t] * m.P_EV_maxup[j])

                # Garantir não-negatividade
                m.c1.add(m.P_EV_E_discharge[j, t] >= 0)
                m.c1.add(m.P_EV_E_discharge_dot[j, t] >= 0)
                m.c1.add(m.P_EV_E_charge[j, t] >= 0)
                m.c1.add(m.P_EV_E_charge_dot[j, t] >= 0)

                # Restrições nos tempos de chegada e saída
                if t == t_ar:
                    m.c1.add(m.SOC_EV_E[j, t_ar] == m.SOC_EV_AR[j])
                if t == t_de:
                    m.c1.add(m.SOC_EV_E[j, t_de] >= m.SOC_EV_DE[j])
                    m.c1.add(m.U_EV_E_up[j, t] + m.U_EV_E_down[j, t] + m.D_EV_E_up[j, t] + m.D_EV_E_down[j, t] == 0)
                    m.c1.add(m.P_EV_E_discharge[j, t] == 0)
                    m.c1.add(m.P_EV_E_charge[j, t] == 0)

            else:
                # Se não há veículo instalado: tudo zerado
                m.b_active[j, t] = 0
                m.c1.add(m.SOC_EV_E[j, t + 1] == m.SOC_EV_E[j, t])
                m.c1.add(m.P_EV_E_charge[j, t] == 0)
                m.c1.add(m.P_EV_E_discharge[j, t] == 0)
                m.c1.add(m.b_EV_E[j, t] == 0)
                m.c1.add(m.P_EV_E_charge_dot[j, t] == 0)
                m.c1.add(m.P_EV_E_discharge_dot[j, t] == 0)
                m.c1.add(m.U_EV_E_up[j, t] == 0)
                m.c1.add(m.U_EV_E_down[j, t] == 0)
                m.c1.add(m.D_EV_E_up[j, t] == 0)
                m.c1.add(m.D_EV_E_down[j, t] == 0)

    for j in m.building:
        for t in m.hours:
            if m.Installed_EV[j] == 1:

                m.c1.add(0 <= m.U_EV_E_down[j, t])
                m.c1.add(m.U_EV_E_down[j, t] <=  (m.P_EV_maxdown[j] - m.P_EV_E_discharge[j, t])*m.b_active[j, t])


                m.c1.add(0 <= m.U_EV_E_up[j, t])
                m.c1.add(m.U_EV_E_up[j, t] <= m.P_EV_E_charge[j, t]*m.b_active[j, t])


                m.c1.add(0 <= m.D_EV_E_up[j, t])
                m.c1.add(m.D_EV_E_up[j, t] <=  (m.P_EV_maxup[j] - m.P_EV_E_charge[j, t])*m.b_active[j, t])


                m.c1.add(0 <= m.D_EV_E_down[j, t])
                m.c1.add(m.D_EV_E_down[j, t] <= m.P_EV_E_discharge[j, t]*m.b_active[j, t])


                m.c1.add(
                    (m.U_EV_E_down[j, t] / m.eta_EV_down[j] + m.U_EV_E_up[j, t] * m.eta_EV_up[j])
                    <= m.SOC_EV_E[j, t + 1] - m.SOC_EV_min[j]
                )


                m.c1.add(
                    (m.D_EV_E_down[j, t] / m.eta_EV_down[j] + m.D_EV_E_up[j, t] * m.eta_EV_up[j])
                    <= m.SOC_EV_max[j] - m.SOC_EV_E[j, t + 1]
                )
            else:
                m.c1.add( m.U_EV_E_down[j, t]==0)
                m.c1.add(m.U_EV_E_up[j, t]==0)

    first_hour = min(m.hours)
    for j in m.building:
            if m.Installed_EV[j] == 1:
                m.c1.add(m.U_EV_E_up[j, first_hour] == 0)
                m.c1.add(m.U_EV_E_down[j, first_hour] == 0)
                m.c1.add(m.D_EV_E_up[j, first_hour] == 0)
                m.c1.add(m.D_EV_E_down[j, first_hour] == 0)
            else:
                m.c1.add(m.U_EV_E_up[j, first_hour] == 0)
                m.c1.add(m.U_EV_E_down[j, first_hour] == 0)
                m.c1.add(m.D_EV_E_up[j, first_hour] == 0)
                m.c1.add(m.D_EV_E_down[j, first_hour] == 0)

    for j in m.building:
        for t in m.hours:
            if m.Installed_EV[j] == 1:
                m.c1.add(
                    m.U_EV_E_up[j, t] + m.U_EV_E_down[j, t] + m.D_EV_E_up[j, t] + m.D_EV_E_down[j, t]
                    <= (m.P_EV_E_charge_dot[j, t + 1] + m.P_EV_E_discharge_dot[j, t + 1])
                )

                m.c1.add(
                    m.U_EV_E_up[j, t] + m.U_EV_E_down[j, t] + m.D_EV_E_up[j, t] + m.D_EV_E_down[j, t]
                    <= m.b_EV_E_dot[j, t] * m.big_M
                )

                m.c1.add(
                    m.P_EV_E_charge_dot[j, t] + m.P_EV_E_discharge_dot[j, t]
                    <= (1 - m.b_EV_E_dot[j, t]) * m.big_M
                )
                if t >= m.t_DE[j]:
                    m.c1.add(m.SOC_EV_E[j, t] >= m.SOC_EV_DE[j])
                    m.c1.add(m.U_EV_E_up[j, t] + m.U_EV_E_down[j, t] + m.D_EV_E_up[j, t] + m.D_EV_E_down[j, t] == 0)
                    m.c1.add(m.P_EV_E_discharge[j, t] == 0)
                    m.c1.add(m.P_EV_E_charge[j, t] == 0)
            else:
                m.c1.add( m.U_EV_E_up[j, t] + m.U_EV_E_down[j, t] + m.D_EV_E_up[j, t] + m.D_EV_E_down[j, t]==0)
                if t >= m.t_DE[j]:
                    m.c1.add(m.SOC_EV_E[j, t] ==0)
                    m.c1.add(m.U_EV_E_up[j, t] + m.U_EV_E_down[j, t] + m.D_EV_E_up[j, t] + m.D_EV_E_down[j, t] == 0)
                    m.c1.add(m.P_EV_E_discharge[j, t] == 0)
                    m.c1.add(m.P_EV_E_charge[j, t] == 0)