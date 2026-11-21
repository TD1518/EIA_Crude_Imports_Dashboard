# Install packages
from pathlib import Path
from dash import Dash, dcc, html, callback, Output, Input
import plotly.express as px
import pandas as pd
import dash_ag_grid as dag
import plotly.io as pio

data_dir = Path(__file__).parent / 'data'    # the "data" folder next to this script
EIA_Crude_Imports = data_dir / 'EIA_Crude_Imports.csv'  #File path for EIA Crude Imports CSV file
Destination_Mapping = data_dir / 'Destination_Mapping.csv' #File path for Destination Mapping CSV file

Crude_Imports_Data = pd.read_csv(EIA_Crude_Imports)  #Open the EIA Crude Imports CSV file and load the data to a pandas DataFrame
Destination_Mapping_Data = pd.read_csv(Destination_Mapping) #Open the Mapping file and load to a pandas DataFrame

#Drop unnecessary columns from the DataFrame
Columns_Drop = ['originId','originType','destinationId','destinationType']
Crude_Imports_Data = Crude_Imports_Data.drop(columns=Columns_Drop)

#Rename columns in the DataFrame for better readability
Columns_Rename ={
    'period':'Date',
    'originName':'Origin',
    'originTypeName':'Origin Type',
    'destinationName':'Destination',
    'destinationTypeName':'Destination Type',
    'gradeId':'Grade ID',
    'gradeName':'Grade',
    'quantity':'Quantity',
    'quantity-units':'Units',
    }

# Convert period and quantity columns to appropriate data types
Crude_Imports_Data['period'] = pd.to_datetime(Crude_Imports_Data['period'])
Crude_Imports_Data['quantity'] = pd.to_numeric(Crude_Imports_Data['quantity'], errors='coerce')

Crude_Imports_Data = Crude_Imports_Data.rename(columns=Columns_Rename)  # Rename columns
Crude_Imports_Data['kb/day'] = Crude_Imports_Data['Quantity'] / Crude_Imports_Data['Date'].dt.days_in_month # Convert monthly totals to thousand barrels per day
Crude_Imports_Data = Crude_Imports_Data.merge(Destination_Mapping_Data, how='left', left_on='Destination', right_on='destinationName') #Merge the Destination Mapping DataFrame with the Crude Imports DataFrame 

padd_data = Crude_Imports_Data[
    (Crude_Imports_Data['Origin Type'] == 'World') &
    (Crude_Imports_Data['Destination Type'] == 'Port PADD')
    ]

padd_data = padd_data.groupby(['Date', 'Market'], as_index=False)['kb/day'].sum()
padd_data = padd_data.sort_values(['Market', 'Date'])
padd_data['Days'] = padd_data['Date'].dt.days_in_month
padd_data['Barrels'] = padd_data['kb/day']*padd_data['Days']
padd_data['Year'] = padd_data['Date'].dt.year
padd_data['MoM Change'] = padd_data.groupby('Market')['kb/day'].diff(1)  # Calculate month-over-month change
padd_data['YoY Change'] = padd_data.groupby('Market')['kb/day'].diff(12) # Calculate year-over-year change
padd_data['YTD Barrels'] = padd_data.groupby(['Market','Year'])['Barrels'].cumsum()  # Calculate YTD barrels
padd_data['YTD Days'] = padd_data.groupby(['Market','Year'])['Days'].cumsum()  # Calculate YTD days
padd_data['YTD Avg'] = padd_data['YTD Barrels'] / padd_data['YTD Days']  # Calculate YTD average

grade_data = Crude_Imports_Data[
    (Crude_Imports_Data['Origin Type'] == 'World') &
    (Crude_Imports_Data['Destination Type'] == 'United States')
    ]
grade_data = grade_data.groupby(['Date', 'Grade'], as_index=False)['kb/day'].sum()

grade_data['Share (%)'] = grade_data['kb/day'] / grade_data.groupby('Date')['kb/day'].transform('sum') * 100

month_list = padd_data['Date'].drop_duplicates().sort_values(ascending=True).to_list()

# Refinery data, all origin types (used by the refinery origin chart's Country/Region/OPEC switch)
ref_data_all = Crude_Imports_Data[
    (Crude_Imports_Data['Destination Type'] == 'Refinery') &
    (Crude_Imports_Data['Category'].isin(['Refinery', 'Other Processor']))
    ]
ref_data_all = ref_data_all.rename(columns={'Market': 'Refinery'})
ref_data_all = ref_data_all.groupby(['Date', 'Refinery', 'Origin', 'Grade', 'Origin Type'], as_index=False)['kb/day'].sum()
ref_data_all = ref_data_all.sort_values(['Refinery', 'Date'])
ref_data_all['Days'] = ref_data_all['Date'].dt.days_in_month
ref_data_all['Barrels'] = ref_data_all['kb/day'] * ref_data_all['Days']
ref_data_all['Year'] = ref_data_all['Date'].dt.year

