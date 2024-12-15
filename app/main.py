import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import world_bank_data as wb

from pymongo import MongoClient
from makeMainDB import DBCreator

# MongoDB конфигурация
MONGO_URI = "mongodb://mongo:27017"
DB_NAME = "indicators_database"
COLLECTION_HEADERS  = "headers"
COLLECTION_MAIN_DATA = "main_data"

def visualizer():
    st.title("World Bank Data Visualization")
    
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection_headers = db[COLLECTION_HEADERS]
    collection_main_data = db[COLLECTION_MAIN_DATA]

    indicators_options = list(set(collection_headers.distinct("name")))

    selected_name = st.selectbox(
        "Выберите название индикатора",
        indicators_options,
        index=None
    )

    countries = list(set(collection_main_data.distinct("Country")))
    
    selected_countries = st.multiselect(
        "Выберите страну",
        countries
    )

    selected_date_interval = st.date_input(
        "Выберите даты",
        (datetime.date(2000, 1, 1), datetime.date(2024, 12, 31)),
        format="DD.MM.YYYY"
    )
    start_date, end_date = str(selected_date_interval[0].year), str(selected_date_interval[1].year)
    
    plot_type = ["line", "scatter", "hist", "bar", "geo"]
    selected_type = st.selectbox(
            "Выберите тип графика",
            plot_type,
            index=None
    )

    query_filter = {
                     "indicator_name" : selected_name, 
                     "Year" : {"$gte": start_date, "$lte": end_date},
                     "Country" : {"$in": selected_countries}
                   }

    db_data = collection_main_data.find(query_filter)
    pd_data = pd.DataFrame(list(db_data))

    if '_id' in pd_data.columns:
        pd_data = pd_data.drop('_id', axis=1)
    
    # Визуализация данных
    match selected_type:
        case "line":
            fig = px.line(
                pd_data, 
                x="Year", 
                y="Y", 
                color="Country", 
                title=selected_name
            )
            st.plotly_chart(fig, use_container_width=True)
        case "scatter":
            fig = px.scatter(
                pd_data, 
                x="Year", 
                y="Y",
                color="Country",
                title=selected_name
            )
            st.plotly_chart(fig, use_container_width=True)
        case "hist":
            fig = px.histogram(
                pd_data,
                x="Y",
                nbins=20,
                title=selected_name
            )
            st.plotly_chart(fig, use_container_width=True)
        case "bar":
            fig = px.bar(
                pd_data,
                x="Year",
                y="Y",
                title=selected_name
            )
            st.plotly_chart(fig, use_container_width=True)
        case "geo":
            fig = px.choropleth(
                pd_data,
                locations="Country",
                locationmode="country names",
                color="Y",
                color_continuous_scale="Viridis",
                title=selected_name
            )
            
            fig.update_geos(
                showcoastlines=True,
                showcountries=True,
                fitbounds="locations"
            )
            st.plotly_chart(fig, use_container_width=True)

visualizer()
