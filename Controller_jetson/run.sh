#!/bin/bash
echo "Starting both applications..."

nohup python3 RTC_Server.py > rtc_server.log 2>&1 &
PID1=$!

nohup python3 main_Controller.py > controller.log 2>&1 &
PID2=$!

echo "RTC_Server PID: $PID1"
echo "main_Controller PID: $PID2"

echo ""
echo "To kill the processes, run:"
echo "kill $PID1 && kill $PID2"
wait $PID1 $PID2