# Refinery data, countries only (used by every other refinery chart and table)
ref_data = ref_data_all[ref_data_all['Origin Type'] == 'Country'].copy()

# One month list for the refinery tab's slider and every callback that reads it
ref_month_list = ref_data_all['Date'].drop_duplicates().sort_values(ascending=True).to_list()

# Default refinery: the one with the largest imports in the latest month
latest_ref_rows = ref_data[ref_data['Date'] == ref_data['Date'].max()]
default_refinery = latest_ref_rows.groupby('Refinery')['kb/day'].sum().idxmax()

px.defaults.template = "simple_white"  # Set default template for Plotly Express charts
pio.templates['simple_white'].layout.font.family = 'Segoe UI, Arial, sans-serif'   # same fonts as the page
pio.templates['simple_white'].layout.font.color = '#1f2937'                       # same dark gray as the page text
pio.templates['simple_white'].layout.yaxis.tickformat = ','  # y-axis numbers with commas, no decimal places
pio.templates['simple_white'].layout.xaxis.hoverformat = '%b-%Y'   # date axis hover shows e.g. "Aug-2026"

data_through = Crude_Imports_Data['Date'].max().strftime('%b %Y')   # latest month in the data, e.g. "Aug 2026"


padd_colors = {
    'PADD 1': '#1f77b4',  # Blue
    'PADD 2': '#ff7f0e',  # Orange
    'PADD 3': '#2ca02c',  # Green
    'PADD 4': '#d62728',  # Red
    'PADD 5': '#9467bd',  # Purple
    'PADD 6': '#17becf',  # Cyan
    'Other': 'lightgray' ,    # Gray
    }

grade_colors = {
    'Light Sweet': '#bcbd22',  # olive
    'Medium': '#8c564b',       # brown
    'Heavy Sweet': '#2c75a0',  # steel blue
    'Light Sour': '#b327d6',   # violet
    'Heavy Sour': '#7b1e1e',   # dark red
}

origin_colors = {
    'Canada': '#1f77b4',        # blue
    'Mexico': '#ff7f0e',        # orange
    'Saudi Arabia': '#2ca02c',  # green
    'Iraq': '#d62728',          # red
    'Kuwait': '#9467bd',        # purple
    'Venezuela': '#8c564b',     # brown
    'Russia': '#e377c2',        # pink
    'Colombia': '#17becf',      # teal (was gray)
    'Brazil': '#bcbd22',        # olive
    'Guyana': '#393b79',        # navy
    'Ecuador': '#e7969c',       # rose
    'Nigeria': '#637939',       # dark olive
    'Other': 'lightgray',         # gray, for background only
}

# KPI data: total U.S. imports per month (World → United States, so nothing is double counted)
kpi_total_data = Crude_Imports_Data[
    (Crude_Imports_Data['Origin Type'] == 'World') &
    (Crude_Imports_Data['Destination Type'] == 'United States')
].groupby('Date')['kb/day'].sum()

# KPI data: U.S. imports by country per month (Country → United States), for the top supplier
kpi_country_data = Crude_Imports_Data[
    (Crude_Imports_Data['Origin Type'] == 'Country') &
    (Crude_Imports_Data['Destination Type'] == 'United States')
].groupby(['Date', 'Origin'], as_index=False)['kb/day'].sum()

# Tab styles: plain when inactive, white with a colored accent line when active
tab_style = {
    'backgroundColor': '#f4f6f9',          # same light gray as the page
    'border': 'none',
    'borderBottom': '2px solid #e5e7eb',   # faint line under inactive tabs
    'color': '#6b7280',                    # gray text
    'padding': '12px',
}
tab_selected_style = {
    'backgroundColor': 'white',            # matches your cards
    'border': 'none',
    'borderBottom': '3px solid #1f77b4',   # blue accent under the active tab
    'color': '#1f2937',                    # dark text
    'fontWeight': '600',                   # semi-bold
    'padding': '12px',
}


