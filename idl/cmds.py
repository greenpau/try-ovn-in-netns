#!/usr/bin/python2.7

from ovs.db import idl
from ovs import stream
from ovs import jsonrpc

err, strm = stream.Stream.open_block(stream.Stream.open('tcp:0.0.0.0:6641'))
rpc = jsonrpc.Connection(strm)
#
#  list-dbs [SERVER]
#
#req = jsonrpc.Message.create_request('list_dbs', [])

#
#  get-schema [SERVER] [DATABASE]
#  get-schema-version [SERVER] [DATABASE]
#  list-tables [SERVER] [DATABASE]
#  list-columns [SERVER] [DATABASE] [TABLE]
#
#req = jsonrpc.Message.create_request('get_schema', ['OVN_Northbound'])

#
#  transact [SERVER] TRANSACTION
#

#
#  monitor [SERVER] [DATABASE] TABLE [COLUMN,...]...
#  monitor-cond [SERVER] [DATABASE] CONDITION TABLE [COLUMN,...]...
#  monitor [SERVER] [DATABASE] ALL
#
# This monitoring persists until the JSON-RPC session terminates or until the client sends a "monitor_cancel" JSON-RPC request.
#
# If there is more than one <monitor-request> in an array, then each <monitor-request> in the array should specify both
# "columns" and "select", and the "columns" MUST be non-overlapping sets
#
#req = jsonrpc.Message.create_request("monitor", ["OVN_Northbound",None,{"Logical_Switch":[{"columns":["acls","dns_records","external_ids","load_balancer","name","other_config","ports","qos_rules","_version"]}]}])
#req = jsonrpc.Message.create_request("monitor", ["OVN_Northbound",None,{"Logical_Switch":[{"columns":["name","ports"],"select":{"initial":False,"insert":True,"delete":True,"modify":True}}]}])
req = jsonrpc.Message.create_request("monitor_cond", ["OVN_Northbound","monid",{"Logical_Switch_Port":{"columns":["addresses","dhcpv4_options","dhcpv6_options","dynamic_addresses","enabled","external_ids","name","options","parent_name","port_security","tag","tag_request","type","up"]}}])

#
#  lock [SERVER] LOCK
#  steal [SERVER] LOCK
#  unlock [SERVER] LOCK
#

#
# echo
#
#req = jsonrpc.Message.create_request("echo", [])

err, resp = rpc.transact_block(req)
rpc.close()
print resp
