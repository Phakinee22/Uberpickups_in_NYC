import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime
import plotly.express as px


st.title('Uber pickups in NYC')

DATE_COLUMN = 'date/time'
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
            'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

@st.cache_data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

data_load_state = st.text('Loading data...')
data = load_data(10000)
data_load_state.text("Done! (using st.cache_data)")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

st.subheader('Number of pickups by hour')
hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0,24))[0]
st.bar_chart(hist_values)

# Some number in the range 0-23
hour_to_filter = st.slider('hour', 0, 23, 17)
filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]

st.subheader('Map of all pickups at %s:00' % hour_to_filter)
st.map(filtered_data)

if 'interaction_count' not in st.session_state:
    st.session_state.interaction_count = 0

if 'prev_time_mode' not in st.session_state:
    st.session_state.prev_time_mode = None

st.header("Deploy  streamlit app")

st.subheader('Map of all pickups 3D')

available_dates = sorted(data['date/time'].dt.date.unique())
min_date = min(available_dates)
max_date = max(available_dates)

selected_date = st.date_input(
    "Select date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

time_mode = st.radio("Select time", ["Any time period", "A single time period", "Time periods"])

# เงื่อนไขการกรองตามโหมด
if time_mode == "Any time period":
    filtered = data[data['date/time'].dt.date == selected_date]
    time_text = "Any time period"
elif time_mode == "A single time period":
    selected_hour = st.selectbox("Select a single time period", range(24), format_func=lambda x: f"{x:02d}:00")
    filtered = data[
        (data['date/time'].dt.date == selected_date) &
        (data['date/time'].dt.hour == selected_hour)
    ]
    time_text = f"{selected_hour:02d}:00"
elif time_mode == "Time periods":
    start_hour, end_hour = st.slider(
        "Time periods",
        0, 23, (8, 11),
        format="%02d:00"
    )
    filtered = data[
        (data['date/time'].dt.date == selected_date) &
        (data['date/time'].dt.hour >= start_hour) &
        (data['date/time'].dt.hour <= end_hour)
    ]
    time_text = f"{start_hour:02d}:00 - {end_hour:02d}:00"

st.write(f"data {len(filtered)} date {selected_date} time: {time_text}")
midpoint = (filtered["lat"].mean(), filtered["lon"].mean()) if len(filtered) else (40.7128, -74.0060)
st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=midpoint[0],
        longitude=midpoint[1],
        zoom=11,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data=filtered,
            get_position='[lon, lat]',
            radius=200,
            elevation_scale=4,
            elevation_range=[0,1000],
            pickable=True,
            extruded=True,
            coverage=0.6,
            opacity=0.5
        )
    ],
    tooltip={"text": "Number of Pickups"}
))

if st.session_state.prev_time_mode != time_mode:
    st.session_state.interaction_count += 1
    st.session_state.prev_time_mode = time_mode

st.header(f"This page has run {st.session_state.interaction_count} times.")

st.subheader('Number of pickups by hour')
data['hour'] = data[DATE_COLUMN].dt.hour
hour_counts = data['hour'].value_counts().sort_index()
fig = px.scatter(x=hour_counts.index, y=hour_counts.values,
             labels={'x': 'Hour of Day', 'y': 'Number of Pickups'},
             title='Uber Pickups by Hour')
st.plotly_chart(fig)