#Start Dash App
app = Dash()
server = app.server #the web server Render's gunicorn runs; not used when you run "app.py"
app.layout= html.Div([
           html.Div([                                              # header strip
            html.H1("EIA Crude Oil Imports", style={'margin': '0'}),           # title on the left; remove default spacing
            html.Div([                                          # source + freshness on the right
                html.Div('Source: U.S. Energy Information Administration (EIA)'),
                html.Div('Data through ' + data_through),
            ], style={'textAlign': 'right', 'fontSize': '13px', 'color': '#6b7280'}),
        ], className='card', style={
            'display': 'flex',
            'justifyContent': 'space-between',                  # push title and info to opposite ends
            'alignItems': 'center',                             # line them up vertically
            'marginBottom': '16px',                             # space above the tabs
        }),      

    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Imports Overview', value='tab-1',style = tab_style, selected_style = tab_selected_style, children=[
# Create date dropdown              
html.Div([
html.Br(),       
       html.Label('Select Month for PADD Table:'),
        dcc.Dropdown(
                id='month_dropdown',
                options=[{'label': date.strftime('%b-%Y'), 'value': date.strftime('%Y-%m-%d')} 
                            for date in padd_data['Date'].drop_duplicates().sort_values(ascending=False)],
                value=padd_data['Date'].max().strftime('%Y-%m-%d'),
                multi=False,
                clearable=False),
       ],style={'width': '15%'}),
html.Br(),      
# KPI row
html.Div([ 
    html.Div([
        html.Div('Total U.S. Imports', className='kpi-label'),
        html.Div(id='kpi_total', className='kpi-value'),
    ], className='card', style={'flex': '1'}),

    html.Div([
        html.Div('Change vs. Last Month', className='kpi-label'),
        html.Div(id='kpi_mom', className='kpi-value'),
    ], className='card', style={'flex': '1'}),

    html.Div([
        html.Div('Change vs. Last Year', className='kpi-label'),
        html.Div(id='kpi_yoy', className='kpi-value'),
    ], className='card', style={'flex': '1'}),

    html.Div([
        html.Div('Top Supplier', className='kpi-label'),
        html.Div(id='kpi_top', className='kpi-value'),
    ], className='card', style={'flex': '1'}),

], style={'display': 'flex', 'gap': '20px', 'marginBottom': '16px'}),

html.Br(),  

#Create row for table and pie charts
html.Div([
html.Div([                     
dag.AgGrid(
            id='padd_table',
            columnDefs=[
                {'field': 'Market'},
                {'field': 'kb/day','valueFormatter': {'function': "d3.format(',.0f')(params.value)"}},
                {'field': 'MoM Change', 'headerName': 'Month-over-Month Change'},
                {'field': 'YoY Change', 'headerName': 'Year-over-Year Change'}
            ], rowData=[],
            dashGridOptions={'domLayout': 'autoHeight'},
            columnSize='sizeToFit'
            ),
],className='card', style={'width': '40%'}),
           
html.Div([
dcc.Graph(id='piechart1', figure={},style={'height': '280px'}),],
         className='card',style={'width': '25%'}),

html.Div([
dcc.Graph(id='piechart2', figure={},style={'height': '280px'}),],
         className='card',style={'width': '25%'}),

],style={'display': 'flex', 'gap': '50px'}),

html.Br(),

#Create row for date range and View Imports By
html.Div([
    html.Label('Select Month Range:'),
    dcc.RangeSlider(
        id='month_slider',
        min=0,
        max=len(month_list) - 1,
        step=1,
        value=[0, len(month_list) - 1],
        marks={i: month.strftime('%Y') for i, month in enumerate(month_list) if month.month == 1},
        allow_direct_input=False
    ),
    html.Br(),
    html.Div(id='slider-label'),
], className='card',style={'width': '450px'}),

html.Br(),
#Create row for filters and bar charts
    html.Div([
    html.Div([                                              
    html.Div([
    html.Div([
        html.Label('View imports by:'),
                    dcc.RadioItems(id='view_switch',
                        options=[
                            {'label': 'Country', 'value': 'Country'},
                            {'label': 'Region', 'value': 'Region'},
                            {'label': 'OPEC vs. Non-OPEC', 'value': 'OPEC/non-OPEC'},
                        ],
                        value='Country',      # which one is selected when the page loads
                        inline=True           # show the choices side by side, not stacked
                    ),
    ]),
    html.Div([                                              
        html.Label('Select Origin(s):'),
        dcc.Dropdown(id='Origin_dropdown',
            options=[],
            value=[],
            multi=True,
            placeholder='All origins (click to filter)',
            style={'width': '300px'}),
    ]),
    ], style={'display': 'flex','gap': '40px'}), 
        dcc.Graph(id='chart1', figure={}),
    ], className='card',style={'width': '48%'}),
    html.Div([                                              
        html.Label('Select Destination Type:'),
        dcc.Dropdown(
            id='Destination_dropdown',
            options=[{'label': DestinationType, 'value': DestinationType}
                     for DestinationType in Crude_Imports_Data['Destination Type'].unique()
                     if DestinationType != 'United States' and DestinationType != 'Port' and DestinationType != 'Refinery'],
            value='Port PADD',
            multi=False,
            clearable=False,
            style={'width': '300px'}),
        dcc.Graph(id='chart2', figure={}),
    ], className='card',style={'width': '50%'}),

], style={'display': 'flex', 'gap': '50px'}), 
        
html.Br(),
html.Div([  
html.Div([
dcc.Graph(id='chart3', figure={}),
],className='card',style = {'width': '48%'}),

html.Div([
dcc.Graph(id='chart4', figure={}),
], className='card',style = {'width': '48%'}),
], style={'display': 'flex', 'gap': '50px'})

]),
    
