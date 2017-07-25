#!/bin/bash -e
echo "IN1 (GPIO71, gpio2_7)"
cat /sys/class/gpio/gpio71/value
echo "IN2 (GPIO73, gpio2_9)"
cat /sys/class/gpio/gpio73/value
echo "IN3 (GPIO72, gpio2_8) - garazas"
cat /sys/class/gpio/gpio72/value
echo "IN4 (GPIO70, gpio2_6)"
cat /sys/class/gpio/gpio70/value
echo "IN5 (GPIO117, gpio3_21) - vartai pultelis"
cat /sys/class/gpio/gpio117/value
echo "IN6 (GPIO49, gpio1_17) - vartai telefonas"
cat /sys/class/gpio/gpio49/value
