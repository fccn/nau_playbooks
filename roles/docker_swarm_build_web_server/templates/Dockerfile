#
# Define each new image
# Remove (absolute) symbolic links 
# Overwrite each symb link with the target file content
#
{% for service in docker_swarm_build_web_server_services %}
# {{ service.service }}
FROM {{ service.docker_image }} as {{ ( service.service + '_new' ) | replace("_", "") }}
{% for folder in service.folders %}
RUN find {{ folder.folder }} -type l -exec bash -c "cp --remove-destination \$(readlink {}) {} " \;
{% endfor %}

{% endfor %}

#
# Define each previous image
# Remove (absolute) symbolic links 
# Overwrite each symb link with the target file content
#
{% for service in docker_swarm_service_info_result.results %}
{% if service.service.Spec is defined %}
# {{ service.item.service }}
FROM {{ service.service.Spec.TaskTemplate.ContainerSpec.Image }} as {{ ( service.item.service + '_previous' ) | replace("_", "") }}
{% for folder in service.item.folders %}
RUN find {{ folder.folder }} -type l -exec bash -c "cp --remove-destination \$(readlink {}) {} " \;
{% endfor %}

{% endif %}
{% endfor %}

# ---- Base image to inherit from ----
FROM {{ docker_swarm_build_web_server_docker_image_from }} as base

# Install rdfind
RUN apt-get update && \
    apt-get install -y \
    rdfind && \
    rm -rf /var/lib/apt/lists/*

{% for service in docker_swarm_service_info_result.results %}
# {{ service.item.service }}
{% if service.service.Spec is defined %}
{% for folder in service.item.folders %}
COPY --from={{ ( service.item.service + '_previous' ) | replace("_", "") }} {{ folder.folder }} {{ folder.previous }}
{% endfor %}
{% endif %}
{% for folder in service.item.folders %}
COPY --from={{ ( service.item.service + '_new' ) | replace("_", "") }} {{ folder.folder }} {{ folder.next }}
{% endfor %}
RUN rdfind -makesymlinks true {% for folder in service.item.folders %}{{ folder.next }} {% endfor %}{% if service.service.Spec is defined %}{% for folder in service.item.folders %}{{ folder.previous }} {% endfor %}{% endif %}

{% endfor %}
