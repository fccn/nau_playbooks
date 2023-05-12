#
# Builder process that copies from any docker images to any target docker image
# They could be based on any based linux distribution. That is why we have more
# intermediate stages so we don't need to install any software on the upstream
# and target images.
#
# 1. Definition phase
# 2. Build phase
# 3. Target phase

#
# Definition phase
#
{% for service in build_web_server_services %}
# Simply define upstream base image for service: {{ service.service }}
FROM {{ service.docker_image }} as {{ ( service.service + 'definition' ) | replace("_", "") }}

{% endfor %}

#
# Build phase
# - Copy from the definition phase
# - Remove deduplication
# - Move to destination folder
# - Run deduplication
# - Change file ownership
#
{% for service in build_web_server_services %}
# Service: {{ service.service }}
FROM docker.io/debian:bullseye-20221114-slim as {{ ( service.service + 'build' ) | replace("_", "") }}

# Install rdfind tool
RUN apt-get update && \
    apt-get install -y \
    rdfind && \
    rm -rf /var/lib/apt/lists/*

# copy static assets from base image
COPY --from={{ ( service.service + 'definition' ) | replace("_", "") }} {{ service.folder_origin }} {{ service.folder_origin }}

# remove (absolute) symbolic links and overwrite each symbolic link with the target file content
RUN find {{ service.folder_origin }} -type l -exec bash -c "cp --remove-destination \$(readlink -f {}) {} " \;

# move folder from the origin to the temporary destination - this prevents the move to it self or a subfolder of self.
RUN mv {{ service.folder_origin }} /tmp/static_assets

# create all destination folder, including its parent folder
RUN mkdir -p {{ service.folder_destination }}

# move folder from its temporary destionation to its final destionation
RUN mv /tmp/static_assets/* {{ service.folder_destination }}

# find duplicate static assets and replace duplicates with symbolic links
RUN rdfind -makesymlinks true {{ service.folder_destination }}

# force change ownership of files to be read for all because the target image can use different
# users to serve the files.
RUN chown -R 644 {{ service.folder_destination }}

{% endfor %}


#
# Target docker build stage
# It only copies the static assets from the merger stages.
#
FROM {{ build_web_server_docker_image_from }} as target

{% for service in build_web_server_services %}
COPY --from={{ ( service.service + 'build' ) | replace("_", "") }} {{ service.folder_destination }} {{ service.folder_destination }}
{% endfor %}
