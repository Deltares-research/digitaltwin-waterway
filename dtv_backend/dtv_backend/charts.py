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


def duration_breakdown(results):
    """create work breakdown plot in echarts format"""
    # read log features
    gdf = gpd.GeoDataFrame.from_features(results["log"]["features"])

    # filter on the desired activities
    cycle_idx = (
        (gdf["Actor type"] != "Operator")
        & (gdf["Name"] != "Cycle")
        & (~gdf["Name"].str.lower().str.contains("request"))
    )
    selected = gdf[cycle_idx].reset_index(drop=True)

    # make a copy of the echart template
    echart = copy.deepcopy(dtv_backend.chart_templates.duration_breakdown_template)

    # the legend data
    echart["legend"]["data"] = selected["Name"].unique().tolist()

    # the series data
    durations = pd.to_datetime(selected["Stop"]) - pd.to_datetime(selected["Start"])
    hours = durations.dt.total_seconds() / 3600
    selected["Duration"] = hours

    df = selected.groupby("Name").sum(numeric_only=True)
    data = [{"value": v, "name": k} for k, v in df["Duration"].to_dict().items()]

    echart["series"][0]["data"] = data

    return echart


def trip_histogram(results):
    """histogram of the duration of trips"""

    # get the template
    echart = copy.deepcopy(dtv_backend.chart_templates.trips_template)

    # convert log to geodataframe
    gdf = gpd.GeoDataFrame.from_features(results["log"]["features"])

    # we're only counting cycles
    cycle_idx = np.logical_and(gdf["Actor type"] == "Ship", gdf["Name"] == "Cycle")
    selected = gdf[cycle_idx].reset_index(drop=True)
    durations = pd.to_datetime(selected["Stop"]) - pd.to_datetime(selected["Start"])
    hours = durations.dt.total_seconds() / 3600

    # make somewhat pretty bins
    bins = np.histogram_bin_edges(hours, bins="sturges")
    bins = np.unique(np.ceil(bins)).astype("int")
    # add the lower bin
    min_hours = np.floor(hours.min()).astype("int")

    # compute the histogram
    counts, bins = np.histogram(hours.tolist(), [min_hours] + bins.tolist())

    # fill in the template
    echart["xAxis"]["data"] = bins.tolist()
    echart["series"][0]["data"] = counts.tolist()

    return echart


def energy_per_time(results):
    """energy per time"""

    # get the template
    echart = copy.deepcopy(dtv_backend.chart_templates.energy_per_time_template)

    # convert log to geodataframe
    energy_gdf = gpd.GeoDataFrame.from_features(results["energy_log"]["features"])

    rows = np.c_[
        energy_gdf["t"], energy_gdf["energy"] / energy_gdf["distance"]
    ].tolist()

    echart["series"][0]["data"] = rows

    return echart


def energy_per_distance(results):
    """energy per distance"""

    # get the template
    echart = copy.deepcopy(dtv_backend.chart_templates.energy_per_distance_template)

    # convert log to geodataframe
    energy_gdf = gpd.GeoDataFrame.from_features(results["energy_log"]["features"])

    rows = np.c_[
        energy_gdf["distance"].cumsum(), energy_gdf["energy"] / energy_gdf["distance"]
    ].tolist()

    echart["series"][0]["data"] = rows

    return echart
