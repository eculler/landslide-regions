library(readr)
library(dplyr)
library(tidyr)
library(purrr)
library(stringr)
library(lubridate)

library(ggplot2)

library(rgdal)
library(raster)

## Load landslides -------------
rain.triggers <- c('rain', 'downpour', 'flooding', 
                   'continuous_rain', 'tropical_cyclone')
slide.raw <- read_csv('glc_plus_slope.csv',
                      guess_max=100000,
                      na=c("", "unknown"),
                      col_types = list(
                        landslide_size = col_factor(
                          c("small", "medium", "large", "very_large", "catastrophic"), 
                          ordered = TRUE),
                        location_accuracy = col_factor(
                          c("exact", "1km", "5km", "10km", "25km", "50km"),
                          ordered=TRUE),
                        landslide_trigger = col_factor(NULL),
                        landslide_category = col_factor(NULL),
                        landslide_setting = col_factor(NULL),
                        event_date = col_datetime()
                      )
) %>% 
  filter(landslide_trigger %in% rain.triggers) %>%
  droplevels()

## Load Population Data -------------
pop.uri <- 'data/population/gpw-v4_pop_density_0-05_nodata.tif'
pop.ds <- raster(pop.uri)
pop.spdf <- as(pop.ds, "SpatialPixelsDataFrame")
pop.df <- as.data.frame(pop.spdf) %>%
  mutate(population.density = gpw.v4_pop_density_0.05_nodata,
         longitude=x, latitude=y,
         x = floor((longitude + 180) / 0.25), 
         y = floor((latitude + 90) / 0.25))

## Generate population spatial lag dataset -------------
pop.dist <- pointDistance(pop.spdf, lonlat=T)
pop.ordered <- t(apply(pop.dist, 1, order))
pop.near <- pop.ordered[,2:441]
pop.n <- nrow(pop.spdf)
pop.rowcols <- cbind(rep(1:pop.n, each=440), as.vector(t(pop.near)))
pop.adj <- pop.dist * 0
pop.dist[is.na(pop.dist)]=0
pop.dist.sym <- pop.dist + t(pop.dist)
pop.weights <- 1/pop.dist.sym
