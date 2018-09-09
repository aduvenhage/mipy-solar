# mipy-solar (retired -- moved to c++ / Raspberry PI)
Remote solar charger / battery monitor framework (retired -- moved to c++ / Raspberry PI)

Currently using an arduino to connect to Victron Solar Regulator and an esp8266 to serve information through a simple http socket. Arduino and ESP8266 connected via I2C bus. Small OLED also attached to I2C bus -- controlled from ESP.

Future work will focus on different arduino projects to swap out victron energy interface with other regulator interfaces or direct interfacing to current and voltage sensors.
