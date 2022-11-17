#
# Builder process that copies from any docker images to any target docker image
# They could be based on any based linux distribution. That is why we have more
# intermediate stages so we don't need to install any software on the upstream
# and target images.
#
# For each new and previous versions
#
# For each new and previous versions create new base docker build stage:
# - simply define upstrem base image
#
# For each new and previous docker build stage:
# - copy static assets from base image
# - remove (absolute) symbolic links
# - overwrite each symbolic link with the target file content
#
# Create a new merger docker build stage, one for each service:
# - install rdfind
# - copy static assets from previous stage
# - copy static assets from new stage
# - find duplicate static assets from next and previous folders and replice duplicates with 
#   symbolic links
# - force change onership of files to be read for all because the target image can use different
#   users to serve the files
#
# Target docker build stage
# - It only copies the static assets from all the merger stages.
#

#
# New version docker stages
#
{% for service in docker_swarm_build_web_server_services %}
# Simply define upstream base image for service: {{ service.service }}
FROM {{ service.docker_image }} as {{ ( service.service + '_basenew' ) | replace("_", "") }}

{% endfor %}

{% for service in docker_swarm_build_web_server_services %}
# Service: {{ service.service }}
FROM docker.io/debian:bullseye-20221114-slim as {{ ( service.service + '_new' ) | replace("_", "") }}
{% for folder in service.folders %}
# copy static assets from base image
COPY --from={{ ( service.service + '_basenew' ) | replace("_", "") }} {{ folder.folder }} {{ folder.folder }}
# remove (absolute) symbolic links and overwrite each symbolic link with the target file content
RUN find {{ folder.folder }} -type l -exec bash -c "cp --remove-destination \$(readlink -f {}) {} " \;
{% endfor %}

{% endfor %}

#
# Previous version docker stages
#
{% for service in docker_swarm_service_info_result.results %}
{% if service.service.Spec is defined %}
FROM {{ service.service.Spec.TaskTemplate.ContainerSpec.Image }} as {{ ( service.item.service + '_baseprevious' ) | replace("_", "") }}
{% endif %}

{% endfor %}

{% for service in docker_swarm_service_info_result.results %}
{% if service.service.Spec is defined %}
# Simply define upstream base image for service: {{ service.item.service }}

FROM docker.io/debian:bullseye-20221114-slim as {{ ( service.item.service + '_previous' ) | replace("_", "") }}
{% for folder in service.item.folders %}
# copy static assets from base image
COPY --from={{ ( service.item.service + '_baseprevious' ) | replace("_", "") }} {{ folder.folder }} {{ folder.folder }}
# remove (absolute) symbolic links and overwrite each symbolic link with the target file content
RUN find {{ folder.folder }} -type l -exec bash -c "cp --remove-destination \$(readlink -f {}) {} " \;
{% endfor %}

{% endif %}
{% endfor %}

#
# Intermediate stages per service. It merge static assets from previous and next release version
#
#

{% for service in docker_swarm_service_info_result.results %}
# service: {{ service.item.service }}
FROM docker.io/debian:bullseye-20221114-slim as {{ ( service.item.service + '_merger' ) | replace("_", "") }}

# Install rdfind tool
RUN apt-get update && \
    apt-get install -y \
    rdfind && \
    rm -rf /var/lib/apt/lists/*

{% if service.service.Spec is defined %}
{% for folder in service.item.folders %}
# copy static assets from previous stage
COPY --from={{ ( service.item.service + '_previous' ) | replace("_", "") }} {{ folder.folder }} {{ folder.previous }}
{% endfor %}
{% endif %}
{% for folder in service.item.folders %}
# copy static assets from new stage
COPY --from={{ ( service.item.service + '_new' ) | replace("_", "") }} {{ folder.folder }} {{ folder.next }}

{% if service.service.Spec is defined %}
# find duplicate static assets from next and previous folders and replice duplicates with symbolic links
RUN rdfind -makesymlinks true {% for folder in service.item.folders %}{{ folder.next }} {% endfor %}{% if service.service.Spec is defined %}{% for folder in service.item.folders %}{{ folder.previous }} {% endfor %}{% endif %}

# force change onership of files to be read for all because the target image can use different
# users to serve the files.
RUN chown -R 644 {% for folder in service.item.folders %}{{ folder.next }} {% endfor %}{% if service.service.Spec is defined %}{% for folder in service.item.folders %}{{ folder.previous }} {% endfor %}{% endif %}
{% endif %}

{% endfor %}
{% endfor %}

#
# Target docker build stage
# It only copies the static assets from the merger stages.
#
FROM {{ docker_swarm_build_web_server_docker_image_from }} as target

{% for service in docker_swarm_service_info_result.results %}
# service: {{ service.item.service }}
{% if service.service.Spec is defined %}
{% for folder in service.item.folders %}
COPY --from={{ ( service.item.service + '_merger' ) | replace("_", "") }} {{ folder.previous }} {{ folder.previous }}
{% endfor %}
{% endif %}
{% for folder in service.item.folders %}
COPY --from={{ ( service.item.service + '_merger' ) | replace("_", "") }} {{ folder.next }} {{ folder.next }}
{% endfor %}

{% endfor %}
