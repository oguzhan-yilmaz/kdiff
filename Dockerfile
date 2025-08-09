FROM amazon/aws-cli:latest AS awscli
FROM bitnami/kubectl:latest AS kubectl

FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest
ENV DEBIAN_FRONTEND=noninteractive
# SHELL ["/bin/bash", "-c"]
USER root
WORKDIR /home/steampipe
RUN apt-get update -y \
    && apt-get install -y wget gpg \
    && wget -O - https://dathere.github.io/qsv-deb-releases/qsv-deb.gpg | gpg --dearmor -o /usr/share/keyrings/qsv-deb.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/qsv-deb.gpg] https://dathere.github.io/qsv-deb-releases ./" | tee /etc/apt/sources.list.d/qsv.list \
    && apt-get update -y \
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

RUN echo "Welcome to Kdiff!" > /etc/motd && \
    echo "TODO: Exec docs here, cli help here, etc." >> /etc/motd

USER steampipe
WORKDIR /home/steampipe

# Add the local bin directory to PATH
ENV PATH="/home/steampipe/.local/bin:${PATH}"

COPY --chown=steampipe:steampipe kdiff-snapshots-entrypoint.sh /home/steampipe/kdiff-snapshots-entrypoint.sh

RUN chmod +x kdiff-snapshots-entrypoint.sh

ENTRYPOINT ["./kdiff-snapshots-entrypoint.sh"]