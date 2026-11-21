# U.S. Crude Oil Imports Dashboard

An interactive dashboard exploring U.S. crude oil imports: where the oil comes from, where it lands, what quality it is, and which refineries take it. Built with Python and Dash, using monthly data from the U.S. Energy Information Administration (EIA).

**Live dashboard:** https://eia-crude-imports.onrender.com
*(Hosted on a free plan: the first visit after a quiet period can take about a minute to load.)*

## What it shows

**Imports Overview**
- Headline figures for any month: total imports, change from the prior month and year, and the top supplier's share
- Imports by PADD region, with month-over-month and year-over-year changes
- Trends by origin country, region, or OPEC membership, and by destination
- Crude quality mix (grade) over time
- Year-to-date averages by PADD, compared with the prior year

**Refinery Analysis**
- Each refinery's suppliers and crude grades for a selected month
- Supply trends over time, and a heatmap showing steady suppliers versus occasional cargoes
- Year-to-date averages by grade, compared with the prior year

## Data

- **Source:** EIA Open Data API (v2), crude oil imports dataset
- **Coverage:** January 2021 through the latest month the EIA has published
- **Units:** the EIA reports monthly totals in thousand barrels. The dashboard converts these to **thousand barrels per day (kb/d)** by dividing by the days in each month, so months of different lengths compare fairly.

## Methods notes

- **No double counting.** The EIA data reports the same oil at several levels (country, region, OPEC group, world total; port, state, PADD, U.S. total). Every view uses exactly one origin level and one destination level, so totals match real-world volumes.
- **Period comparisons with incomplete data.** Refinery imports arrive as individual cargoes, so many months have no shipment from a given country. Month-over-month and year-over-year changes are therefore calculated by comparing exact dates, not by stepping through rows.
- **Day-weighted year-to-date averages.** Year-to-date figures equal total barrels from January 1 through the end of the selected month, divided by the calendar days in that period.
- **EIA row count.** The EIA's reported record total consistently exceeds the rows it returns by about 1,100. Each pull is checked for full pages and duplicate rows, and the gap has stayed constant, indicating the difference lies in the EIA's count rather than missing data.
- **Destination names** are shortened for readability using a mapping file (`data/Destination_Mapping.csv`).

## Project structure

```
app.py              Dash dashboard
get_data.py         Pulls the data from the EIA API and saves it as CSV
requirements.txt    Python packages
assets/style.css    Page styling
data/               Imports data and the destination name mapping
```

## Running it locally

1. Download or clone this repository.
2. Create and activate a virtual environment, then install the packages:
   `pip install -r requirements.txt`
3. Get a free API key from the EIA: https://www.eia.gov/opendata/
4. Create a file named `.env` in the project folder containing one line:
   `EIA_API_Key=YOUR-EIA-API-KEY-HERE`
   (This file is excluded from the repository by `.gitignore`. Never commit it.)
5. Refresh the data: `python get_data.py`
6. Start the dashboard: `python app.py`, then open the address it prints.

## Built with

Python · pandas · Dash · Plotly · Dash AG Grid · hosted on Render