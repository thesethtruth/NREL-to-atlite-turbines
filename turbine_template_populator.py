#%%
from pathlib import Path
import pandas as pd
import jinja2
import re
import requests
from io import StringIO

# https://github.com/NREL/turbine-models
REPO = Path(__file__).parent / "turbine-models"

OFFSHORE = REPO / "Offshore"
ONSHORE = REPO / "Onshore"
TEMPLATE = Path(__file__).parent / "turbine_template.yaml"
TARGET = Path(__file__).parent / "atlite-turbines"
TARGET.mkdir(exist_ok=True, parents=True)


def get_turbine_metadata(turbine_name):
    r = requests.get(f"https://raw.githubusercontent.com/NREL/turbine-models/gh-pages/docs/source/{turbine_name}.rst")
    raw_string = r.content.decode()

    # extract the table lines
    matches = re.findall("(\|.+\n)", raw_string)
    # join and clean up extra spaces
    joined_string = "".join(x for x in matches)
    parsed_string = re.sub("\s{2,}","",joined_string)
    # read table with pandas
    df = (pd.read_table(StringIO(parsed_string), sep="|", index_col=1, skip_blank_lines=True, skipinitialspace=True)
    )
    df = df[df.columns[1]]
    # normalize names
    df.index = [i.lower().replace("-","_").replace(" ","_") for i in df.index]
    df.index = [i if i!="name" else 'id' for i in df.index]

    return df

def populate_turbines(csv_folder: Path, target_dir):
    powercurve_files = csv_folder.glob("*.csv")
    

    for pc in powercurve_files:

        if "NREL" in pc.stem:
            turbine_name = pc.stem
            turbine = get_turbine_metadata(turbine_name)
            
            try:
                source, nrel, ref, rated_power, _ = turbine_name.split("_")
            except ValueError:
                break
            
            
            outname = f"{nrel}_{ref}Turbine_{source}_{rated_power}.yaml"

            df = pd.read_csv(pc)
            windspeeds_ms = list(df['Wind Speed [m/s]'].round(1).values)
            power_MW = list((df['Power [kW]'].round(2)/1e3).values)

            if not turbine.id.strip().endswith("MW"):
                turbine.id += " MW"

            with open(TEMPLATE) as file:
                template = jinja2.Template(file.read())
            output = template.render(
                turbine_name=turbine.id,
                hub_height_m=turbine.hub_height,
                manufacturer="NREL",
                datasheet_source=f"https://nrel.github.io/turbine-models/{turbine_name}.html",
                powercurve_v_ms=windspeeds_ms,
                powercurve_P_MW=power_MW,
            )
            
            with open( target_dir / outname, 'w') as outfile:
                outfile.writelines(output)
                

populate_turbines(OFFSHORE, TARGET)
populate_turbines(ONSHORE, TARGET)


#%%

