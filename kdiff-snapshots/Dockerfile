FROM amazon/aws-cli:latest AS awscli

FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest

# get the aws cli from it's docker image
COPY --from=awscli --chown=steampipe:steampipe /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

COPY --chown=steampipe:steampipe *.sh .

ENTRYPOINT ["bash", "kdiff-entrypoint.sh"]