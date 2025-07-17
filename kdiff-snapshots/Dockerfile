ARG IMAGE_TAG=latest        
FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:${IMAGE_TAG}

COPY --chown=steampipe:steampipe *.sh .

ENTRYPOINT ["bash", "kdiff-entrypoint.sh"]