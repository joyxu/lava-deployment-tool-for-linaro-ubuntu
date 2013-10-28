.. _tips_and_tricks:

Tips and Tricks
***************

.. _ser2net:

Ser2net daemon
==============

W.I.P

ser2net provides a way for a user to connect from a network connection to a serial port, usually over telnet.

http://ser2net.sourceforge.net/

Example config (in /etc/ser2net.conf)

::
 #port:connectiontype:idle_timeout:serial_device:baudrate databit parity stopbit
 7001:telnet:36000:/dev/serial_port1:115200 8DATABITS NONE 1STOPBIT


StarTech rackmount usb
======================

W.I.P

* udev rules

::
 SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="ST167570", SYMLINK+="rack-usb02"
 SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="ST167569", SYMLINK+="rack-usb01"
 SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="ST167572", SYMLINK+="rack-usb04"
 SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="ST167571", SYMLINK+="rack-usb03"

This will create a symlink in /dev called rack-usb01 etc. which can then be addressed in the :ref:`_ser2net` config file.
