FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest

COPY --chown=steampipe:steampipe *.sh .

ENTRYPOINT ["bash", "kdiff-entrypoint.sh"]