#!/bin/bash

if [ -n "$INSTALL_PLUGINS" ]; then
    echo "Installing Plugins: $INSTALL_PLUGINS"
    for mod in $INSTALL_PLUGINS; do
        echo "Installing Plugin: $mod"
        ./steampipe plugin install "$mod" > /dev/null
    done
fi

echo "Updating Plugins..."
./steampipe plugin update --all

echo "Steampipe Plugins:"
./steampipe plugin list

# run the initdb.sh in a sub-shell to not block the steampipe service start
(bash init-db.sh) &

echo "Starting Steampipe:"
./steampipe service start --foreground


# snapshot kubernetes state
bash csv-script.sh --debug --out-dir /tmp/kdiff-snapshots

ls /tmp/kdiff-snapshots



# tar the snapshot


# upload the snapshot to s3





ls -al /tmp/kdiff-snapshots

# TODO: remove this later, for debugging
sleep infinity
