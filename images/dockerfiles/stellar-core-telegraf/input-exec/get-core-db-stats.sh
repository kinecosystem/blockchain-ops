#!/bin/bash
txhistorysize=$(psql $CORE_DB_URL -c 'select distinct count(*) from txhistory ;'|sed -n '3p'|tr -d ' ')
printf 'core_db_stats txhistorysize=%d\n' $txhistorysize
