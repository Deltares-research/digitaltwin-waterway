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
    "km_markering",
    "km_markering_int",
    "discharge_location",
    "geometry",
]
group_columns = [
    "river",
    "km_markering",
    "km_markering_int",
    "discharge_location",
]
value_columns = ["discharge"]
columns = location_columns + value_columns


def value_for_climate(river_interpolator_gdf, climate, value_column="waterlevel"):
    """use the grouped interpolation dataframe and the climate parameters to generate a waterlevel for the points"""

    lobith_gdf = river_interpolator_gdf.query('discharge_location == "Lobith"')
    lobith_values = (
        lobith_gdf["interpolate"]
        .apply(lambda x: x(climate["discharge_lobith"]))
        .astype("float")
    )
    # drop interpolate for performance / compatibility
    lobith_result = lobith_gdf.drop(columns=["interpolate"])
    lobith_result[value_column] = lobith_values

    maas_gdf = river_interpolator_gdf.query('discharge_location == "st Pieter"')
    maas_values = (
        maas_gdf["interpolate"]
        .apply(lambda x: x(climate["discharge_st_pieter"]))
        .astype("float")
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

    # ensure we have a geopandas data frame
    river_interpolator_gdf = gpd.GeoDataFrame(
        river_interpolator_gdf, geometry="geometry"
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
    edges_gdf_utm = dtv_backend.fis.get_edges_gdf(graph).to_crs(epsg)

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
    # ensure we have a geodataframe
    river_with_discharges_gdf = gpd.GeoDataFrame(
        river_with_discharges_gdf, geometry=river_with_discharges_gdf["geometry"]
    )
    return river_with_discharges_gdf


@functools.lru_cache(maxsize=128)
def get_interpolators():
    """return a dictionary of quantity: interpolator"""
    value_columns = ["velocity", "waterlevel"]
    interpolators = {}

    src_path = dtv_backend.get_src_path()

    for value_column in value_columns:
        river_gdf = gpd.read_file(src_path / "data" / f"river_{value_column}.geojson")
        interpolator_gdf = dtv_backend.climate.create_river_interpolator_gdf(
            river_gdf, value_column=value_column
        )
        interpolators[value_column] = interpolator_gdf
    return interpolators


def get_variables_for_climate(climate, interpolators, edges_gdf, max_distance=1500):
    """use the climate interpolators to get waterlevels, velocities and bathymetry for the network"""
    # TODO: filter by route first

    # Interpolate values for the current variable (for example for discharge 1000 @ Lobith)
    values_utm = {}
    for value_column, interpolator_gdf in interpolators.items():
        # these are the variables for the current climate (for example waterlevels at each location)
        value_gdf = value_for_climate(
            interpolator_gdf, climate, value_column=value_column
        )
        # We need to interpolate spatial. We'll do it in meters.
        # For EU or other country networks, we need to this on the sphere
        values_utm[value_column] = value_gdf.to_crs(epsg_utm31n)

    # conver to utm for spatial matching
    edges_gdf_with_variables_gdf = edges_gdf.to_crs(epsg_utm31n)

    # merge computed variables with graph
    # lookup the nearest waterlevel
    for variable in ["velocity", "waterlevel"]:
        edges_gdf_with_variables_gdf = gpd.sjoin_nearest(
            left_df=edges_gdf_with_variables_gdf,
            right_df=values_utm[variable][["geometry", variable]],
            how="left",
            max_distance=max_distance,
            lsuffix="left",
            rsuffix="right",
        )
        # remove created index columns
        if "index_right" in edges_gdf_with_variables_gdf.columns:
            edges_gdf_with_variables_gdf.drop(columns=["index_right"], inplace=True)
        if "index_left" in edges_gdf_with_variables_gdf.columns:
            edges_gdf_with_variables_gdf.drop(columns=["index_left"], inplace=True)

    columns = [
        "source",
        "target",
        "length_m",
        "geometry",
        "velocity",
        "waterlevel",
        "nap_p5",
        "nap_p50",
        "nap_p95",
        "lat_p5",
        "lat_p50",
        "lat_p95",
    ]
    result_utm = edges_gdf_with_variables_gdf[columns]
    # if none of these variables are available, drop the row

    result_utm = result_utm.dropna(
        subset=["nap_p50", "velocity", "waterlevel"], how="all"
    )

    # project back to wgs84 and return
    result = result_utm.to_crs(4326)
    return result
