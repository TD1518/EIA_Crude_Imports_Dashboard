# Import packages
from pathlib import Path
import requests
import os 
import pandas as pd
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
import time

data_dir = Path(__file__).parent / 'data'    # the "data" folder next to this script
data_dir.mkdir(exist_ok=True)                # create it if it doesn't exist yet

# Define the API endpoint and parameters
api_key=os.environ.get("EIA_API_Key")
if not api_key:                                           # nothing loaded from .env
    raise SystemExit("EIA_API_Key not found. Check that your .env file is in this folder and spelled correctly.")
startdate = "2021-01"

url = "https://api.eia.gov/v2/crude-oil-imports/data/" # EIA endpoint, no key
params = { 
          "api_key": api_key,
          "frequency": "monthly", 
          "data[0]": "quantity",
          "start": startdate, 
           # Tie-breaker sorts: give every row one fixed position so the 5,000-row chunks don't overlap or skip rows.
          "sort[0][column]": "period",
          "sort[0][direction]": "desc",
          "sort[1][column]": "originId",
          "sort[1][direction]": "asc",
          "sort[2][column]": "destinationId",
          "sort[2][direction]": "asc",
          "sort[3][column]": "gradeId",
          "sort[3][direction]": "asc",
          "offset": 0,
          "length":5000
           }

# Import data from the EIA API
EIACrudeImports = requests.get(url, params=params, timeout=60) # 60-second timeout
EIACrudeImports.raise_for_status() # raise an exception if the request failed
print(EIACrudeImports.status_code)
total = int(EIACrudeImports.json()['response']['total']) # Get the total number of records from the API response
print("Total rows available:",total)

# --- Pull the data in 5,000-row chunks ---
all_rows = EIACrudeImports.json()["response"]["data"]   # the first request's rows become chunk 1
offset = 5000        # the loop starts where chunk 1 ended
chunks = 1           # chunk 1 is already done
print("Chunk 1 - got", len(all_rows), "rows starting at row 0")

while offset < total:
    params["offset"] = offset                      # tell the EIA where to start
    resp = requests.get(url, params=params, timeout=60) # 60-second timeout
    resp.raise_for_status() # raise an exception if the request failed
    rows = resp.json()["response"]["data"]         # just the rows, not the extra info
    all_rows.extend(rows)                          # add this chunk to the pile
    print("Chunk", chunks + 1, "- got", len(rows), "rows starting at row", offset)
    offset += 5000                                 # move the start forward 5,000
    chunks += 1                                    # count this request
    time.sleep(1)                                  # pause 1 second to avoid overwhelming the server
print("Total rows collected:", len(all_rows))

# --- Check for duplicate rows ---
df = pd.DataFrame(all_rows)                            # turn the pile into a table
print("Duplicate rows:", df.duplicated().sum())        # count rows that appear twice

# --- Save the table to a CSV file ---
df.to_csv(data_dir / 'EIA_Crude_Imports.csv', index=False)
print("Saved", len(df), "rows to CSV")

# NOTE: the EIA's reported total is consistently overstated by ~1,104 rows (tested Oct and Nov 2026:
# every chunk full, no duplicates, nothing past the last row). A WARNING with a gap near 1,104 is
# expected. A much larger gap, or a short chunk in the middle of the run, would be a real problem.

# --- Confirm every row was captured ---
if len(df) == total:
    print("Complete: all", total, "rows captured")
else:
    print("WARNING: expected", total, "rows but got", len(df))