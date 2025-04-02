import pyomo.environ as pe
from data_loader import get_resources
import pandas as pd
def   define_electric_load(m,data):

    m.P_ILE = pe.Param(m.building, m.hours,
                                initialize={(b, h): data["Electrical load"][b][h]
                                            for b in data["Electrical load"]
                                            for h in data["Electrical load"][b]},
                                within=pe.NonNegativeReals)
    return  m

def define_chp_variables(m,data):
    m.P_loadCHP = pe.Param(
        m.building, m.hours,
        initialize={(b, h): data["Gas load"][b][h] for b in data["Gas load"] for h in data["Gas load"][b]},
        within=pe.NonNegativeReals,
        mutable=True
    )
    m.Installed_CHP = pe.Param(m.building, initialize=data["CHP"]["Installed (0-no,1-yes)"],
                              within=pe.Binary, mutable=False)
    m.P_CHPE = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals, initialize=0)  # CHP Electric power generation
    m.P_CHPH = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)
    m.U_CHPE = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)  # CHP Electric power increase
    m.U_CHPH = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)  # CHP Heat power increase
    m.U_CHPG = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals, initialize=0)  # CHP Gas power increase
    m.D_CHPG = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)  # CHP Gas power decrease
    m.D_CHPE = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)  # CHP Electric power decrease
    m.D_CHPH = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)  # CHP Heat power decrease

    m.N_CHP_E_efficiency = pe.Param(m.building, initialize=data["CHP"]["CHP electricity efficiency"],
                              within=pe.NonNegativeReals)
    m.N_CHP_H_efficiency= pe.Param(m.building, initialize=data["CHP"]["CHP heat efficiency"],
                              within=pe.NonNegativeReals)
    m.P_CHPG_min = pe.Param(m.building, initialize=data["CHP"]["Minimum CHP power (kW)"],
                              within=pe.NonNegativeReals)
    m.P_CHPG_max =pe.Param(m.building, initialize=data["CHP"]["Maximum CHP power (kW)"],
                              within=pe.NonNegativeReals)
    m.N_CHP_flexibility_coe =pe.Param(m.building, initialize=data["CHP"]["CHP flexibility coefficient"],
                              within=pe.NonNegativeReals)
    m.P_ILG = pe.Param(
        m.building, m.hours,
        initialize=lambda m, b, h: 0.3 * m.P_loadCHP[b, h],
        within=pe.NonNegativeReals
    )

    def chp_bounds(m, j, t):
        return (m.P_CHPG_min[j], m.P_CHPG_max[j])

    m.P_CHPG = pe.Var(m.building, m.hours, bounds=chp_bounds, domain=pe.NonNegativeReals)

    return m

