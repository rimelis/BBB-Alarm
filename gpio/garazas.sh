#!/bin/bash -e

echo 1 > /sys/class/gpio/gpio67/value

read -rsp $'Garazas...\n' -n 1 -t 5

echo 0 > /sys/class/gpio/gpio67/value
