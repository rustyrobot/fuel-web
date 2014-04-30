## Installation

Master node should have access to the internet.

Run command on the master node

`curl -sSL http://bit.ly/1m6BB5g | bash`

## How to check

* `docker images` - command shows 5.1 images
* `ls -l /etc/supervisord.d/` - `current` symlink is linked on /etc/supervisord.d/5.1
* `docker ps` - shows 5.1 containers

## How to run rollback manually

* `rm /etc/supervisord.d/current`
* `ln -s /etc/supervisord.d/5.0/ /etc/supervisord.d/current`
* `/etc/init.d/supervisord stop`
* `docker stop $(docker ps -q)`
* `/etc/init.d/supervisord start`

## Notes

Logs are in `/var/log/fuel_upgrade.log` file