#!/bin/bash

set -x

FUEL_ROOT_DIR=/web

FUEL_UPGRADE_DIR=$FUEL_ROOT_DIR/fuel-web-4bp-fuel-upgarde/fuel_upgrade_system/fuel_upgrade
UPGRADE_SYSTEM_URL=https://github.com/rustyrobot/fuel-web/archive/4bp/fuel-upgarde.tar.gz

IMAGES_PATH=/var/images
IMAGES_ARCHIVE_NAME=fuel-images.tar.lrz
IMAGES_URL=http://172.18.8.212:9000/fuel-images-14-05-13.tar.lrz
# http://srv11-msk.msk.mirantis.net/eli-docker/fuel-images-fixed-upgrades-nailgun-with-new-field.tar.lrz


echo 'Download containers'

mkdir -p $IMAGES_PATH
pushd $IMAGES_PATH
curl -L -o $IMAGES_PATH/$IMAGES_ARCHIVE_NAME "$IMAGES_URL" || exit 1
lrzuntar $IMAGES_ARCHIVE_NAME || exit 1


echo 'Install upgrade script dependenices'

rm -rf $FUEL_ROOT_DIR
mkdir -p $FUEL_ROOT_DIR
pushd $FUEL_ROOT_DIR
curl -L $UPGRADE_SYSTEM_URL | tar zx

easy_install pip
yum install -y git
pip install git+https://github.com/rustyrobot/docker-py.git@fixed-volumes#egg=docker-py
pushd $FUEL_UPGRADE_DIR
python setup.py develop


echo 'Run upgrade system'
fuel-upgrade --disable_rollback --src $IMAGES_PATH
