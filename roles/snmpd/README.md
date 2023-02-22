# snmpd role

snmpd configuration used by Icinga, Nagios and Cacti.

Nagios/Icinga sent alarms when something is not ok.

Cacti generate time series based charts.

To test execute this command on the server:

```bash
snmpwalk -v 2c -c d84jvmsq94uo localhost NET-SNMP-EXTEND-MIB::nsExtendOutputFull
```
