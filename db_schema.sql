CREATE DATABASE snmp_poller;
USE snmp_poller;
CREATE TABLE last_poll_info(
	id SERIAL PRIMARY KEY,
	server_name VARCHAR(256) NOT NULL,
	octet_count BIGINT NOT NULL,
	time timestamp NOT NULL);
CREATE TABLE load_stats(
	id SERIAL PRIMARY KEY,
	server_name VARCHAR(256) NOT NULL,
	if_load FLOAT(10, 2) NOT NULL,
	time timestamp NOT NULL);
