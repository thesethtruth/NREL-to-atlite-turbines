from genericpath import exists
from pathlib import Path
import pandas as pd
import jinja2
import re

# https://github.com/NREL/turbine-models
REPO = Path(__file__).parent / "turbine-models"

OFFSHORE = REPO / "Offshore"
ONSHORE = REPO / "Onshore"
TEMPLATE = Path(__file__).parent / "turbine_template.yaml"
TARGET = Path(__file__).parent / "atlite-turbines"
TARGET.mkdir(exist_ok=True, parents=True)

def populate_turbines(csv_folder: Path, target_dir, suffix):
    powercurve_files = csv_folder.glob("*.csv")
    

    for pc in powercurve_files:
        turbine_name = pc.stem
        match_hub = re.findall("_\d{2,}$|_\d{2,}.\d$|_\d{2,}_", turbine_name)
        try:
            hub_height = float(match_hub[0].replace("_", ""))
        except IndexError:
            print(f"no hubheight found for {turbine_name}")
            hub_height = None
    
        if hub_height:
            df = pd.read_csv(pc)
            windspeeds_ms = list(df['Wind Speed [m/s]'].round(1).values)
            power_MW = list((df['Power [kW]'].round(2)/1e3).values)

            with open(TEMPLATE) as file:
                template = jinja2.Template(file.read())
            output = template.render(
                turbine_name=turbine_name,
                hub_height_m=hub_height,
                manufacturer="NREL",
                datasheet_source=f"https://nrel.github.io/turbine-models/{turbine_name}.html",
                powercurve_v_ms=windspeeds_ms,
                powercurve_P_MW=power_MW,
            )
            
            with open( target_dir / (turbine_name + suffix +".yaml"), 'w') as outfile:
                outfile.writelines(output)
            

populate_turbines(OFFSHORE, TARGET, suffix="_offshore")
populate_turbines(ONSHORE, TARGET, suffix="")