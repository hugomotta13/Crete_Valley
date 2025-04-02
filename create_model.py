import pyomo.environ as pe
import pandas as pd
import os
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


def create_model(data):
    # Criar modelo Pyomo
    m = pe.ConcreteModel()
    m.c1 = ConstraintList()

    # Definir conjuntos e variáveis (exemplo)
    m.hours = pe.RangeSet(1, 24)
    m.extended_hours = pe.RangeSet(1, 25)
    all_building = set(data["Electrical load"].keys()) | \
                   set(data["Gas load"].keys()) | \
                   set(data["Heat load"].keys())

    m.building = pe.Set(initialize=list(all_building))
    m.big_M = 1000

    load_resources_params(m, data)
    Buildings_max_temp(m, data)
    Buildings_min_temp(m, data)
    Outside_temp(m, data)
    Heat_Gains_losses(m, data)
    Weather_forecasts(m, data)
    process_prices(m, data)

    define_all_variables(m, data)
    # Apply constraints for CHP resource based on the status of secondary reserves
    CHP_resource.define_chp_constraints(m)
    PV_resource.define_pv_constraints(m)
    HP_resource.define_hp_constraints(m)
    Storage_resource.define_battery_constraints(m)
    Electrolyzer_P2G_resource.P2G_electrolyzer_constraints(m)
    Hydrogen_Storage_resource.hydrogen_storage_constraints(m)
    Fuel_cell_resource.fuel_cell_storage_constraints(m)
    Eletric_Vehicles_resource.define_Eletric_Vehicles_constraints(m)
    Wind_Turbine_resource.define_wind_turbine_constraints(m)
    Biomass_Boiler_resource.define_biomassas_boiler_constraints(m)

    run_optimization_model.run_optimization(m)
    output_path = os.path.join(os.getcwd(), "final_results_crete_valley.xlsx")
    output_model.save_results_to_excel(m, output_file=output_path)
    output_model.plot_results(m, output_folder="plot_result")
    output_model.plot_initial_loads(m)
    output_model.plot_secondary_reserves_separate(m, list(m.hours), output_folder="plot_result/secondary_reserves")

    return m
