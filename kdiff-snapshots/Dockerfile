FROM amazon/aws-cli:latest as awscli

FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:${IMAGE_TAG}
ARG IMAGE_TAG=latest        

# get the aws cli from it's docker image
COPY --from=awscli /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

COPY --chown=steampipe:steampipe *.sh .

ENTRYPOINT ["bash", "kdiff-entrypoint.sh"]