#Refinery Analysis Tab
dcc.Tab(label = 'Refinery Analysis', value = 'tab-2', style = tab_style, selected_style = tab_selected_style, children = [
html.Div([
html.Div([
   html.Label('Select Month'),
         dcc.Dropdown(
                   id='month_dropdown2',
                   options=[{'label': date.strftime('%b-%Y'), 'value': date.strftime('%Y-%m-%d')} 
                               for date in ref_data['Date'].drop_duplicates().sort_values(ascending=False)],
                   value=ref_data['Date'].max().strftime('%Y-%m-%d'),
                   multi=False,
                   clearable=False),
],style={'width': '15%'}),

html.Div([    
      html.Label('Select Refinery'),
               dcc.Dropdown(
                         id='ref_dropdown',
                         options=[{'label': refinery, 'value': refinery} 
                                     for refinery in ref_data['Refinery'].drop_duplicates().sort_values()],
                         value= default_refinery,
                         multi=False,
                         clearable=False),
],style={'width': '15%'}),
],style={'display': 'flex', 'gap': '50px'}),
 
   
html.Br(),
html.Div([
html.Div([                     
dag.AgGrid(
            id='ref_table',
            columnDefs=[
                {'field': 'Origin'},
                {'field': 'kb/day','valueFormatter': {'function': "d3.format(',.0f')(params.value)"}},
                {'field': 'MoM Change', 'headerName': 'Month-over-Month Change'},
                {'field': 'YoY Change', 'headerName': 'Year-over-Year Change'}
            ], rowData=[],
            dashGridOptions={'domLayout': 'autoHeight'},
            columnSize='sizeToFit'
           ),
],className='card',style={'width': '40%'}),
        
      html.Div([
        dcc.Graph(id='refchart1', figure={},style={'height': '280px'}),],
                 className='card',style={'width': '25%'}),
    html.Div([
        dcc.Graph(id='refchart2', figure={},style={'height': '280px'}),],
                className='card',style={'width': '25%'}),
      
], style={'display': 'flex', 'gap': '50px'}),
html.Br(),
    html.Div([
    html.Div([
        html.Label('Select Month Range:'),
        dcc.RangeSlider(
            id='month_slider1',
            min=0,
            max=len(ref_month_list) - 1,
            step=1,
            value=[0, len(ref_month_list) - 1],
            marks={i: month.strftime('%Y') for i, month in enumerate(ref_month_list) if month.month == 1},
            allow_direct_input=False
        ),
        html.Br(),
        html.Div(id='slider-label1'),
    ], className='card',style={'width': '450px'}),

html.Div([
        html.Label('View imports by:'),
            dcc.RadioItems(
                id='view_switch1',
                options=[
                    {'label': 'Country', 'value': 'Country'},
                    {'label': 'Region', 'value': 'Region'},
                    {'label': 'OPEC vs. Non-OPEC', 'value': 'OPEC/non-OPEC'},
                ],
                value='Country',      # which one is selected when the page loads
                inline=True           # show the choices side by side, not stacked
            ),
    
            ],className='card',style={'width': '25%'}),
    ],style={'display': 'flex', 'gap': '50px'}),
    html.Br(),
    html.Div([
    html.Div([
        dcc.Graph(id='ref_origin_chart', figure={}),
        ],className='card',style = {'width': '50%'}),

    html.Div([
        dcc.Graph(id='ref_grade_chart', figure={}),
        ],className='card',style = {'width': '50%'}),
    ], style={'display': 'flex', 'gap': '50px'}),
    html.Br(),
    html.Div([ 
    html.Div([
        dcc.Graph(id='ref_grade_ytd_chart', figure={}),
        ], className='card',style = {'width': '50%'}),

    html.Div([
        dcc.Graph(id='ref_heatmap', figure={}),
        ], className='card',style = {'width': '50%'}),
    ], style={'display': 'flex', 'gap': '50px'})

]),
]),
])

#Callbacks

def make_pie(data, names_col, color_map, title):
    """Build a styled pie chart. Used by all four pie callbacks."""
    fig = px.pie(
        data,
        names=names_col,
        values='kb/day',
        hole=0.2,
        color=names_col,                 # needed for color_discrete_map to work on pies
        color_discrete_map=color_map,
        title=title,
    )
    fig.update_traces(
        textposition='inside',
        textinfo='label',
        insidetextorientation='horizontal',
        hovertemplate='%{label}<br>%{value:,.0f} kb/day<br>%{percent}<extra></extra>',
    )
    fig.update_layout(
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5),
        title_x=0.5,
        title_xanchor='center',
        margin=dict(t=85, b=5, l=10, r=10),
    )
    return fig

