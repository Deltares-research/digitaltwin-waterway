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

    cycle_idx = np.logical_and(gdf["Actor type"] == "Ship", gdf["Name"] == "Cycle")
    selected = gdf[cycle_idx].reset_index(drop=True)
    echart = copy.deepcopy(dtv_backend.chart_templates.trip_duration_template)
    echart["xAxis"]["data"] = selected.index.tolist()
    durations = pd.to_datetime(selected["Stop"]) - pd.to_datetime(selected["Start"])
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
