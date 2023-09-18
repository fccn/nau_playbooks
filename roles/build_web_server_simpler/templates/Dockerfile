# Builder process that copies from any docker images to any target docker image.
#
# 1. Definition phase
# 2. Target phase

#
# Definition phase
#
{% for service in build_web_server_services %}
# Simply define upstream base image for service: {{ service.service }}
FROM {{ service.docker_image }} as {{ ( service.service + 'definition' ) | replace("_", "") }}

{% endfor %}


#
# Target docker build stage
# It only copies the static assets from the merger stages.
#
FROM {{ build_web_server_docker_image_target }} as target

{% for service in build_web_server_services %}
COPY --from={{ ( service.service + 'definition' ) | replace("_", "") }} {{ service.folder }} {{ service.folder }}
{% endfor %}