def define_heat_pump_variables(m,data):


    m.Installed_HP=pe.Param(m.building, initialize=data["Heat Pump"]["Installed (0-no,1-yes)"],within=pe.Binary, mutable=False)
    m.Thermal_Capacitance = pe.Param(m.building, initialize=data["Heat Pump"]["C (kWh/ºC)"], within=pe.NonNegativeReals)
    m.Thermal_Resistance=   pe.Param(m.building, initialize=data["Heat Pump"]["R (ºC/kWh)"], within=pe.NonNegativeReals)
    m.Delta_t= pe.Param(m.building, initialize=data["Heat Pump"]["delta_t"], within=pe.NonNegativeReals)


    m.P_HP_min =pe.Param(m.building, initialize=data["Heat Pump"]["Minimum heat pump power (kW)"], within=pe.NonNegativeReals)


    m.P_HP_max =pe.Param(m.building, initialize=data["Heat Pump"]["Maximum heat pump power (kW)"], within=pe.NonNegativeReals)
    def thermal_constant_rule(m, b):
        if pe.value(m.Installed_HP[b]) == 0:
            return 0  # Se o prédio não tem HP, retorna 0

        # Garantindo que todos os valores sejam numéricos antes da multiplicação
        delta_t = pe.value(m.Delta_t[b])
        capacitance = pe.value(m.Thermal_Capacitance[b])
        resistance = pe.value(m.Thermal_Resistance[b])

        return delta_t / (capacitance * resistance)

    m.Thermal_Constant = pe.Expression(m.building, rule=thermal_constant_rule)

    m.Efficiency_HP =  pe.Param(m.building, initialize=data["Heat Pump"]["Efficiency HP"], within=pe.NonNegativeReals)
    m.Min_Temperature = pe.Param(
        m.building, m.hours,
        initialize={(b, h): data["inside_min_temp"][b][h] for b in m.building for h in m.hours},
        within=pe.Reals
    )
    m.Max_Temperature=pe.Param(
        m.building, m.hours,
        initialize={(b, h): data["inside_max_temp"][b][h] for b in m.building for h in m.hours},
        within=pe.Reals)
    m.Outside_Temperature = pe.Param(
        m.building, m.hours,
        initialize={(b, h): data["outside_temp"][b][h] for b in m.building for h in m.hours},
        within=pe.Reals)
    m.Heat_Gains_Losses= pe.Param(
        m.building, m.hours,
        initialize={(b, h): data["loss_temp"][b][h] for b in m.building for h in m.hours},
        within=pe.Reals)
    m.N_HP_efficiency =pe.Param(m.building, initialize=data["Heat Pump"]["Heat pump efficiency (COP)"], within=pe.NonNegativeReals)
    m.heat_load =pe.Param(m.building, m.hours,
                                initialize={(b, h): data["Heat load"][b][h]
                                            for b in data["Heat load"]
                                            for h in data["Heat load"][b]},
                                within=pe.NonNegativeReals)
    m.P_DH_max = pe.Param(m.building, initialize=data["District Heating"]["Maximum district heating power (kW)"], within=pe.NonNegativeReals)
    m.P_DH_min =pe.Param(m.building, initialize=data["District Heating"]["Minimum district heating power (kW)"], within=pe.NonNegativeReals)
    m.P_ILH = pe.Param(
        m.building, m.hours,
        initialize=lambda m, b, h: 0.3 * m.heat_load[b, h],
        within=pe.NonNegativeReals
    )
    m.P_DH =  pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)
    m.U_DH = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)
    m.D_DH = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)
    m.P_HP = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)
    m.U_HP = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)
    m.D_HP = pe.Var(m.building,  m.hours, domain=pe.NonNegativeReals)
    m.Theta_E = pe.Var(m.building, m.extended_hours, within=pe.Reals, initialize=0)  # Building temperature
    m.Theta_U = pe.Var(m.building, m.extended_hours, within=pe.Reals, initialize=0)  # Positive temperature deviation
    m.Theta_D = pe.Var(m.building, m.extended_hours, within=pe.Reals, initialize=0)  # Negative temperature deviation

    # print("\n--- Checando m.Outside_Temperature ---")
    # for b in m.building:
    #     for h in m.hours:
    #         print(f"Building {b}, Hour {h}: {m.Outside_Temperature[b, h]}")
    # print("--- Fim da checagem ---\n")


    return m


def define_pv_variables(m, data):
    """Define variables and parameters for PV systems."""

    # Define PV-related variables

    m.P_PV = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # PV power generation
    m.U_PV = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # PV power up
    m.D_PV = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # PV power down

    # Define PV-related parameters
    m.Installed_PV = pe.Param(m.building, initialize=data["PV"]["Installed (0-no,1-yes)"],
                              within=pe.Binary, mutable=False)
    m.PV_max = pe.Param(
        m.building,
        initialize={b: data["PV"]["Max power (kW)"][b] for b in m.building},
        within=pe.NonNegativeReals
    )
    m.alpha = pe.Param(
        m.building, m.hours,
        initialize={(b, t): data["weather_forecasts"]["solar_profile"][t - 1]
                    for b in m.building
                    for t in m.hours},
        default=0
    )

    # print("\n--- PV Generation Profile (m.P_pv) ---")
    # for b in m.building:
    #     for t in m.hours:
    #         print(f"Building {b}, Hour {t}: PV_max = {pe.value(m.PV_max[b])}, alpha = {pe.value(m.alpha[b, t])}")
    # print("--- Fim dos dados ---\n")

    return m


