#!/bin/bash -e

echo "OUT8 (GPIO68, gpio2_4, P8_10)"
cat /sys/class/gpio/gpio68/value

echo "IN4 (GPIO70, gpio2_6, P8_45)"
cat /sys/class/gpio/gpio70/value

echo "OUT4 (GPIO26)"
cat /sys/class/gpio/gpio26/value
