#!/usr/bin/env python3

import pandas as pd

epsg_wgs84 = 4326


def waterlevel_for_climate(grouped_interpolator_gdf, climate):
    """use the grouped interpolation dataframe and the climate parameters to generate a waterlevel for the points"""

    lobith_gdf = grouped_interpolator_gdf.query('discharge_location == "Lobith"')
    lobith_waterlevels = lobith_gdf["interpolate"].apply(
        lambda x: x(climate["discharge_lobith"])
    )
    # drop interpolate for performance / compatibility
    lobith_result = lobith_gdf.drop(columns=["interpolate"])
    lobith_result["waterlevel"] = lobith_waterlevels

    maas_gdf = grouped_interpolator_gdf.query('discharge_location == "st Pieter"')
    maas_waterlevels = maas_gdf["interpolate"].apply(
        lambda x: x(climate["discharge_st_pieter"])
    )
    # drop interpolate for performance / compatibility
    maas_result = maas_gdf.drop(columns=["interpolate"])
    maas_result["waterlevel"] = maas_waterlevels

    result = pd.concat([lobith_result, maas_result])
    result = result.set_crs(epsg_wgs84)
    return result
