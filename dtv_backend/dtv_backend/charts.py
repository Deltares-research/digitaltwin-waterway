"""Generate charts"""

import copy

import pandas as pd
import geopandas as gpd
import numpy as np
import plotly.express as px


import dtv_backend.chart_templates


def trip_duration(results):
    """generate trip duration plot in echarts format"""
    # read log features
    gdf = gpd.GeoDataFrame.from_features(results["log"]["features"])

    cycle_idx = np.logical_and(
        gdf["Actor type"] == "Ship", gdf["Name"] == "Cycle")
    selected = gdf[cycle_idx].reset_index(drop=True)
    echart = copy.deepcopy(dtv_backend.chart_templates.trip_duration_template)
    echart["xAxis"]["data"] = selected.index.tolist()
    durations = pd.to_datetime(
        selected["Stop"]) - pd.to_datetime(selected["Start"])
    hours = durations.dt.total_seconds() / 3600
    echart["series"][0]["data"] = hours.tolist()
    return echart


def gantt(results):
    """create a gantt chart"""
    gdf = gpd.GeoDataFrame.from_features(results["log"]["features"])
    fig = px.timeline(
        gdf, x_start="Start", x_end="Stop", y="Name", color="Actor", opacity=0.3
    )

    fig.update_yaxes(autorange="reversed")
    return fig


def duration_breakdown(results):
    """create work breakdown plot in echarts format"""
    # TODO: clean up a bit
    # read log features
    gdf = gpd.GeoDataFrame.from_features(results["log"]["features"])

    # TODO: fix correct filter, waiting, and mixes between logging of vessel and port
    cycle_idx = np.logical_and(
        gdf["Actor type"] == "Ship", gdf["Name"] != "Cycle"
    )
    selected = gdf[cycle_idx].reset_index(drop=True)

    echart = copy.deepcopy(
        dtv_backend.chart_templates.duration_breakdown_template)

    # the legend data
    echart['legend']['data'] = selected['Name'].unique().tolist()

    # the series data
    durations = pd.to_datetime(
        selected["Stop"]) - pd.to_datetime(selected["Start"])
    hours = durations.dt.total_seconds() / 3600
    selected['Duration'] = hours

    df = selected.groupby('Name').sum()
    # TODO: possibly replace line below by renaming columns of df and
    # converting to list of dicts
    data = [{"value": v, "name": k}
            for k, v in df['Duration'].to_dict().items()]

    echart['series'][0]['data'] = data

    return echart


def trips(result):
    """counting the duration of trips"""
    echart = copy.deepcopy(dtv_backend.chart_templates.trips_template)
    
    return echart