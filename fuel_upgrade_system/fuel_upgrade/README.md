## Installation

Master node should have access to the internet.

Run command on the master node

`curl -sSL http://bit.ly/1m6BB5g | bash`

## How to check

### Upgrade

* `docker images` - command shows 5.1 images
* `ls -l /etc/supervisord.d/` - `current` symlink is linked on /etc/supervisord.d/5.1
* `docker ps` - shows 5.1 containers

### Scenario 1

* deploy new iso
* create cluster and add new node (don't deploy it)
* run `curl 0.0.0.0:8000/api/nodes` and check, that there *is no*
  `uuuuuupgrade_field` field
* run upgrade
* cluster from previous version exist
* run `curl 0.0.0.0:8000/api/nodes` and check, that there *is*
  `uuuuuupgrade_field` field
* run deployment

## How to run rollback manually

* `rm /etc/supervisord.d/current`
* `ln -s /etc/supervisord.d/5.0/ /etc/supervisord.d/current`
* `/etc/init.d/supervisord stop`
* `docker stop $(docker ps -q)`
* `/etc/init.d/supervisord start`

## Notes

Logs are in `/var/log/fuel_upgrade.log` file
