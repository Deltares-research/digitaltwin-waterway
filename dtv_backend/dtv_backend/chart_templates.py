""""Templates for charts."""

# %% Trip duration
trip_duration_template = {
    "title": {"text": "Trip duration", "subtext": "Example data"},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "toolbox": {"show": True, "feature": {"saveAsImage": {}}},
    "xAxis": {"type": "category", "boundaryGap": True, "data": []},
    "yAxis": {
        "type": "value",
        "axisLabel": {"formatter": "{value}"},
        "axisPointer": {"snap": True},
    },
    "visualMap": {
        "show": True,
        "dimension": 1,
        "pieces": [{"lte": 32.98, "color": "green"}, {"gt": 32.98, "color": "red"}],
    },
    "series": [{"name": "Trip duration", "type": "scatter", "data": []}],
}


# %% Breakdown of duration into activities
duration_breakdown_template = {
    "tooltip": {
        "trigger": "item",
        "formatter": "{b} : {c}h ({d}%)"
    },
    "legend": {
        "orient": "vertical",
        "left": "left",
        "data": [],  # data categories
    },
    "series": [{
        "name": "Duration breakdown",
        "type": "pie",
        "radius": "80%",
        "center": ["50%", "50%"],
        "data": [],  # dict value:name (i.e. total duration:category),
        "emphasis": {
            "itemStyle": {
                "shadowBlur": 10,
                "shadowOffsetX": 0,
                "shadowColor": "rgba(0, 0, 0, 0.5)"
            }
        }
    }]
}


# %% Trips
trips_template = {
    "xAxis": {
        "name": "Duration",
        "type": "category",
        "boundaryGap": False,
        "data": [0,1]
    },
    "yAxis": {
        "type": "value",
        "name": "Count"
    },
    "legend": {
        "data": ["Duration [h]"]
    },
    "series": [{
        "name": "Duration [h]",
        "data": [0,1],
        "type": "line",
        "areaStyle": {}
    }]
}
