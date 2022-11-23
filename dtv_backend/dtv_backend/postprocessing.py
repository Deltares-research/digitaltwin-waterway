"""Routines for postprocessing the results of OpenCLSim/OpenTNSim"""
import json

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely.wkt
import random

import plotly.graph_objs as go
from plotly.offline import init_notebook_mode, iplot
import plotly.express as px


def log2gantt(log_df):
    """convert log data frame to a gantt chart"""
    log_df["actor_name"] = log_df["Meta"].apply(lambda x: x["actor"].name)
    log_df["state"] = log_df["Meta"].apply(lambda x: x["state"])
    gantt_df = pd.DataFrame(
        log_df.pivot(index="ActivityID", columns="state")[
            [
                ("Timestamp", "START"),
                ("Timestamp", "STOP"),
                ("Message", "START"),
                ("actor_name", "START"),
            ]
        ].values,
        columns=["Start", "Stop", "Name", "Actor"],
    )
    # TODO: check why operator cycle ends with NaN
    gantt_df = gantt_df.dropna()
    # add proper gantt chart headers
    gantt_df = gantt_df.query('Name != "Cycle"')
    gantt_df = gantt_df.sort_values(["Start", "Name"])
    fig = px.timeline(
        gantt_df, x_start="Start", x_end="Stop", y="Name", color="Actor", opacity=0.3
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def log2json(log_df):
    """convert a log dataframe to a pivoted geojson"""
    log_df["actor_name"] = log_df["Meta"].apply(lambda x: x["actor"].name)
    log_df["actor_type"] = log_df["Meta"].apply(lambda x: type(x["actor"]).__name__)
    log_df["state"] = log_df["Meta"].apply(lambda x: x["state"])
    log_df["description"] = log_df["Meta"].apply(lambda x: x["description"])

    # rename to these columns
    columns = [
        "Start",
        "Stop",
        "Name",
        "Description",
        "Actor",
        "Actor type",
        "Geometry",
    ]
    pivot_df = pd.DataFrame(
        # the pivot creates a multi-index, pick to create a single index
        log_df.pivot(index="ActivityID", columns="state")[
            [
                ("Timestamp", "START"),
                ("Timestamp", "STOP"),
                ("Message", "START"),
                ("description", "START"),
                ("actor_name", "START"),
                ("actor_type", "START"),
                ("geometry", "START"),
            ]
        ].values,
        columns=columns,
    )

    pivot_df["Start Timestamp"] = pivot_df["Start"].values.astype(np.int64) // 10**9
    pivot_df["Stop Timestamp"] = pivot_df["Stop"].values.astype(np.int64) // 10**9

    export_columns = [*columns, "Start Timestamp", "Stop Timestamp"]
    pivot_df["Start"] = pivot_df["Start"].dt.strftime("%Y-%m-%d %H:%M:%S")
    pivot_df["Stop"] = pivot_df["Stop"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # make geometry consistent
    geometry = pivot_df["Geometry"].apply(
        lambda x: shapely.geometry.shape(x)
        if (hasattr(x, "geom_type") or isinstance(x, dict))
        else None
    )
    pivot_df["Geometry"] = geometry
    pivot_df = gpd.GeoDataFrame(pivot_df[export_columns], geometry="Geometry")

    # drop missings
    # TODO: fix the cause of these missings
    pivot_df = pivot_df[~pivot_df["Name"].isna()]

    json_str = pivot_df.to_json()
    return json.loads(json_str)


#%% Visualization of vessel planning
def get_colors(n):
    """Get random colors for the activities."""
    ret = []
    r = int(random.random() * 256)
    g = int(random.random() * 256)
    b = int(random.random() * 256)
    step = 256 / n
    for i in range(n):
        r += step
        g += step
        b += step
        r = int(r) % 256
        g = int(g) % 256
        b = int(b) % 256
        ret.append((r, g, b))
    return ret


def get_segments(df, activity, y_val):
    """Extract 'start' and 'stop' of activities from log."""
    x = []
    y = []
    for i in range(len(df)):
        if "START" in df["activity_state"][i] and df["log_string"][i] == activity:
            start = df.index[i]
        elif "STOP" in df["activity_state"][i] and df["log_string"][i] == activity:
            x.extend((start, start, df.index[i], df.index[i], df.index[i]))
            y.extend((y_val, y_val, y_val, y_val, None))
    return x, y


def vessel_planning(
    vessels, activities=None, colors=None, web=False, static=False, y_scale="text"
):
    """Create a plot of the planning of vessels."""

    if activities is None:
        activities = []
        for obj in vessels:
            activities.extend(set(obj.log["Message"]))

    if colors is None:
        C = get_colors(len(activities))
        colors = {}
        for i in range(len(activities)):
            colors[i] = f"rgb({C[i][0]},{C[i][1]},{C[i][2]})"

    # organise logdata into 'dataframes'
    dataframes = []
    names = []
    for vessel in vessels:
        if len(vessel.log["Timestamp"]) > 0:
            df = pd.DataFrame(
                {
                    "log_value": vessel.log["Value"],
                    "log_string": vessel.log["Message"],
                    "activity_state": vessel.log["ActivityState"],
                },
                vessel.log["Timestamp"],
            )
            dataframes.append(df)
            names.append(vessel.name)

    df = dataframes[0]

    # prepare traces for each of the activities
    traces = []
    for i, activity in enumerate(activities):
        x_combined = []
        y_combined = []
        for k, df in enumerate(dataframes):
            y_val = -k if y_scale == "numbers" else names[k]
            x, y = get_segments(df, activity=activity, y_val=y_val)
            x_combined.extend(x)
            y_combined.extend(y)
        traces.append(
            go.Scatter(
                name=activity,
                x=x_combined,
                y=y_combined,
                mode="lines",
                hoverinfo="y+name",
                line=dict(color=colors[i], width=10),
                connectgaps=False,
            )
        )

    timestamps = []
    logs = [o.log["Timestamp"] for o in vessels]
    for log in logs:
        timestamps.extend(log)

    layout = go.Layout(
        title="Vessel planning",
        hovermode="closest",
        legend=dict(x=0, y=-0.2, orientation="h"),
        xaxis=dict(
            title="Time",
            titlefont=dict(family="Courier New, monospace", size=18, color="#7f7f7f"),
            range=[min(timestamps), max(timestamps)],
        ),
        yaxis=dict(
            title="Vessels",
            titlefont=dict(family="Courier New, monospace", size=18, color="#7f7f7f"),
        ),
    )

    if static is False:
        init_notebook_mode(connected=True)
        fig = go.Figure(data=traces, layout=layout)

        return iplot(fig, filename="news-source")
    else:
        return {"data": traces, "layout": layout}


def energy_gdf_from_log_df(log_df):
    """extract the energy log in geodataframe format from the log dataframe"""
    # append all energy logs together

    def row2energy_df(row):
        """create an energy dataframe for a sailing message"""
        energy_df_i = pd.DataFrame(row["Meta"]["energy_profile"])
        return energy_df_i

    # lookup all stop messages
    sailing_stop_idx = np.logical_and(
        log_df["Message"] == "Sailing",
        log_df["Meta"].apply(lambda x: x["state"]) == "STOP",
    )

    stop_messages = log_df[sailing_stop_idx]
    # from each stop message get the energy_profile
    energy_df = pd.concat(
        stop_messages.apply(row2energy_df, axis=1).values
    ).reset_index(drop=True)
    energy_gdf = gpd.GeoDataFrame(energy_df)

    return energy_gdf


def energy_gdf_to_json(energy_gdf):
    """convert the energy log to json"""
    # drop this column. Too big and unserializable due to extra geometry
    energy_gdf = energy_gdf.drop(columns=["edge"])
    # Time as string in json
    energy_gdf["t"] = energy_gdf["t"].dt.strftime("%Y-%m-%d %H:%M:%S")
    energy_json_str = energy_gdf.to_json()
    energy_json = json.loads(energy_json_str)
    return energy_json