#Callback - KPI cards (follow the month dropdown)
@callback(
    Output('kpi_total', 'children'),
    Output('kpi_mom', 'children'),
    Output('kpi_yoy', 'children'),
    Output('kpi_top', 'children'),
    Input('month_dropdown', 'value')
)

def update_kpis(selected_month):
    selected_date = pd.to_datetime(selected_month)
    prev_date = selected_date - pd.DateOffset(months=1)      # last month
    prior_date = selected_date - pd.DateOffset(years=1)      # same month last year

    # Look up each month's U.S. total (None if that month isn't in the data)
    total = kpi_total_data.get(selected_date)
    prev_total = kpi_total_data.get(prev_date)
    prior_total = kpi_total_data.get(prior_date)

    # Card 1: total imports
    total_text = f'{total:,.0f} kb/d'

    # Cards 2 and 3: changes, with a + or - sign; 'n/a' when there's nothing to compare
    mom_text = f'{total - prev_total:+,.0f} kb/d' if prev_total is not None else 'n/a'
    yoy_text = f'{total - prior_total:+,.0f} kb/d' if prior_total is not None else 'n/a'

    # Card 4: biggest supplier this month and its share of the total
    month_rows = kpi_country_data[kpi_country_data['Date'] == selected_date]
    top_row = month_rows.loc[month_rows['kb/day'].idxmax()]
    top_share = top_row['kb/day'] / total * 100
    top_text = f"{top_row['Origin']} ({top_share:.0f}%)"

    return total_text, mom_text, yoy_text, top_text


def get_filtered_import_data(slider_value, origin_values, destination_values, view_type):
    start_month = ref_month_list[slider_value[0]]
    end_month = ref_month_list[slider_value[1]]

    if not origin_values:
        origin_values = Crude_Imports_Data['Origin'].unique().tolist()  # If no origins are selected, use all origins

    return Crude_Imports_Data[
        (Crude_Imports_Data['Date'] >= (start_month)) &
        (Crude_Imports_Data['Date'] <=(end_month)) &
        (Crude_Imports_Data['Origin'].isin(origin_values)) &
        (Crude_Imports_Data['Destination Type'] == destination_values) &
        (Crude_Imports_Data['Origin Type'] == view_type)
    ]

#Callback - Crude Imports by Origin
@callback(
    Output('chart1', 'figure'),
    Input('month_slider', 'value'),
    Input('Origin_dropdown', 'value'),
    Input('Destination_dropdown', 'value'),
    Input('view_switch', 'value')
)
def update_chart1(slider_value, origin_values, destination_values, view_type):
    filtered_data = get_filtered_import_data(slider_value, origin_values, destination_values, view_type)

    chart_data = filtered_data.groupby(['Date', 'Origin'], as_index=False)['kb/day'].sum()
    
    top_origins = filtered_data.groupby(['Origin'], as_index=False)['kb/day'].sum()
    top8_list = top_origins.nlargest(8, 'kb/day')['Origin'].tolist()  # Create the list of top 8 origins
    checktop8 = chart_data['Origin'].isin(top8_list)  # Check if each origin is in the top 8 list
    chart_data['Origin'] = chart_data['Origin'].where(checktop8, 'Other')  # Replace non-top 8 origins with 'Other'
    chart_data = chart_data.groupby(['Date', 'Origin'], as_index=False)['kb/day'].sum()  # Re-aggregate after grouping 'Other'
    chart_data = chart_data.round({'kb/day': 0})  # Round chart1 values to 0 decimal places

    chart1 = px.bar(
        chart_data,
        x='Date',
        y='kb/day',
        color='Origin',
        pattern_shape_sequence=[''],
        color_discrete_map=origin_colors,
        category_orders={'Origin': top8_list + ['Other']},  # Ensure 'Other' is last in the legend
        title='Crude Imports by Origin (Top 8 + Other)'
    )
    chart1.update_layout(
        legend_traceorder='reversed',
        xaxis_title=None,
    )  # Reverse Legend order

    return chart1

