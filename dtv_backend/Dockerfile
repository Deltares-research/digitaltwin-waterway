FROM continuumio/miniconda3
LABEL maintainer="Cindy.vandeVriesSafaviNic@deltares.nl"
USER root

WORKDIR /root

# Do not bother with equestions
ENV DEBIAN_FRONTEND=noninteractive
# update system and install dependencies
RUN apt update \
    && apt install -y \
    davfs2  \
    vim \
    wget \
    curl \
    sudo \
    locales \
    fonts-liberation \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


# Update conda base environment
RUN conda update -n base -c defaults conda


# # The rest with pip
COPY . $HOME/app

WORKDIR $HOME/app
# this is faster
RUN conda install --override-channels -c conda-forge git  pip diskcache click geojson geopandas networkx numpy pandas pyproj requests scipy setuptools shapely geos tqdm jupyter notebook jupyterlab ipython
RUN pip install simpy
ENV PATH /opt/conda/bin:$PATH
RUN pip install -e .



CMD dtv_backend simulate test/test-01/config.json
