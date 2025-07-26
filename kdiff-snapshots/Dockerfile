FROM amazon/aws-cli:latest AS awscli

FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest

# SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y inotify-tools && apt-get clean && rm -rf /var/lib/apt/lists/*

# get the aws cli from it's docker image
COPY --from=awscli --chown=steampipe:steampipe /usr/local/aws-cli /usr/local/aws-cli
USER root
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws
USER steampipe

# Add the local bin directory to PATH
ENV PATH="/home/steampipe/.local/bin:${PATH}"

COPY --chown=steampipe:steampipe *.sh .

ENTRYPOINT ["bash", "kdiff-entrypoint.sh"]