#Callback - Crude Imports by Destination
@callback(
    Output('chart2', 'figure'),
    Input('month_slider', 'value'),
    Input('Origin_dropdown', 'value'),
    Input('Destination_dropdown', 'value'),
    Input('view_switch', 'value')
)
def update_chart2(slider_value, origin_values, destination_values, view_type):
    filtered_data = get_filtered_import_data(slider_value, origin_values, destination_values, view_type)

    chart2_data = filtered_data.groupby(['Date', 'Market'], as_index=False)['kb/day'].sum()
    chart2_data = chart2_data.round({'kb/day': 0})  # Round chart2 values to 0 decimal places

    top_markets = filtered_data.groupby(['Market'], as_index=False)['kb/day'].sum()
    top10_markets_list = top_markets.nlargest(10, 'kb/day')['Market'].tolist()  # Create the list of top 10 markets
    checktop10_markets = chart2_data['Market'].isin(top10_markets_list)  # Check if each market is in the top 10 list
    chart2_data['Market'] = chart2_data['Market'].where(checktop10_markets, 'Other')  # Replace non-top 10 markets with 'Other'
    chart2_data = chart2_data.groupby(['Date', 'Market'], as_index=False)['kb/day'].sum()  # Re-aggregate after grouping 'Other'

    chart2 = px.bar(
        chart2_data,
        x='Date',
        y='kb/day',
        color='Market',
        pattern_shape_sequence=[''],
        color_discrete_map=padd_colors,
        category_orders={'Market': top10_markets_list + ['Other']},  # Ensure 'Other' is last in the legend
        title='Crude Imports by Destination'
    )

    chart2.update_layout(
        legend_traceorder='reversed',
        xaxis_title=None,
    )

    return chart2

#Callback - Date Slider Label
@callback(
    Output('slider-label', 'children'),
    Input('month_slider', 'value')
)
def update_slider_label(slider_range):
    start_month = month_list[slider_range[0]].strftime('%b-%Y')
    end_month = month_list[slider_range[1]].strftime('%b-%Y')
    return f'Selected Month Range: {start_month} to {end_month}'

#Callback - Date Slider1 Label
@callback(
    Output('slider-label1', 'children'),
    Input('month_slider1', 'value')
)
def update_ref_slider_label(slider_range1):
    start_month = month_list[slider_range1[0]].strftime('%b-%Y')
    end_month = month_list[slider_range1[1]].strftime('%b-%Y')
    return f'Selected Month Range: {start_month} to {end_month}'

#Callback - Grade Percentage
@callback(
    Output('chart3', 'figure'),
    Input('month_slider', 'value')
)
def update_grade_chart(slider_value):
    start_month = month_list[slider_value[0]]
    end_month = month_list[slider_value[1]]
    grade_filtered = grade_data[
        (grade_data['Date'] >= (start_month)) &
        (grade_data['Date'] <= (end_month))
    ]
    chart3data = grade_filtered.round(1)  # Round chart3 values to 1 decimal place
    chart3 = px.line(chart3data, x='Date', y='Share (%)', color='Grade', title='Crude Imports by Grade Share (%)') 
    chart3.update_layout(
            xaxis_title=None,
            ) 
    return chart3

#Callback - Origin Dropdown
@callback(
    Output('Origin_dropdown', 'options'),   # the list of choices in the dropdown
    Output('Origin_dropdown', 'value'),     # which choices are selected
    Input('view_switch', 'value')           # runs whenever the switch changes
)
def update_origin_list(view_type):
    # Keep only origins matching the picked button, listed once each, A to Z
    origins = sorted(Crude_Imports_Data.loc[Crude_Imports_Data['Origin Type'] == view_type, 'Origin'].unique())
    return origins, []                 # first = the choices, second = nothing is selected

#Callback - PADD table
@callback(
    Output('padd_table', 'rowData'),
    Input('month_dropdown', 'value')
)
def update_padd_table(selected_month):
    month_rows = padd_data[padd_data['Date'] == selected_month]
    month_rows = month_rows[['Market', 'kb/day', 'MoM Change', 'YoY Change']]
    month_rows = month_rows.round(0)  # Round the values to 0 decimal places
    return month_rows.to_dict('records')

#Callback - Pie Chart by Market
@callback(
    Output('piechart1', 'figure'),
    Input('month_dropdown', 'value')
)
def update_piechart1(selected_month):
    piechart1_data = padd_data[padd_data['Date'] == selected_month]
    return make_pie(piechart1_data, 'Market', padd_colors, 'Crude Imports by Market')

#Callback - Pie Chart by Grade
@callback(
    Output('piechart2', 'figure'),
    Input('month_dropdown', 'value')
)
def update_piechart2(selected_month):
    piechart2_data = grade_data[grade_data['Date'] == selected_month]
    return make_pie(piechart2_data, 'Grade', grade_colors, 'Crude Imports by Grade')

#Callback - YTD Average by Market
@callback(
    Output('chart4','figure'),
    Input('month_dropdown','value')
)