def define_price_parameters(m, data):
    """Define price-related parameters and variables."""

    # Define price-related parameters
    m.electricity_price = pe.Param(m.hours,initialize={t: data["prices"]["Electricity energy"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.natural_gas_price = pe.Param(m.hours,initialize={t: data["prices"]["Gas energy"][t] for t in m.hours},
                                       within=pe.NonNegativeReals)  # Natural gas price




    m.lambda_s_price = pe.Param(m.hours,initialize={t: data["prices"]["Electricity energy"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_B = pe.Param(m.hours,initialize={t: data["prices"]["Secondary band"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_UE = pe.Param(m.hours,initialize={t: data["prices"]["Secondary up"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_DE = pe.Param(m.hours,initialize={t: data["prices"]["Secondary down"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.phi_D= pe.Param(m.hours,initialize={t: data["prices"]["Secondary ratio down"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.phi_U = pe.Param(m.hours,initialize={t: data["prices"]["Secondary ratio up"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_UG= pe.Param(m.hours,initialize={t: data["prices"]["Gas secondary down"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_DG= pe.Param(m.hours,initialize={t: data["prices"]["Gas secondary up"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_BB=pe.Param(m.hours,initialize={t: data["prices"]["Biomass"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_UB=pe.Param(m.hours,initialize={t: data["prices"]["Biomass seconday up"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.lambda_DB =pe.Param(m.hours,initialize={t: data["prices"]["Biomass seconday dpwn"][t] for t in m.hours},
                                   within=pe.NonNegativeReals)
    m.water_price=pe.Param( initialize=data["prices"]["water"][1])
    m.green_hydrogen =pe.Param( initialize=data["prices"]["green hydrogen"][1])
    m.factor_water=pe.Param( initialize=data["prices"]["Conversion factor for water"][1])
    m.hydrogen_imbalance=pe.Param( initialize=data["prices"]["green hydrogen imbalance"][1])


    return m


def define_battery_variables(m, data):
    """Defines variables and parameters for battery systems."""

    # Defining battery-related parameters
    # Installed status (0 = no, 1 = yes)
    m.Installed_ESS = pe.Param(m.building, initialize=data["Storage"]["Installed (0-no,1-yes)"],
                               within=pe.Binary, mutable=False)

    # State of Charge (SOC) parameters
    m.SOC_Sto_E_max = pe.Param(m.building, initialize=data["Storage"]["Max SOC (kWh)"],
                               within=pe.NonNegativeReals)  # Maximum SOC
    m.SOC_Sto_E_min = pe.Param(m.building, initialize=data["Storage"]["Min SOC (kWh)"],
                               within=pe.NonNegativeReals)  # Minimum SOC
    m.SOC_Sto_E_0 = pe.Param(m.building, initialize=data["Storage"]["Initial SOC (kWh)"],
                             within=pe.NonNegativeReals)  # Initial SOC
    # Power parameters
    m.P_Sto_max = pe.Param(m.building, initialize=data["Storage"]["Max power (kW)"],
                           within=pe.NonNegativeReals)  # Max charge power
    m.P_Sto_min = pe.Param(m.building, initialize=data["Storage"]["Min power(kW)"],
                           within=pe.NonNegativeReals)  # Min discharge power
    # Efficiency
    m.eta_Sto_E_plus = pe.Param(m.building, initialize=data["Storage"]["Efficiency"],
                                within=pe.NonNegativeReals)  # Charge efficiency
    m.eta_Sto_E_minus = pe.Param(m.building, initialize=data["Storage"]["Efficiency"],
                                 within=pe.NonNegativeReals)  # Discharge efficiency


    # Defining state of charge variable with bounds
    def SOC_bounds(m, b, h):
        return (m.SOC_Sto_E_min[b], m.SOC_Sto_E_max[b])
    m.SOC = pe.Var(m.building, m.extended_hours, bounds=SOC_bounds)  # State of charge variable
    # Charge and discharge power variables
    m.P_charge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # Charge power
    m.P_charge_plus = pe.Var(m.building, m.extended_hours, within=pe.NonNegativeReals)  # Charge power increase
    m.P_discharge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # Discharge power
    m.P_discharge_plus = pe.Var(m.building, m.extended_hours, within=pe.NonNegativeReals)  # Discharge power increase
    # Operation mode (binary: charging/discharging)
    m.operation_mode = pe.Var(m.building, m.hours, within=pe.Binary)
    # Reserve up and down variables
    m.U_reserve_charge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # Upward reserve for charging
    m.U_reserve_discharge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # Upward reserve for discharging
    m.D_reserve_charge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # Downward reserve for charging
    m.D_reserve_discharge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)  # Downward reserve for discharging



    return m

def define_objective_function_variables(m):
    m.Fe_electric_cost = pe.Var(m.hours, domain=pe.Reals)
    m.Fe= pe.Var(m.hours, domain=pe.Reals)
    m.Fg_gas_cost = pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.Fg=pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.F_H2=pe.Var(m.hours, domain=pe.Reals)
    m.F_H2O =pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.F_O2=pe.Var(m.hours, domain=pe.Reals)
    m.F_Boiler =pe.Var(m.hours, domain=pe.Reals)
    m.E_E = pe.Var( m.hours, domain=pe.Reals)
    m.E_G = pe.Var( m.hours, domain=pe.Reals)
    m.E_H = pe.Var( m.hours, domain=pe.NonNegativeReals)
    m.E_H2 = pe.Var( m.hours, domain=pe.NonNegativeReals)
    m.E_B = pe.Var( m.hours, domain=pe.Reals)
    m.U_E = pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.D_E = pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.U_G=  pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.D_G = pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.U_H2= pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.D_H2 = pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.U_B  = pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.D_B = pe.Var(m.hours, domain=pe.NonNegativeReals)
    m.F_reserve=pe.Var(m.hours, domain=pe.Reals)


    return m

def define_hydrogen_variables(m, data):
    # parameters
    m.Installed_HSS = pe.Param(m.building, initialize=data["Hydrogen Storage"]["Installed (0-no,1-yes)"],
                               within=pe.Binary, mutable=False)
    m.SOC_Sto_H2_0 =  pe.Param(m.building, initialize=data["Hydrogen Storage"]["Initial Sto SOC (kWh)"],
                              within=pe.NonNegativeReals)
    m.SOC_H2_min =  pe.Param(m.building, initialize=data["Hydrogen Storage"]["Min Sto SOC (kWh)"],
                              within=pe.NonNegativeReals)
    m.SOC_H2_max =  pe.Param(m.building, initialize=data["Hydrogen Storage"]["Max Sto SOC (kWh)"],
                              within=pe.NonNegativeReals)
    m.eta_H2_plus = pe.Param(m.building, initialize=data["Hydrogen Storage"]["Sto Charge Efficiency"],
                              within=pe.NonNegativeReals)
    m.eta_H2_minus = pe.Param(m.building, initialize=data["Hydrogen Storage"]["Sto Discharge Efficiency"],
                              within=pe.NonNegativeReals)
    m.P_Sto_H2_max_up = pe.Param(m.building, initialize=data["Hydrogen Storage"]["Max Sto Charge Power(kW)"],
                              within=pe.NonNegativeReals)
    m.P_Sto_H2_max_down = pe.Param(m.building, initialize=data["Hydrogen Storage"]["Max Sto Discharge Power(kW)"],
                              within=pe.NonNegativeReals)
    m.gamma_H2 =  pe.Param(m.building, initialize=data["Hydrogen Storage"]["Sto Self-discharge Rate"],
                              within=pe.NonNegativeReals)

    print("\n--- Hydrogen Storage Parameters ---")
    for b in m.building:
        print(f"Building {b}:")
        print(f"  Installed_HSS         = {pe.value(m.Installed_HSS[b])}")
        print(f"  SOC_Sto_H2_0          = {pe.value(m.SOC_Sto_H2_0[b])}")
        print(f"  SOC_H2_min            = {pe.value(m.SOC_H2_min[b])}")
        print(f"  SOC_H2_max            = {pe.value(m.SOC_H2_max[b])}")
        print(f"  eta_H2_plus           = {pe.value(m.eta_H2_plus[b])}")
        print(f"  eta_H2_minus          = {pe.value(m.eta_H2_minus[b])}")
        print(f"  P_Sto_H2_max_up       = {pe.value(m.P_Sto_H2_max_up[b])}")
        print(f"  P_Sto_H2_max_down     = {pe.value(m.P_Sto_H2_max_down[b])}")
        print(f"  gamma_H2              = {pe.value(m.gamma_H2[b])}")
    print("--- Fim dos parâmetros de Hydrogen Storage ---\n")

    # variables
    def SOC_H2_bounds(m, j, t):
        return (m.SOC_H2_min[j], m.SOC_H2_max[j])

    m.SOC_H2 = pe.Var(m.building, m.extended_hours, bounds=SOC_H2_bounds)
    m.P_Sto_charge_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_Sto_discharge_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_reserve_up_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_reserve_up_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_reserve_down_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_reserve_down_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.mode_charge_H2 = pe.Var(m.building, m.hours, within=pe.Binary)
    m.mode_discharge_H2 = pe.Var(m.building, m.hours, within=pe.Binary)
    m.P_Sto_H2_up = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_Sto_H2_down = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_Sto_load_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_Sto_Net_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    return m


def define_electrolyzer_P2G_variables(m, data):
    #parameters

    m.Installed_P2G = pe.Param(m.building, initialize=data["Electrolyzer P2G"]["Installed (0-no,1-yes)"],
                               within=pe.Binary, mutable=False)
    m.eta_P2G = pe.Param(m.building, initialize=data["Electrolyzer P2G"]["Efficiency"],
                               within=pe.NonNegativeReals)
    m.P2G_E_min = pe.Param(m.building, initialize=data["Electrolyzer P2G"]["Min power (kW)"],
                               within=pe.NonNegativeReals)
    m.P2G_E_max = pe.Param(m.building, initialize=data["Electrolyzer P2G"]["Max power (kW)"],
                               within=pe.NonNegativeReals)
    # m.P2G_Load_H2 = pe.Param(P2G_ids, initialize=P2G_Load_H2_dict)

    # print("\n--- Verificando parâmetros do Eletrólise P2G ---")
    # for b in m.building:
    #     print(f"Edifício {b}:")
    #     print(f"  Installed_P2G = {pe.value(m.Installed_P2G[b])}")
    #     print(f"  eta_P2G       = {pe.value(m.eta_P2G[b])}")
    #     print(f"  P2G_E_min     = {pe.value(m.P2G_E_min[b])}")
    #     print(f"  P2G_E_max     = {pe.value(m.P2G_E_max[b])}")
    # print("--- Fim da verificação ---\n")

    #variables
    m.P2G_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P2G_E = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P2G_Net_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P2G_Sto_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_P2G_E = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_P2G_E = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_P2G_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_P2G_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_P2G_Sto_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_P2G_Sto_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_P2G_Net_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_P2G_Net_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    return m


def define_fuel_cell_variables(m, data):
    #parameters
    m.Installed_FC = pe.Param(m.building, initialize=data["Fuel Cell"]["Load (0-no,1-yes)"],
                               within=pe.Binary, mutable=False)
    m.eta_FC =  pe.Param(m.building, initialize=data["Fuel Cell"]["Efficiency"],
                               within=pe.NonNegativeReals)
    m.P_FC_H2_max = pe.Param(m.building, initialize=data["Fuel Cell"]["Max power (kW)"],
                               within=pe.NonNegativeReals)

    #variables

    m.P_FC_E = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_Sto_FC_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_Sto_FC_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_Sto_FC_H2 = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_FC_E = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_FC_E = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)

    # print("\n--- Verificando parâmetros da Fuel Cell ---")
    # for b in m.building:
    #     print(f"Edifício {b}:")
    #     print(f"  Installed_FC   = {pe.value(m.Installed_FC[b])}")
    #     print(f"  eta_FC         = {pe.value(m.eta_FC[b])}")
    #     print(f"  P_FC_H2_max    = {pe.value(m.P_FC_H2_max[b])}")
    # print("--- Fim da verificação ---\n")

    return m

def define_electric_vehicle_variables(m, data):
    m.SOC_EV_E = pe.Var(m.building, m.extended_hours, within=pe.NonNegativeReals)
    m.P_EV_E_charge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_EV_E_discharge = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_EV_E_charge_dot = pe.Var(m.building, m.extended_hours, within=pe.NonNegativeReals)
    m.P_EV_E_discharge_dot = pe.Var(m.building, m.extended_hours, within=pe.NonNegativeReals)
    m.U_EV_E_up= pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_EV_E_up= pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_EV_E_down= pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_EV_E_down= pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.b_EV_E= pe.Var(m.building, m.hours, within=pe.Binary)
    m.b_EV_E_dot=pe.Var(m.building, m.hours, within=pe.Binary)

    #parameters
    m.Installed_EV = pe.Param(m.building, initialize=data["Electric vehicle"]["Installed (0-no,1-yes)"],
                              within=pe.Binary, mutable=False)
    m.P_EV_maxup = pe.Param(m.building, initialize=data["Electric vehicle"]["Max EV power (kW)"])
    m.P_EV_maxdown = pe.Param(m.building, initialize=data["Electric vehicle"][
        "Min EV power (kW)"])
    m.SOC_EV_0 = pe.Param(m.building, initialize=data["Electric vehicle"]["Initial EV SOC(kWh)"])
    m.SOC_EV_min = pe.Param(m.building, initialize=data["Electric vehicle"]["Min EV SOC (kW)"])
    m.SOC_EV_max = pe.Param(m.building, initialize=data["Electric vehicle"]["Max EV SOC (kW)"])
    m.eta_EV_up = pe.Param(m.building, initialize=data["Electric vehicle"]["EV Charging Efficiency"])
    m.eta_EV_down = pe.Param(m.building, initialize=data["Electric vehicle"]["EV Discharging Efficiency"])
    m.SOC_EV_AR = pe.Param(m.building, initialize=data["Electric vehicle"]["EV Arrival SOC"])
    m.SOC_EV_DE = pe.Param(m.building, initialize=data["Electric vehicle"]["EV Departure SOC"])
    m.t_AR = pe.Param(m.building, initialize=data["Electric vehicle"]["EV Arrival time"])
    m.t_DE = pe.Param(m.building, initialize=data["Electric vehicle"]["EV Departure Time"])
    # print("\n--- Parâmetros dos Veículos Elétricos ---")
    # for ev in m.building:
    #     print(f"\nVeículo: {ev}")
    #     print(f"  P_EV_maxup       = {pe.value(m.P_EV_maxup[ev])}")
    #     print(f"  P_EV_maxdown     = {pe.value(m.P_EV_maxdown[ev])}")
    #     print(f"  SOC_EV_0         = {pe.value(m.SOC_EV_0[ev])}")
    #     print(f"  SOC_EV_min       = {pe.value(m.SOC_EV_min[ev])}")
    #     print(f"  SOC_EV_max       = {pe.value(m.SOC_EV_max[ev])}")
    #     print(f"  eta_EV_up        = {pe.value(m.eta_EV_up[ev])}")
    #     print(f"  eta_EV_down      = {pe.value(m.eta_EV_down[ev])}")
    #     print(f"  SOC_EV_AR        = {pe.value(m.SOC_EV_AR[ev])}")
    #     print(f"  SOC_EV_DE        = {pe.value(m.SOC_EV_DE[ev])}")
    #     print(f"  t_AR             = {pe.value(m.t_AR[ev])}")
    #     print(f"  t_DE             = {pe.value(m.t_DE[ev])}")
    #     print(f"  big_M            = {pe.value(m.big_M[ev])}")
    # print("\n--- Fim dos parâmetros ---\n")

    return m

def define_wind_turbine_variables(m,data):
    m.Installed_WT = pe.Param(m.building, initialize=data["Wind Turbine"]["Installed (0-no,1-yes)"],
                              within=pe.Binary, mutable=False)
    m.wind_speed  = pe.Param(
        m.building, m.hours,
        initialize={(b, t): data["weather_forecasts"]["wind_speed"][t - 1]
                    for b in m.building if pe.value( m.Installed_WT[b]) == 1
                    for t in m.hours},
        default=0) # Define 0 para edifícios sem PV instalado
    m.P_nominal = pe.Param(m.building, initialize=data["Wind Turbine"]["Max Wind Turbine Power(kW)"],
                              within=pe.NonNegativeReals)
    m.VI =pe.Param(m.building, initialize=data["Wind Turbine"]["Cut-in Wind Speed"],
                              within=pe.NonNegativeReals)
    m.VO = pe.Param(m.building, initialize=data["Wind Turbine"]["Cut-out Wind Speed "],
                              within=pe.NonNegativeReals)
    m.VR = pe.Param(m.building, initialize=data["Wind Turbine"]["Rated Wind Speed"],
                              within=pe.NonNegativeReals)
    # print("\n--- Parâmetros das Turbinas Eólicas ---")
    # for b in m.building:
    #     print(f"\nEdifício: {b}")
    #     print(f"  Installed_WT = {pe.value(m.Installed_WT[b])}")
    #     print(f"  P_nominal    = {pe.value(m.P_nominal[b])}")
    #     print(f"  VI (cut-in)  = {pe.value(m.VI[b])}")
    #     print(f"  VO (cut-out) = {pe.value(m.VO[b])}")
    #     print(f"  VR (rated)   = {pe.value(m.VR[b])}")
    #     print("  Wind speed profile:")
    #     for t in m.hours:
    #         print(f"    Hour {t}: {pe.value(m.wind_speed[b, t])}")
    # print("\n--- Fim dos parâmetros das turbinas eólicas ---\n")

    m.P_wind_E= pe.Var(m.building, m.hours,within=pe.NonNegativeReals )
    m.U_wind=pe.Var(m.building, m.hours,within=pe.NonNegativeReals )
    m.D_wind=pe.Var(m.building, m.hours,within=pe.NonNegativeReals)
    return m


def define_biomass_boiler(m,data):
    m.Installed_BB = pe.Param(m.building, initialize=data["Biomass Boiler"]["Installed (0-no,1-yes)"],
                              within=pe.Binary, mutable=False)
    m.eta_H = pe.Param(m.building, initialize=data["Biomass Boiler"]["Biomass Heat Efficiency"],
                              within=pe.NonNegativeReals)
    m.eta_E = pe.Param(m.building, initialize=data["Biomass Boiler"]["Biomass Electricity Efficiency"],
                              within=pe.NonNegativeReals)
    m.P_boiler_min_F =pe.Param(m.building, initialize=data["Biomass Boiler"]["Min Biomass Consumption"],
                              within=pe.NonNegativeReals)
    m.P_boiler_max_F =pe.Param(m.building, initialize=data["Biomass Boiler"]["Max Biomass Consumption"],
                              within=pe.NonNegativeReals)
    m.mi_biomass =pe.Param(m.building, initialize=data["Biomass Boiler"]["Biomass Flexibility Factor"],
                              within=pe.NonNegativeReals)

    m.P_boiler_H = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_boiler_F =pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.P_boiler_E = pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_boiler_F= pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_boiler_E =pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.U_boiler_H =pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_boiler_F =pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_boiler_E =pe.Var(m.building, m.hours, within=pe.NonNegativeReals)
    m.D_boiler_H =pe.Var(m.building, m.hours, within=pe.NonNegativeReals)

    # print("\n--- Biomass Boiler Parameters ---")
    # for b in m.building:
    #     print(f"Building: {b}")
    #     print(f"  Installed_BB     = {pe.value(m.Installed_BB[b])}")
    #     print(f"  eta_H            = {pe.value(m.eta_H[b])}")
    #     print(f"  eta_E            = {pe.value(m.eta_E[b])}")
    #     print(f"  P_boiler_min_F   = {pe.value(m.P_boiler_min_F[b])}")
    #     print(f"  P_boiler_max_F   = {pe.value(m.P_boiler_max_F[b])}")
    #     print(f"  mi_biomass       = {pe.value(m.mi_biomass[b])}")
    # print("--- End Biomass Boiler Parameters ---\n")

    return m


def define_all_variables(m, data):
    define_electric_load(m, data)
    define_chp_variables(m, data)
    define_heat_pump_variables(m, data)
    define_pv_variables(m, data)
    define_price_parameters(m, data)
    define_battery_variables(m, data)
    define_objective_function_variables(m)
    define_hydrogen_variables(m, data)
    define_electrolyzer_P2G_variables(m, data)
    define_fuel_cell_variables(m, data)
    define_electric_vehicle_variables(m, data)
    define_wind_turbine_variables(m, data)
    define_biomass_boiler(m, data)
    return m