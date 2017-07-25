#!/bin/bash -e

echo 1 > /sys/class/gpio/gpio69/value

read -rsp $'Vartai...\n' -n 1 -t 5

echo 0 > /sys/class/gpio/gpio69/value
