ovn-nbctl ls-del ls1

ip netns del n1p1
ip netns del n1p2

ovs-vsctl --db=unix:/usr/local/var/run/openvswitch/node1/db.sock del-port br-int n1p1o
ovs-vsctl --db=unix:/usr/local/var/run/openvswitch/node2/db.sock del-port br-int n1p2o
