import pyomo.environ as pe
import pandas as pd
import os
from pyomo.environ import SolverFactory, value, SolverStatus, TerminationCondition
import math
from pyomo.environ import ConstraintList
import CHP_resource
import PV_resource
import HP_resource
import run_optimization_model
import output_model
import Storage_resource
import Electrolyzer_P2G_resource
import Hydrogen_Storage_resource
import Fuel_cell_resource
import Eletric_Vehicles_resource
import Wind_Turbine_resource
import Biomass_Boiler_resource


from data_loader import (
    get_resources,
    load_resources_params,
    Buildings_max_temp,
    Buildings_min_temp,
    Outside_temp,
    Heat_Gains_losses,
    Weather_forecasts,
    process_prices,
)

from create_variables import (
    define_all_variables,
)

from optimal_power_flow import(
    load_power_network_data,
    define_power_flow_parameters,
    export_results_to_excel,
    generate_plots_per_node,
    optimal_power_flow,
    #redistribuir_edificios,
)

def create_model(data, include_flow=True, penalize=True):
    # Create Pyomo model
    m = pe.ConcreteModel()
    m.c1 = ConstraintList()

    # Define sets and variables
    m.hours = pe.RangeSet(1, 24)
    m.extended_hours = pe.RangeSet(1, 25)
    all_building = set(data["Electrical load"].keys()) | \
                   set(data["Gas load"].keys()) | \
                   set(data["Heat load"].keys())
    m.building = pe.Set(initialize=list(all_building))



    network_data = load_power_network_data()
    m.node = pe.Set(initialize=set(network_data["building_to_node"].values()))

    # Mapping of buildings to nodes
    mapped_building_node = {int(k): v for k, v in network_data["building_to_node"].items()}
    m.building_node = pe.Param(m.building, initialize=mapped_building_node, within=m.node)

    # Network lines (From–To pairs)
    m.line = pe.Set(initialize=network_data["lines"], dimen=2)


    m.big_M = 1000
    # Load and process all necessary input data for the model, including resource parameters,
    # temperature data, heat gains/losses, weather forecasts, and price data
    load_resources_params(m, data)
    Buildings_max_temp(m, data)
    Buildings_min_temp(m, data)
    Outside_temp(m, data)
    Heat_Gains_losses(m, data)
    Weather_forecasts(m, data)
    process_prices(m, data)
    # Creation of all variables and constraints for each resource
    define_all_variables(m, data)
    # Define all the constraints for each resource in the model
    CHP_resource.define_chp_constraints(m)  # CHP
    PV_resource.define_pv_constraints(m) # PV
    HP_resource.define_hp_constraints(m) # HP
    Storage_resource.define_battery_constraints(m) # Storage
    Electrolyzer_P2G_resource.P2G_electrolyzer_constraints(m)  # P2G
    Hydrogen_Storage_resource.hydrogen_storage_constraints(m) #  Hydrogen Storage
    Fuel_cell_resource.fuel_cell_storage_constraints(m)   # FC
    Eletric_Vehicles_resource.define_Eletric_Vehicles_constraints(m)  # Ev
    Wind_Turbine_resource.define_wind_turbine_constraints(m)  # Wind Turbine
    Biomass_Boiler_resource.define_biomassas_boiler_constraints(m) # Biomass Boiler
    define_power_flow_parameters(m, network_data)
    run_optimization_model.run_optimization(m, include_flow=include_flow, penalize=penalize)  # Constraints and objective function
    output_path = os.path.join(os.getcwd(), "final_results_crete_valley.xlsx")  # Create the file in xlsx
    output_model.save_results_to_excel(m, output_file=output_path) # Save the results in Excel
    output_model.plot_results(m, output_folder="plot_result")  # Plot the graph for the electricity, gas,
    output_model.plot_initial_loads(m) # Initial loads
    output_model.plot_secondary_reserves_separate(m, list(m.hours), output_folder="plot_result/secondary_reserves") # Graphs of the secondary reserve band
    label_rede = "with network" if include_flow else "without network"
    output_model.plot_aggregated_secondary_reserves(m, output_folder="secondary_reserves", label_rede=label_rede)
    if include_flow:
        df_voltage, df_P_pu, df_current, df_Q_pu = export_results_to_excel(m)
        generate_plots_per_node(df_voltage, df_P_pu, df_current)  # Plot voltage, current, and active power graphs
    return m
