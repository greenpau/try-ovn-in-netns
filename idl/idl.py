#!/usr/bin/python2.7

from ovs.db import idl
from ovs import stream
from ovs import jsonrpc

err, strm = stream.Stream.open_block(stream.Stream.open('tcp:0.0.0.0:6641'))
rpc = jsonrpc.Connection(strm)
#req = jsonrpc.Message.create_request('transact', ["OVN_Northbound",{"op":"insert","table":"Logical_Switch","row":{"name":"ls3"}}])
req = jsonrpc.Message.create_request('transact', ["OVN_Northbound",{"op":"select","table":"Logical_Switch","where":[["name","==","ls3"]]}])
#req = jsonrpc.Message.create_request('transact', ["OVN_Northbound",{"op":"update","table":"Logical_Switch","where":[["name","==","ls3"]],"row":{"external_ids":["map",[["foo","bar"]]]}}])
#req = jsonrpc.Message.create_request('transact', ["OVN_Northbound",{"op":"delete","table":"Logical_Switch","where":[["name","==","ls3"]]}])

# mutate ?
# wait ?

err, resp = rpc.transact_block(req)
rpc.close()
print resp
