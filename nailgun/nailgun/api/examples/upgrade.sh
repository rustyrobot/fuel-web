#!/usr/bin/env bash

# Ubuntu 12.04.5 LTS (Precise Pangolin)
# coreutils installed by default, so need to install only jq

# wget -O /tmp/jq_1.4-2.1_amd64.deb \
# http://ftp.us.debian.org/debian/pool/main/j/jq/jq_1.4-2.1_amd64.deb && \
# dpkg -i /tmp/jq_1.4-2.1_amd64.deb

# CentOS

# wget -O /usr/local/bin/jq https://stedolan.github.io/jq/download/linux64/jq
# chmod a+x /usr/local/bin/jq

# MacOS X
# install HomeBrew packet manager and script dependencies

# ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
# brew update
# brew install bash curl jq coreutils

# Check that all variable are bound
set -u

# default settings
_fuel_node="10.20.0.2"
_fuel_node="172.16.37.5"
_auth_token=""

# default api urls
_keystone_api="http://${_fuel_node}:35357/v2.0/"
_fuel_api="http://${_fuel_node}:8000/api/v1/"

# display an error and exit
function die {
    echo -e "$1" ; exit 1
}

# call an api
function api_call {
    local _method="${1^^}"
    local _params="${2}"
    local _data=""

    [[ "PUT POST" =~ ${_method} ]] && _data="${3}"

    _out=`curl --stderr - -sS -X "${_method}" -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -H "X-Auth-Token: ${_auth_token}" \
        -d "${_data}" \
        "${_api_url}${_params}"`

    _err=${?}

    [[ ${_err} != 0 ]] && die "${_out}"

    return ${_err}
}

# get token from the keystone using an api call
function auth_keystone {
    _api_url=${_keystone_api}
    api_call post 'tokens' '{"auth": {"tenantName": "admin", "passwordCredentials": {"username": "admin", "password": "admin"}}}'
    _auth_token=`echo ${_out} | jq ".access.token.id" | tr -d '"'`
    [[ ${_auth_token} == 'null' ]] && die "${_out}"
    _api_url=${_fuel_api}
}

# initial setup
auth_keystone

# get clusters info
api_call get clusters

_cluser_status=`echo ${_out} | jq ".[] | .status"`
[[ ${_cluser_status} != "\"operational\"" ]] && echo -e "WARNING! Current environment is not in operational state !!!"

_env_id=`echo ${_out} | jq ".[] | .id"`
_rel_id=`echo ${_out} | jq ".[] | .release_id"`

# get installed releases info
api_call get releases

_env_name=`echo ${_out} | jq ".[] | select(.id == ${_rel_id}) | .name" | tr -d '"'`
_env_os=`echo ${_out} | jq ".[] | select(.id == ${_rel_id}) | .operating_system"`

echo -e "Environment id:\t${_env_id} (${_env_name})\n"

_rel_ver=`echo ${_out} | jq ".[] | select(.id == ${_rel_id}) | .version" | tr -d '"'`
echo -e "Installed version:\t${_rel_ver} (id:${_rel_id})"

_avail_id=`echo ${_out} | jq ".[] | select(.id != ${_rel_id}) | select(.operating_system == ${_env_os}) | .id"`
_avail_ver=`echo ${_out} | jq ".[] | select(.id != ${_rel_id}) | select(.operating_system == ${_env_os}) | .version" | tr -d '"'`
echo -e "Available version:\t${_avail_ver} (id:${_avail_id})"

# print node list table used for 'nodes' api call
function node_list {
    _node_list=`echo ${_out} | jq ".[] | .id" | sort`
    [[ $? == 4 ]] && echo "${_out}" >>debug.log

    local _f="%-3s %-20s %-12s %-10s %-10s\n"

    printf "\n"
    printf "${_f}" "id" "name" "status" "progress" "roles"
    printf "${_f}" "---" "-----" "-------" "---------" "------"

    for _node_id in $_node_list
    do
        _node_name=`echo ${_out} | jq ".[] | select(.id == ${_node_id}) | .name"`
        [[ $? == 4 ]] && echo "${_out}" >>debug.log
        _node_status=`echo ${_out} | jq ".[] | select(.id == ${_node_id}) | .status"`
        [[ $? == 4 ]] && echo "${_out}" >>debug.log
        _node_progress=`echo ${_out} | jq ".[] | select(.id == ${_node_id}) | .progress"`
        [[ $? == 4 ]] && echo "${_out}" >>debug.log
        _node_roles=`echo ${_out} | jq ".[] | select(.id == ${_node_id}) | .roles | join(\", \")"`
        [[ $? == 4 ]] && echo "${_out}" >>debug.log
        printf "${_f}" "${_node_id}" "${_node_name}" "${_node_status}" "${_node_progress}%" "${_node_roles}"
    done
}

# get nodes status from cluster
api_call get nodes
_node_status=`echo ${_out} | jq ".[] | .status" | sort -u`

[[ ${_node_status} =~ "error" ]] && echo -e "\nWARNING! Some of nodes in cluster in error state !!!"
node_list

if [[ ${_node_status} == "\"ready\"" ]] ; then

    echo -e "\nPress ENTER to continue or Ctrl+C to abort" ; read _input

    # put cluster into 'update' mode with new 'pending_release_id'
    api_call put "clusters/${_env_id}" "{ \"status\": \"update\", \"pending_release_id\": ${_avail_id} }"

    # get sorted list of nodes to deploy
    api_call get nodes
    _deploy_nodes=`echo ${_out} | jq "[.[] | .id | tostring] | sort | join(\",\")" | tr -d \"`

    # run an update on nodes
    api_call put "clusters/${_env_id}/deploy/?nodes=${_deploy_nodes}" "{ }"
    _deploy_status=`echo ${_out} | jq ".status"`

    if [[ ${_deploy_status} == "\"running\"" ]] ; then
        echo -e "Update started on the nodes: ${_deploy_nodes}"
        api_call get nodes
        _node_status=`echo ${_out} | jq ".[] | .status" | sort -u`
    fi
#else
    #echo ${_out}
fi

while [[ ${_node_status} != "\"ready\"" ]] ; do
    sleep 5
    api_call get nodes
    node_list
    _node_status=`echo ${_out} | jq ".[] | .status" | sort -u`
    [[ ${_node_status} =~ "error" ]] && break
done

api_call get clusters
_cluser_status=`echo ${_out} | jq ".[] | .status"`

if [[ ${_cluser_status} == "\"update\"" ]] && [[ ${_node_status} == "\"ready\"" ]] ; then
    api_call put "clusters/${_env_id}" "{ \"status\": \"operational\", \"release_id\": ${_avail_id}, \"pending_release_id\": null }"
fi

