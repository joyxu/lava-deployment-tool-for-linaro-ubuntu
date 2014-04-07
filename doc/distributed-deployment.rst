.. _distributed_deployment:

Deploying Distributed Instances
*******************************

When deploying a large LAVA "lab" instance with many :ref:`DUT` it is suggested to use :ref:`remote_worker` nodes.

.. _remote_worker:

Remote Worker
=============

A remote worker node is a reduced install of LAVA that is capable of running :ref:`lava_dispatcher` jobs and submitting the results back to the master :ref:`lava_server`.
In a lab environment, you will likely have too many test devices for a single server to handle with, so a worker-node can be used to spread the load.
An example reason for using worker nodes is a LAVA server struggling to cope with multiple high-IO process while dispatching images to a :ref:`DUT`

Configuring Master server for remote workers
============================================

As in a :ref:`single_deployment`, perform the setup step::

 $ ./lava-deployment-tool setup

In order for remote workers to be able to access the master database, Postgres has to be configured to allow access from external clients over the network. This can be done with the environment setting of LAVA_DB_ALLOWREMOTE.
If you are configuring multiple remote workers, it may be useful to overrided the auto-generated database password, and set it manually on all installs with the LAVA_DB_PASSWORD setting.

*Example command line*::

 $ LAVA_DB_ALLOWREMOTE=yes LAVA_DB_PASSWORD=secret ./lava-deployment-tool install instance_name

Configuring remote worker
=========================

A remote worker needs to know the network address of the Master :ref:`lava_server`. This can be set with LAVA_MASTER.
Again, LAVA_DB_PASSWORD can be used if you wish to preset the database password, otherwise you will be asked in the prompt.

*Example command line*::

 $ LAVA_DB_PASSWORD=secret LAVA_MASTER=lava-master ./lava-deployment-tool installworker instance_name

Remote databases
================

``lava-deployment-tool`` remoteworker installations assume the DB resides on the LAVA_MASTER and
remote worker installations using the prompts will set up your instance using a database on
LAVA_MASTER. It is possible to use a remote database by using the ``LAVA_DB_SERVER`` variable.

.. note: A remote postgres database only works with remote workers, the master install
will still install a postgres server as part of the setup task. If you are using a remote
database, the master instance will need to be configured separately.

*Example command line*::

 $ LAVA_DB_PASSWORD=secret LAVA_DB_SERVER=postgres LAVA_MASTER=lava-master ./lava-deployment-tool installworker instance_name

LAVA_MASTER is still needed to support sshfs connections for results.

Heartbeat
=========
Each dispatcher worker node sends heartbeat data to the master node
via xmlrpc. For this feature to work correctly the ``rpc2_url``
parameter should be set properly. Login as an admin user and go to
http://localhost/admin/lava_scheduler_app/worker/ (replace localhost
with your server name/IP). Click on the machine which is your master
and in the page that opens, set the "Master RPC2 URL:" with the
correct value, if it is not set properly, already. Do not touch any
other values in this page except the description, since all the other
fields except description is populated automatically. The following
figure illustrates this:

.. image:: ./images/lava-worker-rpc2-url.png
    :width: 640
    :height: 480

The "HEARTBEAT_TIMEOUT" value decides the frequency (in seconds) at
which heartbeat data gets updated. The default value is 300 seconds. This
timeout could be set separately for each worker node by tweaking the 
value of "HEARTBEAT_TIMEOUT" value in
``/srv/lava/$LAVA_INSTANCE/etc/lava-server/worker.conf``

Frequently encountered problems
===============================

Make sure that your database connectivity is configured correctly in::
/srv/lava/instances/your_instance/instance.conf
/srv/lava/instances/your_instance/etc/lava-server/default_database.conf

and your LAVA_SERVER_IP (worker ip address) is configured correctly in::
/srv/lava/instances/your_instance/instance.conf
/srv/lava/instances/your_instance/etc/lava-dispatcher/lava-dispatcher.conf

Postgres on the master server is running on the default port 5432 (or whatever port you have configured)

SSHFS on the worker has successfully mounted from the master. Check `mount` and `dmesg` outputs for help.

Considerations for Geographically separate Master/Worker setups
===============================================================

A :ref:`remote_worker` needs to be able to communicate with the :ref:`lava_server` over SSH and Postgres (standard ports 22 and 5432) so some configuration will be needed if the :ref:`lava_master` is behind a firewall.

* The :ref:`DUT` console output logs are written to a filesystem that is shared over SSHFS from the master :ref:`lava_master`. A side-effect of this is that over high latency links there can be a delay in seeing console output when viewing it on the scheduler job webpage. SSHFS can recover from network problems but a monitoring system to check the mount is still available is preferred.
* Latency over SSHFS
* Log file update speed
* Port forwarding behind firewalls

Scaling Deployments
===================

* How many boards can a server "dispatch"?

  Some jobs require some heavy IO while LAVA reconfigures an image or
  compresses/decompresses. This blocks one processor.


Considerations of serial connections
====================================

* Modern server or desktop x86 hardware will often have no, or very
  few, serial ports, but :ref:`DUT` are still often controlled by LAVA
  over serial. The 2 solutions we use for this in the LAVA lab are
  dedicated serial console servers or usb-to-serial adaptors. If you
  plan to use many usb-to-serial adaptors, ensure that your USB hub
  has an external power source. For ease of udev configuration, use a
  usb-to-serial chipset that supports unique serial numbers, such as
  FTDI.
* In a large deployment in server racks, rackmounted serial hardware
  is available. Avocent offer Cyclades serial console servers which
  work well however the cost can be high. An alternative is a 16 port
  rackmount USB serial adapters, available from companies such as
  StarTech. Combined with :ref:`ser2net`, we have found these to be
  very reliable.


Other Issues to consider
========================

* Network switch bandwidth
  There will be huge data transfers happening between the dispatcher
  worker and the master, also between the devices attached to the
  dispatcher worker. In such a case careful thought must be given in
  placing and commissioning a network switch, in order to handle this
  huge bandwidth transfer.
* Proxy server
  Since all the devices loads images from the URL given in the job
  file, it is a good idea to have a proxy server installed and route
  the download traffic via this proxy server, which prevents image
  downloads directly and saves bandwidth. The proxy server can be set
  for the dispatcher during installation via lava deployment tool or
  by editing the value of ``LAVA_PROXY`` in /srv/lava/instances/<your_instance_name>/instance.conf

