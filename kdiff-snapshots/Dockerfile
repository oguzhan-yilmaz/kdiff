FROM amazon/aws-cli:latest AS awscli
FROM bitnami/kubectl:latest as kubectl

FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest
ENV DEBIAN_FRONTEND=noninteractive
# SHELL ["/bin/bash", "-c"]

USER root
RUN apt-get update -y \
    && apt-get install -y \
        inotify-tools \
        curl \
        git \
        unzip \
        qsv \
        jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# get the aws cli from it's docker image
COPY --from=awscli --chown=steampipe:steampipe /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

COPY --from=kubectl /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl

USER steampipe

# Add the local bin directory to PATH
ENV PATH="/home/steampipe/.local/bin:${PATH}"

COPY --chown=steampipe:steampipe *.sh .

ENTRYPOINT ["bash", "kdiff-entrypoint.sh"]