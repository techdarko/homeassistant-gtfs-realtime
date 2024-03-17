# syntax = docker/dockerfile:1.0-experimental
FROM homeassistant/home-assistant:2024.3
# Copy Application and Resources
COPY custom_components/gtfs_realtime custom_components/gtfs_realtime
COPY resources/NYCT_Bullets www/NYCT_Bullets

# Install requirements directly from the manifest
RUN cat custom_components/gtfs_realtime/manifest.json |  jq -r  '.requirements | .[]' | xargs pip install

# Generate the hass config
ARG STOP_IDS
ARG ROUTE_IDS
ENV GTFS_REALTIME_CONFIG=configuration.yaml

RUN mkdir -p /gtfs_realtime_config 
RUN echo "default_config:" >> ${GTFS_REALTIME_CONFIG}
RUN echo "" >> ${GTFS_REALTIME_CONFIG}
RUN --mount=type=secret,id=api_key \
    python -m custom_components.gtfs_realtime.feeds nyc.subway \
    --stops $STOP_IDS \
    --routes $ROUTE_IDS \
    --route-icons /local/NYCT_Bullets \
    --api-key=$(cat /run/secrets/api_key) >> ${GTFS_REALTIME_CONFIG}

ARG USER
RUN --mount=type=secret,id=password \
    hass -c . --script auth add ${USER} $(cat /run/secrets/password)