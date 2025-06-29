FROM ghcr.io/oguzhan-yilmaz/steampipe-powerpipe-kubernetes--steampipe:latest

COPY --chown=steampipe:steampipe entrypoint.sh kdiff-entrypoint.sh

ENTRYPOINT ["bash", "kdiff-entrypoint.sh"]