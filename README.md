# # Crete Valley – Energy Aggregator Optimization Model


##  Project Overview

This study aims to develop an optimization model to minimize operational costs for an energy aggregator, considering transactions of electricity, gas, green hydrogen, and CO₂ in the daily forecast electricity market.

The model's objective function includes:
- Costs associated with buying and selling electrical energy
- Secondary reserve transactions
- Gas and hydrogen transactions
- Revenues from selling oxygen

The model is structured to optimize these variables simultaneously, allowing the aggregator to reduce costs while maximizing its revenues.

Additionally, the model incorporates various energy resources such as:
- **Solar panels (PV)**
- **Heat pumps (HP)**
- **Combined heat and power units (CHP)**
- **Battery energy storage systems (ESS)**
- **Hydrogen storage**
- **P2G Electrolyzers (Power to Gas)**
- **Fuel cells**
- **Electric vehicles (EVs)**
- **Biomass boilers**
- **Wind turbines**

These resources are modeled considering their technical characteristics, operational constraints, interdependencies, and their ability to provide flexibility to the aggregator.

---

## 📁 Input Data Instructions

### File: `Input Data-Resources 1.xlsx`

#### 1. Load Data Tabs
- **Electric**: Contains the electrical loads  
- **Gas**: Contains the gas loads  
- **Thermal Load (Heat Load)**: Contains the thermal loads  

#### 2. `"Buildings_Resources"` Tab
- The **"Installed"** field (`0` = No, `1` = Yes) indicates whether the resource is installed.  
- Buildings with a **P2G Electrolyzer** must also have **Hydrogen Storage** installed, as their equations are interconnected.  
- Pay special attention to buildings with **Heat Pumps (HP)** installed, as other tabs are interconnected with this resource.  

#### 3. Temperature and Heat Loss Tabs
- In the tabs `Buildings_Max Temperature`, `Buildings_Min Temperature`, `Outside Temperature`, and `Heat_Gains_Losses`, buildings with HP installed must have the temperatures correctly filled in.  
- For buildings **without HP installed**, the temperatures should be set to **zero**.

---

### File: `Input Data-Other.xlsx`

#### 1. Climate Forecasts and Prices Tabs
- **Weather Forecasts**: Contains data on the **solar profile** and **wind speed**
- **Prices**: Contains values for:
  - Electrical energy  
  - Gas energy  
  - Secondary reserve bands (upward, downward, and their ratios)  
  - Biomass (including secondary reserve bands)  
  - Water  
  - Green hydrogen  
  - Conversion and imbalance factors for **water** and **green hydrogen**

---

##  Program Structure

### 🔧 Main Modules

| Module                  | Description                                                     |
|-------------------------|-----------------------------------------------------------------|
| `main.py`               | Executes the main script                                        |
| `create_model.py`       | Defines the optimization model and calls associated functions   |
| `run_optimization_model.py` | Defines constraints, objective function, and solver          |
| `data_loader.py`        | Processes input data                                            |
| `create_variables.py`   | Defines variables and parameters required by the model          |
| `output_model.py`       | Saves results to Excel, including plots of electrical, gas, hydrogen, and reserve data |

---

###  Resource-Specific Modules

Each resource has its own module containing the modeling equations and constraints, as listed below:

| Python File                     | Description                                 |
|--------------------------------|---------------------------------------------|
| `Biomass_Boiler_resource.py`   | Modeling equations for the Biomass Boiler   |
| `CHP_resource.py`              | Modeling of Combined Heat and Power (CHP)   |
| `Electrolyzer_P2G_resource.py` | Modeling of the Power-to-Gas (P2G) system   |
| `Electric_Vehicles_resource.py`| Modeling of Electric Vehicles (EVs)         |
| `Fuel_Cell_resource.py`        | Modeling of Fuel Cells                      |
| `HP_resource.py`               | Modeling of Heat Pumps (HP)                 |
| `Hydrogen_Storage_resource.py` | Modeling of Hydrogen Storage                |
| `PV_resource.py`               | Modeling of Photovoltaic (PV) panels        |
| `Storage_resource.py`          | Modeling of Battery Storage Systems         |
| `Wind_Turbine_resource.py`     | Modeling of Wind Turbines                   |


---

## 💾 Simulation Results Storage

All generated graphs and resource outputs are saved in the folder containing the `Crete_Valley_T.4.3` file.


...
## 🚀 How to Use

### 1. Cloning the Repository

To start using this project, first clone the repository. In the terminal, run:

```bash
git clone https://github.com/hugomotta13/crete_valley.git
```

This will create a local copy of the repository on your computer.

---

### 2. Setting Up the Environment

The project uses a virtual environment to manage dependencies. Follow the steps below:

#### 2.1 Navigate to the project directory:

```bash
cd crete_valley
```

#### 2.2 Create the virtual environment:

```bash
python -m venv .venv
```

#### 2.3 Activate the virtual environment:

**Windows (PowerShell):**

```bash
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```bash
.\venv\Scripts\activate.bat
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

---

### 3. Installing Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

If there's no `requirements.txt` file, you can install the libraries manually:

```bash
pip install pandas pyomo matplotlib numpy openpyxl
```

---

### 4. Preparing the Input Data

Make sure the files `Input Data-Resources 1.xlsx` and `Input Data-Other.xlsx` are in the correct folder as specified in the project structure.

---

### 5. Running the Code

Run the main Python file:

```bash
python main.py
```

---

### 6. Checking the Results

After execution, the results will be generated and saved in an Excel file (or another format, depending on your code).

You will find plots of:
- Electricity loads  
- Gas loads  
- Hydrogen production  
- Secondary reserve allocation  
- Other resource-specific outputs

---

## 📝 Final Notes

- Ensure that all input Excel files are in the correct format and contain the appropriate sheet names, as described earlier.  
- Adjust any necessary parameters in the code (e.g., price values, demand forecasts) according to your use case.





