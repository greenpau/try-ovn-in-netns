pkill -9 -f ovs
pkill -9 -f ovn
rm -rf /usr/local/etc/openvswitch/*
rm -rf /usr/local/var/run/openvswitch/*
rm -rf /usr/local/var/log/openvswitch/*
rm -rf ./node1-ovs-*
rm -rf ./node2-ovs-*
