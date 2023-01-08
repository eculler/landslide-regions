# Use an official Python runtime as a parent image
FROM continuumio/miniconda3

WORKDIR /gis

RUN apt-get update && apt-get install -y gdb

COPY environment.yml /gis
RUN conda env create -f /gis/environment.yml
ENV PATH /opt/conda/envs/gisenv/bin:$PATH
RUN /bin/bash -c "source activate gisenv"

COPY src /gis/src
COPY gages_active.txt /gis/data/
