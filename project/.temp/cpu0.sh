#!/bin/bash

# Reads CPU usage of core 0 over 1 second interval

read cpu user nice system idle iowait irq softirq steal guest < <(grep '^cpu0 ' /proc/stat)
prev_idle=$idle
prev_used=$((user + nice + system + irq + softirq + steal))

sleep 1

read cpu user nice system idle iowait irq softirq steal guest < <(grep '^cpu0 ' /proc/stat)
idle_diff=$((idle - prev_idle))
used_diff=$(( (user + nice + system + irq + softirq + steal) - prev_used ))
total=$((idle_diff + used_diff))

CPU0_UTIL=$(awk -v u="$used_diff" -v t="$total" 'BEGIN {printf "%.2f", (u/t)*100}')

echo "$CPU0_UTIL"
