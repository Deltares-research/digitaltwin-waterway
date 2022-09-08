""""Templates for charts"""

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
