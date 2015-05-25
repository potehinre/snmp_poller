# -*- coding: utf-8 -*-
#Название опрашиваемого интерфейса, если такого интерфейса у сервера нету , ставится -1
INTERFACE_NAME = "eth0"
COMMUNITY_STRING = 'public'
SNMP_PORT = 161
#Спустя какое количество времени удалять статистику в секундах.
DELETE_STAT_AFTER = 60 * 30
#Список опрашиваемых серверов
SERVER_NAMES = ("demo.snmplabs.com", "false.server.ru")
DB_SETTINGS = {"user": "root",
               "password": "86kitty",
               "host": "127.0.0.1",
               "database": "snmp_poller"}
