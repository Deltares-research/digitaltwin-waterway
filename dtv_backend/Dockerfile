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

RUN conda install mamba -c conda-forge


RUN mamba install -y -c conda-forge git  pip diskcache click geojson geopandas networkx numpy pandas pyproj requests scipy setuptools shapely geos pygeos tqdm jupyter notebook jupyterlab ipython flask flask-cors requests-cache
RUN mamba install -y -c conda-forge pint plotly gunicorn pyyaml

# # The rest with pip
COPY . $HOME/app

WORKDIR $HOME/app
# this is faster
RUN pip install simpy timeboard
ENV PATH /opt/conda/bin:$PATH
RUN pip install -e .

EXPOSE 5000

# CMD gunicorn --capture-output --log-level info --error-logfile="-"  --access-logfile="-" -w 4 -b 0.0.0.0:5000 "dtv_backend.server:create_app()"
CMD dtv_backend run --port 5000 --host 0.0.0.0 --no-debugger
