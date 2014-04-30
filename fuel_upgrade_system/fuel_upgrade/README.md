## Installation

Master node should have access to the internet.

Run command on the master node

`curl -sSL http://bit.ly/1m6BB5g | bash`

## How to check

`docker images` - command shows 5.1 images
`ls -l /etc/supervisord.d/` - `current` symlink is linked on /etc/supervisord.d/5.1
`docker ps` - shows 5.1 containers

## Notes

Logs are in `/var/log/fuel_upgrade.log` file