def update_chart4(selected_month):
    selected_date = pd.to_datetime(selected_month)
    prior_date = selected_date - pd.DateOffset(years=1)
    chart4_data = padd_data[padd_data['Date'].isin([selected_date,prior_date])]
    chart4_data = chart4_data[['Market','YTD Avg', 'Year']]
    chart4_data['Year'] = chart4_data['Year'].astype(str)
    chart4 = px.bar(
        chart4_data, 
        x = 'YTD Avg',
        y = 'Market',
        orientation= 'h',
        barmode= 'group',
        color= 'Year'
        )
    chart4.update_layout(yaxis_autorange = 'reversed',xaxis_tickformat=',',xaxis_hoverformat=',.0f')
    
    return chart4
        
@callback(
    Output('refchart1', 'figure'),
    Input('month_dropdown2', 'value'),
    Input('ref_dropdown', 'value')
)
def update_refchart1(selected_month,selected_refinery):
    refchart1_data = ref_data[ref_data['Date'] == selected_month]
    refchart1_data = refchart1_data[refchart1_data['Refinery'] == selected_refinery]
    refchart1_data = refchart1_data.groupby('Origin', as_index=False)['kb/day'].sum()   # one row per country
    return make_pie(refchart1_data, 'Origin', origin_colors, 'Crude Imports by Country')

@callback(
    Output('refchart2', 'figure'),
    Input('month_dropdown2', 'value'),
    Input('ref_dropdown', 'value')
)
def update_refchart2(selected_month,selected_refinery):
    refchart2_data = ref_data[ref_data['Date'] == selected_month]
    refchart2_data = refchart2_data[refchart2_data['Refinery'] == selected_refinery]
    refchart2_data = refchart2_data.groupby('Grade', as_index=False)['kb/day'].sum()   # one row per grade
    return make_pie(refchart2_data, 'Grade', grade_colors, 'Crude Imports by Grade')

#Callback - Refinery table
@callback(
    Output('ref_table', 'rowData'),
    Input('month_dropdown2', 'value'),
    Input('ref_dropdown','value')
)
def update_ref_table(selected_month,selected_refinery):
    selected_date = pd.to_datetime(selected_month)
    previous_date = selected_date - pd.DateOffset(months=1)
    selected_date_py = selected_date - pd.DateOffset(years=1)
    refinery_rows = ref_data[ref_data['Refinery'] == selected_refinery]
    selected = refinery_rows[refinery_rows['Date'] == selected_date]
    selected = selected.groupby(['Origin'], as_index=False)['kb/day'].sum()
    previous = refinery_rows[refinery_rows['Date'] == previous_date]
    previous = previous.groupby(['Origin'], as_index=False)['kb/day'].sum()
    selected_py = refinery_rows[refinery_rows['Date'] == selected_date_py]
    selected_py = selected_py.groupby(['Origin'], as_index=False)['kb/day'].sum()
    previous = previous.rename(columns={'kb/day': 'Previous Month'})
    selected_py = selected_py.rename(columns={'kb/day': 'Previous Year'})
    ref_table = pd.merge(selected, previous, on='Origin', how='outer')
    ref_table = pd.merge(ref_table, selected_py, on='Origin', how='outer').fillna(0)
    ref_table['MoM Change'] = ref_table['kb/day'] - ref_table['Previous Month']
    ref_table['YoY Change'] = ref_table['kb/day'] - ref_table['Previous Year']
    return ref_table.round(0).to_dict('records')

#Callback - Refinery Imports by Origin
@callback(
    Output('ref_origin_chart', 'figure'),
    Input('month_slider1', 'value'),
    Input('ref_dropdown', 'value'),
    Input('view_switch1', 'value')
)
def update_ref_origin_chart(slider_value, refinery_values, view_type):
    ref_start_month = ref_month_list[slider_value[0]]
    ref_end_month = ref_month_list[slider_value[1]]
    ref_origin_chart_data = ref_data_all[
        (ref_data_all['Date'] >= (ref_start_month)) &
        (ref_data_all['Date'] <= (ref_end_month)) &
        (ref_data_all['Refinery'] == refinery_values) &
        (ref_data_all['Origin Type'] == view_type)
    ]
    ref_origin_chart_data = ref_origin_chart_data.groupby(['Date', 'Origin'], as_index=False)['kb/day'].sum()
    ref_origin_chart_data = ref_origin_chart_data.round({'kb/day': 0})  # Round chart1 values to 0 decimal places
    ref_origin_chart = px.bar(
        ref_origin_chart_data,
        x='Date',
        y='kb/day',
        color='Origin',
        pattern_shape_sequence=[''],
        color_discrete_map={'Other': 'lightgray'},
        title='Crude Imports by Origin'
    )
    ref_origin_chart.update_layout(
        legend_traceorder='reversed',
        xaxis_title=None,
    )  # Reverse Legend order

    return ref_origin_chart

