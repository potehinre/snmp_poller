# -*- coding:utf-8 -*-
import mysql.connector
import sys
import os
import time
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.error import PySnmpError
from config import INTERFACE_NAME, COMMUNITY_STRING, SNMP_PORT, SERVER_NAMES, DB_SETTINGS, DELETE_STAT_AFTER
IN_OCTETS_OID = "1.3.6.1.2.1.2.2.1.10"
OUT_OCTETS_OID = "1.3.6.1.2.1.2.2.1.16"
INTERFACE_NAMES_OID = "1.3.6.1.2.1.2.2.1.2"
SERVER_UNAVAILABLE = -1
#Transport settings
RETRIES_COUNT = 0
TIMEOUT = 1

poll_info = {}
if_load_info = {}


def datetime_to_timestamp(datetime):
    return time.mktime(datetime.timetuple())


def get_last_servers_poll_info(connection):
    result = {}
    cursor = connection.cursor()
    query = "SELECT server_name,octet_count,time FROM last_poll_info"
    cursor.execute(query)
    for (server_name, octet_count, time) in cursor:
        result[server_name] = {"octet_count": octet_count, "time": datetime_to_timestamp(time)}
    return result


def del_last_servers_poll_info(connection):
    query = "DELETE FROM last_poll_info"
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def save_last_servers_poll_info(connection, poll_info):
    cursor = connection.cursor()
    query = "INSERT INTO last_poll_info(server_name, octet_count) VALUES(%s, %s)"
    for server_name, octet_count in poll_info.items():
        cursor.execute(query, [server_name, octet_count])
    connection.commit()
    cursor.close()


def save_load_stats(connection, load_stats):
    cursor = connection.cursor()
    query = "INSERT INTO load_stats(server_name, if_load) VALUES (%s, %s)"
    for server_name, if_load in load_stats.items():
        cursor.execute(query, [server_name, if_load])
    connection.commit()
    cursor.close()


def delete_old_load_stats(connection):
    cursor = connection.cursor()
    query = "DELETE FROM load_stats WHERE TIME_TO_SEC(TIMEDIFF(NOW(),time)) > %s"
    cursor.execute(query, [DELETE_STAT_AFTER])
    connection.commit()
    cursor.close()


#Async callbacks
def get_interface_number(send_request_handle, error_indication, error_status, error_index,
                  var_binds, server_name):
    interface_number = None
    if error_indication:
        if_load_info[server_name] = -1
    else:
        for var_bind_table_row in var_binds:
            for name, val in var_bind_table_row:
                if val == INTERFACE_NAME:
                    interface_number = int(name[-1])
    if interface_number:
        try:
            cmdGen.asyncGetCmd(cmdgen.CommunityData(COMMUNITY_STRING),
                          cmdgen.UdpTransportTarget((server_name, SNMP_PORT), retries=RETRIES_COUNT, timeout=TIMEOUT),
                          (IN_OCTETS_OID + "." + str(interface_number), OUT_OCTETS_OID + "." + str(interface_number)),
                          (get_interface_load_info, (server_name, interface_number)))
        except PySnmpError:
            if_load_info[server_name] = SERVER_UNAVAILABLE
        return False
    else:
        if_load_info[server_name] = SERVER_UNAVAILABLE
    return True


def get_interface_load_info(send_request_handle, error_indication, error_status,
                error_index, var_binds, cb_ctx):
    server_name = cb_ctx[0]
    interface_number = cb_ctx[1]
    if error_indication:
        if_load_info[server_name] = SERVER_UNAVAILABLE
    else:
        sum_octets = sum(v for k, v in var_binds)
        if server_name in last_servers_poll_info:
            current_time = int(time.time())
            previous_time = last_servers_poll_info[server_name]['time']
            time_diff = current_time - previous_time
            if time_diff > 0:
                if_load_info[server_name] = float(sum_octets - last_servers_poll_info[server_name]['octet_count']) / time_diff
        poll_info[server_name] = int(sum_octets)
        

if __name__ == "__main__":
    try:
        connection = mysql.connector.connect(user=DB_SETTINGS["user"],
                             password=DB_SETTINGS["password"],
                             host=DB_SETTINGS["host"],
                             database=DB_SETTINGS["database"])
        
        last_servers_poll_info = get_last_servers_poll_info(connection)
        del_last_servers_poll_info(connection)
        cmdGen = cmdgen.AsynCommandGenerator()
        for server_name in SERVER_NAMES:
            try:
                cmdGen.asyncNextCmd(
                    cmdgen.CommunityData(COMMUNITY_STRING),
                    cmdgen.UdpTransportTarget((server_name, SNMP_PORT), retries=RETRIES_COUNT, timeout=TIMEOUT),
                    (INTERFACE_NAMES_OID,),
                    (get_interface_number, server_name)
                )
            except PySnmpError:
                if_load_info[server_name] = SERVER_UNAVAILABLE
        cmdGen.snmpEngine.transportDispatcher.runDispatcher()
        save_last_servers_poll_info(connection, poll_info)
        save_load_stats(connection, if_load_info)
        delete_old_load_stats(connection)
    except mysql.connector.Error as err:
        sys.stderr.write("Can't connect to DB. errno=" + str(err.errno) + "\n")
        sys.exit(1)
    else:
        connection.close()
