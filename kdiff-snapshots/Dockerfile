FROM amazon/aws-cli:latest AS awscli
FROM bitnami/kubectl:latest AS kubectl

# actual image
FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest
ARG TARGETPLATFORM
ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]
ENV QSV_VER="8.1.1"

USER root
RUN apt-get update -y \
    && apt-get install -y wget gpg \
    && apt-get install -y \
        inotify-tools ca-certificates \
        curl git unzip jq  \
    && apt-get clean 


# Install qsv depending on architecture
COPY --chown=steampipe:steampipe install-qsv.sh .
RUN bash install-qsv.sh


RUN qsv --version

# get the aws cli from it's docker image
COPY --from=awscli --chown=steampipe:steampipe /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

# get kubectl cli 
COPY --from=kubectl /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl


# Add the local bin directory to PATH
ENV PATH="/home/steampipe/.local/bin:${PATH}"

COPY  --chown=steampipe:steampipe kdiff-snapshots-entrypoint.sh .
COPY  --chown=steampipe:steampipe csv-script.sh .
COPY  --chown=steampipe:steampipe start-and-wait-steampipe-service.sh .
COPY  --chown=steampipe:steampipe snapshot-config.yaml .

RUN ls && ls / && ls /home/steampipe
RUN chmod +x *.sh

RUN ls -la

USER steampipe
ENTRYPOINT ["./kdiff-snapshots-entrypoint.sh"]