#Callback - Refinery Imports by Grade
@callback(
    Output('ref_grade_chart', 'figure'),
    Input('month_slider1', 'value'),
    Input('ref_dropdown', 'value'),
   
)
def update_ref_grade_chart(slider_value, refinery_values):
    ref_start_month = ref_month_list[slider_value[0]]
    ref_end_month = ref_month_list[slider_value[1]]
    ref_grade_chart_data = ref_data[
        (ref_data['Date'] >= (ref_start_month)) &
        (ref_data['Date'] <= (ref_end_month)) &
        (ref_data['Refinery'] == refinery_values)
    ]
    ref_grade_chart_data = ref_grade_chart_data.groupby(['Date', 'Grade'], as_index=False)['kb/day'].sum()
    ref_grade_chart_data = ref_grade_chart_data.round({'kb/day': 0})  # Round chart2 values to 0 decimal places
    ref_grade_chart = px.bar(
        ref_grade_chart_data,
        x='Date',
        y='kb/day',
        color='Grade',
        pattern_shape_sequence=[''],
        color_discrete_map=grade_colors,
        title='Crude Imports by Grade'
    )
    ref_grade_chart.update_layout(
        legend_traceorder='reversed',
        xaxis_title=None,
    )  # Reverse Legend order

    return ref_grade_chart

#Callback - YTD Average by Grade - Refinery
@callback(
    Output('ref_grade_ytd_chart','figure'),
    Input('month_dropdown2','value'),
    Input('ref_dropdown','value')
)

def update_ref_ytd_chart(selected_month, refinery_value):
    selected_date = pd.to_datetime(selected_month)
    prior_date = selected_date - pd.DateOffset(years=1)
    current_start = selected_date.replace(month=1)
    prior_start = prior_date.replace(month=1)
    refinery_rows = ref_data[ref_data['Refinery'] == refinery_value]
    current = refinery_rows[(refinery_rows['Date'] >= current_start) & (refinery_rows['Date'] <= selected_date)]
    prior = refinery_rows[(refinery_rows['Date'] >= prior_start) & (refinery_rows['Date'] <= prior_date)]
    current = current.groupby(['Grade'], as_index=False)['Barrels'].sum()
    prior = prior.groupby(['Grade'], as_index=False)['Barrels'].sum()
    current_end = selected_date + pd.offsets.MonthEnd(0)
    current_days = (current_end - current_start).days + 1
    prior_end = prior_date + pd.offsets.MonthEnd(0)
    prior_days = (prior_end - prior_start).days + 1
    current['YTD Avg'] = current['Barrels'] / current_days
    prior['YTD Avg'] = prior['Barrels'] / prior_days
    current['Year'] = str(selected_date.year)
    prior['Year'] = str(prior_date.year)
    ytd_data = pd.concat([current, prior])

    ref_grade_ytd_chart = px.bar(
        ytd_data,
        x = 'YTD Avg', 
        y = 'Grade', 
        orientation= 'h',
        barmode= 'group',
        color= 'Year',
        title='YTD Average Imports by Grade - Refinery'
        )
    ref_grade_ytd_chart.update_layout(
        yaxis_autorange='reversed',
        xaxis_tickformat=',',          # commas on the axis
        xaxis_hoverformat=',.0f'       # commas, 0 decimals on hover
    )
    
    return ref_grade_ytd_chart

#Callback - Refinery Imports Heatmap
@callback(
    Output('ref_heatmap','figure'),
    Input('ref_dropdown','value'),
    Input('month_slider1','value')
)

def update_heatmap(refinery_value, slider_value):
    heat_start_month = ref_month_list[slider_value[0]]
    heat_end_month = ref_month_list[slider_value[1]]
    ref_heatmapchart = ref_data[
            (ref_data['Date'] >= (heat_start_month)) &
            (ref_data['Date'] <= (heat_end_month)) &
            (ref_data['Refinery'] == refinery_value)
        ]
    ref_heatmapchart = ref_heatmapchart.groupby(['Date', 'Origin'], as_index=False)['kb/day'].sum()
    ref_heatmapchart = ref_heatmapchart.pivot(index='Origin', columns='Date', values='kb/day')
    ref_heatmapchart = ref_heatmapchart.loc[ref_heatmapchart.sum(axis=1).sort_values(ascending=False).index]   # biggest total on top
    ref_heatmap = px.imshow(
        ref_heatmapchart,
        labels=dict(x="Date", y="Origin", color="kb/day"),
        title="Refinery Imports Heatmap",
        color_continuous_scale='Blues'
    )
    ref_heatmap.update_traces(hovertemplate='%{y}<br>%{x|%b %Y}<br>%{z:,.0f} kb/day<extra></extra>')
    ref_heatmap.update_layout(plot_bgcolor="white",xaxis_title=None, yaxis_title=None)
    return ref_heatmap

if __name__ == '__main__':
    app.run(debug=True)