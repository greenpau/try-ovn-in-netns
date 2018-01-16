#!/bin/bash
#
# run as root

modprobe openvswitch
eth_path=/usr/local/etc/openvswitch
run_path=/usr/local/var/run/openvswitch
log_path=/usr/local/var/log/openvswitch

sdb_ip="10.0.0.3"
sdb_sock=$run_path/ovnsb_db.sock

dtch="--detach"
mnt="--monitor"

for ns in node1 node2
do
    mkdir $eth_path/$ns
    mkdir $run_path/$ns
    mkdir $log_path/$ns

    local_db=$eth_path/${ns}/conf.db
    local_sock=$run_path/${ns}/db.sock
    svr_pid=$run_path/${ns}/ovsdb-server.pid
    svr_log=$log_path/${ns}/ovsdb-server.log
    swch_pid=$run_path/${ns}/ovs-vswitchd.pid
    swch_log=$log_path/${ns}/ovs-vswitchd.log

    ctrl_log=$log_path/${ns}/ovn-controller.log
    ctrl_pid=$run_path/${ns}/ovn-controller.pid

    ovsdb-tool create $local_db

    ip netns exec $ns ovsdb-server --remote=punix:${local_sock} --remote=db:Open_vSwitch,Open_vSwitch,manager_options --private-key=db:Open_vSwitch,SSL,private_key --certificate=db:Open_vSwitch,SSL,certificate --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert --pidfile=$svr_pid $dtch --log-file=$svr_log $local_db 

    env OVS_RUNDIR=$run_path/$ns OVS_DBDIR=$eth_path/$ns OVS_LOGDIR=$log_path/$ns ip netns exec $ns ovs-vswitchd --pidfile=$swch_pid $dtch $mnt --log-file=$swch_log unix:$local_sock

    env OVS_RUNDIR=$run_path/$ns OVS_DBDIR=$eth_path/$ns OVS_LOGDIR=$log_path/$ns ip netns exec $ns ovn-controller $dtch $mnt --pidfile=$ctrl_pid --log-file=$ctrl_log unix:$local_sock

    if [[ $ns == "node1" ]]; then
        local_ip="10.0.0.4"
    else
        local_ip="10.0.0.5"
    fi
    ovs-vsctl --db=unix:$local_sock --if-exists set open . external_ids:system-id=$ns external_ids:ovn-encap-ip=$local_ip external_ids:ovn-encap-type="geneve,vxlan" external_ids:ovn-remote="tcp:$sdb_ip:6642" external_ids:hostname="$ns"

    echo "ovs-vsctl --db=unix:$run_path/$ns/db.sock \$*" > $ns-ovs-vsctl
    echo "env OVS_RUNDIR=$run_path/$ns OVS_DBDIR=$eth_path/$ns OVS_LOGDIR=$log_path/$ns \$*" > $ns-ovs-env
    chmod o+x $ns-ovs-vsctl
    chmod o+x $ns-ovs-env

done

ndb_sock=''
for db in nb sb
do
    xth_db=$eth_path/ovn${db}.conf.db
    xth_db_sock=$run_path/ovn${db}_db.sock
    xth_db_log=$log_path/ovsdb-server-${db}.log
    xth_db_pid=$run_path/ovn${db}_db.pid

    ovsdb-tool create $xth_db /usr/local/share/openvswitch/ovn-${db}.ovsschema 

    if [[ $db == "nb" ]]; then
        d="OVN_Northbound"
        g="NB_Global"
        ctl="ovnnb_db.ctl"
        ndb_sock=$xth_db_sock
        p=6641
    else
        d="OVN_Southbound"
        g="SB_Global"
        ctl="ovnsb_db.ctl"
        p=6642
    fi

    ip netns exec db_node ovsdb-server $dtch $mnt -vconsole:off -vfile:info --log-file=$xth_db_log --remote=punix:$xth_db_sock --remote=ptcp:${p}:0.0.0.0 --pidfile=$xth_db_pid --remote=db:${d},${g},connections --unixctl=${ctl} --private-key=db:${d},SSL,private_key --certificate=db:${d},SSL,certificate --ca-cert=db:${d},SSL,ca_cert --ssl-protocols=db:${d},SSL,ssl_protocols --ssl-ciphers=db:${d},SSL,ssl_ciphers $xth_db
done

ovn-northd --ovnnb-db=unix:$ndb_sock --ovnsb-db=unix:$sdb_sock $dtch $mnt --log-file=${log_path}/ovn-northd.log
