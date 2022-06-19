#!/usr/bin/env python3
import functools
import pathlib

import pandas as pd
import scipy.interpolate
import geopandas as gpd

import dtv_backend.fis


src_dir = pathlib.Path(__file__).parent.parent

epsg_utm31n = 32631
epsg_wgs84 = 4326
epsg_rd = 28992

# we need these columns for interpolations
location_columns = [
    "river",
    "vrt_code",
    "vwk_id",
    "km_markering",
    "km_markering_int",
    "discharge_location",
    "geometry",
]
group_columns = [
    "river",
    "vrt_code",
    "vwk_id",
    "km_markering",
    "km_markering_int",
    "discharge_location",
]
value_columns = ["discharge"]
columns = location_columns + value_columns


def value_for_climate(river_interpolator_gdf, climate, value_column="waterlevel"):
    """use the grouped interpolation dataframe and the climate parameters to generate a waterlevel for the points"""

    lobith_gdf = river_interpolator_gdf.query('discharge_location == "Lobith"')
    lobith_values = lobith_gdf["interpolate"].apply(
        lambda x: x(climate["discharge_lobith"])
    )
    # drop interpolate for performance / compatibility
    lobith_result = lobith_gdf.drop(columns=["interpolate"])
    lobith_result[value_column] = lobith_values

    maas_gdf = river_interpolator_gdf.query('discharge_location == "st Pieter"')
    maas_values = maas_gdf["interpolate"].apply(
        lambda x: x(climate["discharge_st_pieter"])
    )
    # drop interpolate for performance / compatibility
    maas_result = maas_gdf.drop(columns=["interpolate"])
    maas_result[value_column] = maas_values

    result = pd.concat([lobith_result, maas_result])
    result = result.set_crs(epsg_wgs84)
    return result


def create_river_interpolator_gdf(river_with_discharges_gdf, value_column="waterlevel"):
    """create interpolation functions per point in the river"""

    # define interpolation function that interpolates between discharge and waterlevel, extrpolate if needed
    def interpolate(df_i):
        interpolator = scipy.interpolate.interp1d(
            df_i["discharge"], df_i[value_column], fill_value="extrapolate"
        )
        return pd.Series({"interpolate": interpolator})

    # group by the group columns and apply the interpolation function
    grouped_interpolator = (
        river_with_discharges_gdf[columns + [value_column]]
        .groupby(group_columns)
        .apply(interpolate)
        .reset_index()
    )
    # lookup the corresponding geometry
    grouped_geometry = (
        river_with_discharges_gdf[location_columns]
        .groupby(group_columns)
        .agg("first")
        .reset_index()
    )
    # merge them back together
    river_interpolator_gdf = pd.merge(
        grouped_interpolator,
        grouped_geometry,
        left_on=group_columns,
        right_on=group_columns,
    )
    return river_interpolator_gdf


def interpolated_values_for_climate(
    climate,
    graph,
    river_interpolator_gdf,
    epsg=epsg_utm31n,
    max_distance=1500,
    value_column="waterlevel",
):
    """compute waterlevels and interpolate onto graph"""

    # use 1500 as max distance because we have a 1km input

    value_gdf = value_for_climate(
        river_interpolator_gdf, climate, value_column=value_column
    )
    value_gdf_utm = value_gdf.to_crs(epsg)
    edges_gdf_utm = dtv_backend.fis.get_edge_gdf(graph, epsg=epsg)

    edges_merged = gpd.sjoin_nearest(
        left_df=edges_gdf_utm,
        right_df=value_gdf_utm,
        how="left",
        max_distance=max_distance,
        lsuffix="left",
        rsuffix="right",
        distance_col="distance",
    )

    columns = [
        "source",
        "target",
        "geometry",
        "km_markering",
        "km_markering_int",
        "discharge_location",
        "distance",
    ] + [value_column]
    result = edges_merged.loc[:, columns].dropna()
    return result


@functools.lru_cache(maxsize=128)
def get_river_with_discharges_gdf(value_column="waterlevel"):
    river_with_discharges_gdf = gpd.read_file(
        src_dir / "data" / f"river_{value_column}.geojson"
    )
    return river_with_discharges_gdf


@functools.lru_cache(maxsize=128)
def get_river_interpolator_gdf(value_column="waterlevel"):
    river_with_discharges_gdf = pd.read_pickle(
        src_dir / "data" / f"river_{value_column}_interpolator_gdf.pickle"
    )
    return river_with_discharges_gdf
