import pandas as pd
from pathlib import Path

Path("data/lookups").mkdir(parents=True, exist_ok=True)

trains = pd.read_csv("../train_details.csv")

trains[
    ["train_no", "train_name"]
].drop_duplicates().to_json(
    "data/lookups/trains.json",
    orient="records",
    indent=2
)
stations = pd.read_csv("../station_full_names.csv")

stations[
    ["station_name", "station_full_name"]
].drop_duplicates().to_json(
    "data/lookups/stations.json",
    orient="records",
    indent=2
)