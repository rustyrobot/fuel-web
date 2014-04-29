#!/bin/bash

set -x

ROOT_DIR=/web

FUEL_UPGRADE_DIR=$ROOT_DIR/fuel-web-4bp-fuel-upgarde/fuel_upgrade_system/fuel_upgrade
UPGRADE_SYSTEM_URL=https://github.com/rustyrobot/fuel-web/archive/4bp/fuel-upgarde.tar.gz

IMAGES_PATH=/var/images
IMAGES_ARCHIVE_NAME=fuel-images.tar.lrz
IMAGES_URL=http://srv11-msk.msk.mirantis.net/eli-docker/fuel-images.tar.lrz


echo 'Download containers'

mkdir -p $IMAGES_PATH
pushd $IMAGES_PATH
curl -L -o $IMAGES_PATH/$IMAGES_ARCHIVE_NAME "$IMAGES_URL" || exit 1
lrzuntar $IMAGES_ARCHIVE_NAME || exit 1


echo 'Install upgrade script dependenices'

mkdir -p $ROOT_DIR
pushd $ROOT_DIR
curl -L $UPGRADE_SYSTEM_URL | tar zx

easy_install pip
yum install git
pip install git+https://github.com/rustyrobot/docker-py.git@fixed-volumes#egg=docker-py
python $FUEL_UPGRADE_DIR/setup.py develop


echo 'Run upgrade system'
fuel-upgrade --disable_rollback --src $IMAGES_PATH
