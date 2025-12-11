"""
Functionalities for generating charts.
"""

import copy

import pandas as pd
import geopandas as gpd
import numpy as np
import plotly.express as px

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


import dtv_backend.chart_templates

plt.style.use("dark_background")


def trip_duration(results):
    """
    Generate trip duration plot in echarts format.

    Parameters
    ----------
    results : dict
        Results dictionary from simulation.

    Returns
    -------
    echart : dict
        Echarts JSON-like dictionary for trip duration plot.
    """
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
    """
    Create a gantt chart.

    Parameters
    ----------
    results : dict
        Results dictionary from simulation.

    Returns
    -------
    fig : plotly.graph_objs._figure.Figure
        Gantt chart figure.
    """
    gdf = gpd.GeoDataFrame.from_features(results["log"]["features"])
    fig = px.timeline(
        gdf, x_start="Start", x_end="Stop", y="Name", color="Actor", opacity=0.3
    )

    fig.update_yaxes(autorange="reversed")
    return fig


def duration_breakdown(results):
    """
    Create work breakdown plot in echarts format.

    Parameters
    ----------
    results : dict
        Results dictionary from simulation.
    
    Returns
    -------
    echart : dict
        Echarts JSON-like dictionary for duration breakdown plot.
    """
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
    """
    Histogram of the duration of trips.

    Parameters
    ----------
    results : dict
        Results dictionary from simulation.

    Returns
    -------
    echart : dict
        Echarts JSON-like dictionary for trip histogram plot.
    """


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
    """
    Energy per time.

    Parameters
    ----------
    results : dict
        Results dictionary from simulation.

    Returns
    -------
    echart : dict
        Echarts JSON-like dictionary for energy per time plot.
    """

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
    """
    Energy per distance.

    Parameters
    ----------
    results : dict
        Results dictionary from simulation.

    Returns
    -------
    echart : dict
        Echarts JSON-like dictionary for energy per distance plot.
    """

    # get the template
    echart = copy.deepcopy(dtv_backend.chart_templates.energy_per_distance_template)

    # convert log to geodataframe
    energy_gdf = gpd.GeoDataFrame.from_features(results["energy_log"]["features"])

    rows = np.c_[
        energy_gdf["distance"].cumsum(), energy_gdf["energy"] / energy_gdf["distance"]
    ].tolist()

    echart["series"][0]["data"] = rows

    return echart


def route_gdf_from_config(config):
    """
    Create route geodataframe with quantities from config.

    Parameters
    ----------
    config : dict
        Configuration dictionary.

    Returns
    -------
    route_gdf : gpd.GeoDataFrame
        Route geodataframe with quantities.
    """
    route_gdf = gpd.GeoDataFrame.from_features(config["route"])

    waterlevel_gdf = gpd.GeoDataFrame.from_features(
        config["quantities"]["waterlevels"]["features"]
    )
    depth_gdf = gpd.GeoDataFrame.from_features(
        config["quantities"]["bathymetry"]["features"]
    )
    velocity_gdf = gpd.GeoDataFrame.from_features(
        config["quantities"]["velocities"]["features"]
    )

    route_gdf["e_sorted"] = route_gdf["e"].apply(lambda e: tuple(sorted(e)))
    waterlevel_gdf["e_sorted"] = waterlevel_gdf.apply(
        lambda row: tuple(sorted([row["source"], row["target"]])), axis=1
    )
    depth_gdf["e_sorted"] = depth_gdf.apply(
        lambda row: tuple(sorted([row["source"], row["target"]])), axis=1
    )
    velocity_gdf["e_sorted"] = velocity_gdf.apply(
        lambda row: tuple(sorted([row["source"], row["target"]])), axis=1
    )

    route_gdf = route_gdf.set_index("e_sorted")
    waterlevel_gdf = waterlevel_gdf.set_index("e_sorted")
    depth_gdf = depth_gdf.set_index("e_sorted")
    velocity_gdf = velocity_gdf.set_index("e_sorted")

    merged_gdf = pd.merge(
        route_gdf,
        waterlevel_gdf["waterlevel"],
        left_index=True,
        right_index=True,
        how="left",
    )
    merged_gdf = pd.merge(
        merged_gdf,
        depth_gdf[["nap_p5", "nap_p50", "nap_p95", "lat_p5", "lat_p50", "lat_p95"]],
        left_index=True,
        right_index=True,
        how="left",
    )
    merged_gdf = pd.merge(
        merged_gdf,
        velocity_gdf["velocity"],
        left_index=True,
        right_index=True,
        how="left",
    )

    route_gdf = merged_gdf.sort_values("length_m_cumsum")
    return route_gdf


def route_profile(config):
    """
    Create route profile plot.

    Parameters
    ----------
    config : dict
        Configuration dictionary.

    Returns
    -------
    fig : matplotlib.figure.Figure
        Route profile figure.
    axes : np.ndarray
        Axes of the route profile figure.
    """
    
    route_gdf = route_gdf_from_config(config)
    structures_gdf = route_gdf[~route_gdf["structure"].isna()]
    structures_gdf = structures_gdf.merge(
        structures_gdf.apply(lambda row: pd.Series(row["structure"]), axis=1),
        left_index=True,
        right_index=True,
    )
    bridges_gdf = structures_gdf.query('structure_type == "Bridge"')

    fig, axes = plt.subplots(
        figsize=(13, 8), nrows=2, sharex=True, gridspec_kw=dict(height_ratios=[3, 1])
    )

    ax = axes[0]
    earth_color = "#DBA85C"
    water_color = "#bbbbff"

    length_km = route_gdf["length_m_cumsum"] / 1000

    ax.fill_between(
        length_km,
        route_gdf["nap_p5"],
        route_gdf["nap_p95"],
        alpha=0.3,
        color=earth_color,
    )
    ax.plot(length_km, route_gdf["nap_p5"], color=earth_color, label="Depth 5%")

    ax.fill_between(
        length_km,
        route_gdf["nap_p95"],
        route_gdf["waterlevel"],
        alpha=0.3,
        color=water_color,
    )

    ax.plot(length_km, route_gdf["waterlevel"], color=water_color, label="Waterlevel")

    ax.plot(
        bridges_gdf.length_m_cumsum / 1000,
        bridges_gdf["waterlevel"],
        "k.",
        alpha=0.5,
        label="Bridge",
    )
    ax.set_xlabel("Route length [km]")
    ax.set_ylabel("Height [m w.r.t. NAP]")
    ax.legend(loc="best")

    ax = axes[1]
    ax.plot(length_km, route_gdf["velocity"])
    ax.set_ylabel("Velocity [m/s]")

    fig.tight_layout()

    return fig, axes


def gantt(results):
    """
    Create gantt chart.

    Parameters
    ----------
    results : dict
        Results dictionary from simulation.

    Returns
    -------
    fig : plotly.graph_objs._figure.Figure
        Gantt chart figure.
    """
    log_gdf = gpd.GeoDataFrame.from_features(results["log"])
    fig = px.timeline(
        log_gdf,
        x_start="Start",
        x_end="Stop",
        y="Name",
        color="Actor",
        opacity=0.3,
        template="plotly_dark",
    )

    fig.update_yaxes(autorange="reversed")
    return fig
