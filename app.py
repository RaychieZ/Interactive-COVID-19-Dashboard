# [wAAI ChatGPT-5.5] AI assistance was used for code structure, debugging, and implementation guidance.

import streamlit as st
import pandas as pd
import plotly.express as px

# loading data
CONFIRMED_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/refs/heads/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
DEATHS_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"


# setting webpage 
st.set_page_config(
    page_title="COVID-19 Country Dashboard",    # adding title for browser tab
    layout="wide"     # makes the app use more horizontal space on the webpage
)

st.title("COVID-19 Country Dashboard")  # adding title at the top of the webpage

st.write(
    "This app displays historical COVID-19 case information by country "
    "using the Johns Hopkins Center for Systems Science and Engineering "
    "COVID-19 time-series dataset."
)

st.write(
    "Use the sidebar to choose the data type, countries, and whether to display cumulative or daily counts."
)

# This function loads one COVID CSV file, cleans it, and returns it in a format that is easier to plot in Streamlit.

@st.cache_data    # tells Streamlit to remember the result of this function
def load_covid_data(url):
    data = pd.read_csv(url)

    # Remove columns that are not date columns
    data = data.drop(columns=["Province/State", "Lat", "Long"], errors="ignore")

    # Group by country because some countries have multiple provinces/states
    data = data.groupby("Country/Region").sum(numeric_only=True)

    # Turn dates from columns into rows
    data = data.reset_index()
    # Turning wide format into long format for plotting
    data_long = data.melt(
        id_vars="Country/Region",    # keep the country column as an identifying column
        var_name="Date",    # turn the old date columns into a new column called "Date"
        value_name="Count"    # turn the numbers inside the old date columns into a new column called "Count"
    )

    data_long["Date"] = pd.to_datetime(data_long["Date"], format="%m/%d/%y")   # convert the date values from string into real datetime values
    data_long = data_long.rename(columns={"Country/Region": "Country"})

    return data_long

confirmed = load_covid_data(CONFIRMED_URL)
deaths = load_covid_data(DEATHS_URL)

st.sidebar.header("User Options")

# select dataset
data_choice = st.sidebar.selectbox(       # create a dropdown menu where the user can choose one option
    "Select COVID-19 data type",
    ["Confirmed Cases", "Deaths"]
)

if data_choice == "Confirmed Cases":
    covid_data = confirmed.copy()
else:
    covid_data = deaths.copy()

# get the list of countries
countries = sorted(covid_data["Country"].unique())

# select country 
selected_countries = st.sidebar.multiselect(         # creates a dropdown where the user can choose multiple options
    "Select countries",
    countries,
    default=["US", "Brazil", "Canada"]
)

# select display type 
display_type = st.sidebar.selectbox(
    "Select display type",
    ["Cumulative counts", "Daily counts"]
)

# keeping the selected countries
filtered = covid_data[
                covid_data["Country"]     # select the "Country" column from the dataframe
                .isin(selected_countries)].copy()      # check whether each row’s country is inside the user’s selected country list
# keep only the rows where the result is True


# Default smoothing option
smooth = False

if display_type == "Daily counts":
    # Add 7-day rolling average for a smoother effect
    smooth = st.sidebar.checkbox("Show 7-day rolling average")
    
    filtered = filtered.sort_values(["Country", "Date"])     # sort the data first by country, then by date

    # Convert cumulative counts into daily counts
    filtered["Count"] = filtered.groupby("Country")["Count"].diff()      # getting the daily count by computing difference
    filtered["Count"] = filtered["Count"].fillna(0)    # replace missing values with 0

    # Some daily values may be negative due to corrections in the original data
    filtered["Count"] = filtered["Count"].clip(lower=0)     # prevent negative daily counts
    
    if smooth:
        filtered["Count"] = (
            filtered.groupby("Country")["Count"]
            .transform(lambda x: x.rolling(7, min_periods=1).mean())     
            # transform: return the smoothed values in the same shape as the original dataframe
            # min_periods=1: pandas is allowed to calculate an average even if there are fewer than 7 previous days.
        )     


# Plotting
chart_title = f"{display_type} of {data_choice}"

if display_type == "Daily counts" and smooth:
    chart_title = f"7-day average daily counts of {data_choice}"

fig = px.line(      # make a line plot
    filtered,        # the dataframe being plotted. It contains only the countries the user selected
    x="Date",
    y="Count",
    color="Country",     # each country gets its own line
    title=chart_title,
    labels={
        "Date": "Date",
        "Count": data_choice,       # Show the y-axis label as whatever the user selected, such as “Confirmed Cases” or “Deaths.”
        "Country": "Country"
    }
)

st.plotly_chart(fig, use_container_width=True)

# Keeping only date
table_data = filtered.copy()
table_data = table_data.reset_index(drop=True)     # cleaning table index
table_data["Date"] = table_data["Date"].dt.date     # display only the date     .dt.date: From the datetime column, keep only the date.

st.subheader("Selected Data")
st.dataframe(table_data, use_container_width=True)         # shows table_data as an interactive table in your Streamlit app

st.subheader("About this App")
st.write(
    "The original CSSE dataset reports cumulative counts over time. "
    "For daily counts, this app computes the difference between consecutive days "
    "within each country. Countries with province-level rows are aggregated into "
    "one country-level total. The optional 7-day rolling average smooths daily "
    "counts by averaging each day with the previous six days."
)

st.write(
    "Data source: Johns Hopkins Center for Systems Science and Engineering "
    "COVID-19 GitHub time-series dataset."
)
