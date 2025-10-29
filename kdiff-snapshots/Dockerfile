FROM amazon/aws-cli:latest AS awscli
FROM bitnami/kubectl:latest AS kubectl

# actual image
FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]
ENV QSV_VER="8.1.1"

USER root
RUN apt-get update -y \
    && apt-get install -y wget gpg \
    && wget -O - https://dathere.github.io/qsv-deb-releases/qsv-deb.gpg | gpg --dearmor -o /usr/share/keyrings/qsv-deb.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/qsv-deb.gpg] https://dathere.github.io/qsv-deb-releases ./" | tee /etc/apt/sources.list.d/qsv.list \
    && apt-get update -y \
    && apt-get install -y \
        inotify-tools \
        curl git unzip jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*



# Install qsv
RUN echo "architecture = $(dpkg --print-architecture)" \
    if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
        apt-get install -y qsv; \
    elif [ "$(dpkg --print-architecture)" = "arm64" ]; then \
        export QSV_DOWNLOAD_URL="https://github.com/dathere/qsv/releases/download/${QSV_VER}/qsv-${QSV_VER}-aarch64-unknown-linux-gnu.zip" \ 
        && echo "QSV_DOWNLOAD_URL=$QSV_DOWNLOAD_URL" \
        && wget "$QSV_DOWNLOAD_URL" \
        && unzip qsv-${QSV_VER}-aarch64-unknown-linux-gnu.zip \
        && mv qsv /usr/local/bin/ \
        && chmod +x /usr/local/bin/qsv \
        && rm qsv-${QSV_VER}-aarch64-unknown-linux-gnu.zip; \
    fi
RUN ls -R
RUN qsv --version

# get the aws cli from it's docker image
COPY --from=awscli --chown=steampipe:steampipe /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

COPY --from=kubectl /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl


# Add the local bin directory to PATH
ENV PATH="/home/steampipe/.local/bin:${PATH}"

COPY  --chown=steampipe:steampipe kdiff-snapshots-entrypoint.sh .
COPY  --chown=steampipe:steampipe csv-script.sh .

RUN ls && ls / && ls /home/steampipe
RUN chmod +x *.sh

# RUN chmod +x kdiff-snapshots-entrypoint.sh
# RUN chmod +x csv-script.sh
RUN ls -la

USER steampipe
ENTRYPOINT ["./kdiff-snapshots-entrypoint.sh"]