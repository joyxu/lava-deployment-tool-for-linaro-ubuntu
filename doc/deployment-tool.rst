LAVA Installation
*****************

LAVA Deployment Tool is meant to assist you setting up LAVA on your machine.
The tool is suitable for both personal and more "production" installations that
are expected to perform adequately with more concurrent users. This tool is
not, however, designed for multi-machine installation, including cloud
deployment. For that it is likely we will turn to Juju_.

.. _Juju: https://juju.ubuntu.com/

Getting LAVA Deployment Tool
============================

LAVA Deployment Tool can be downloaded from git:

 $ git clone http://git.linaro.org/git-ro/lava/lava-deployment-tool.git

Quickstart
==========

For the impatient, or those just looking for a cheat sheet but know what they
are doing otherwise, here are the basic set of commands to get an instance::

 $ ./lava-deployment-tool setup
 $ ./lava-deployment-tool install testinstance
 $ ./lava-deployment-tool manage testinstance createsuperuser

At this point you can start your LAVA instance one of two ways:

* Running under the apache web server with::

  $ sudo start lava-instance LAVA_INSTANCE=testinstance

* A development server running on http://localhost:8000 (requires *DEBUG* set to
  true in */srv/lava/instances/testinstance/etc/lava-server/settings.conf*)::

  $ #NOTE: these are equivalent, one just doesn't require lava-deployment-tool
  $ ./lava-deployment-tool manage testinstance runserver
  $ /srv/lava/instances/testinstance/bin/lava-server manage runserver

Quickstart with Vagrant
-----------------------

Vagrant_ is a tool to manage virtual machines. You can use it to keep
development environments isolated from your main system.

.. _Vagrant: http://vagrantup.com/

Obtain Ubuntu Precise "base box"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you have Vagrant installed, you will need an Ubuntu Precise virtual
machine template (a "base box" in Vagrant terms), which can be obtained
with::

 $ vagrant box add ubuntu-precise http://files.vagrantup.com/precise64.box

The above step only needs to be done once. And the base box you get be
reused for other Vagrant projects.

Provide VM with access to host serial port (if needed)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you will need access to a host serial port within VM, add
the following ``config.vm.customize()`` line to ``Vagrantfile`` within
the directory where you have ``lava-deployment-tool``::

 config.vm.customize(["modifyvm", :id, "--uart1", "0x3F8", "4", "--uartmode1", "/dev/ttyUSB0"])

 (Replace ``/dev/ttyUSB0`` with the appropriate host serial device)

The host serial port will be made available as COM1 (/dev/ttyS0) within the VM.

Bring up VM
^^^^^^^^^^^

Now, you can bring a VM with LAVA installed up with a single command,
run from inside the directory where you have ``lava-deployment-tool``::

 $ vagrant up

At the time of writing, the ``vagrant up`` step took a little less than
20 minutes. After ``vagrant up`` finishes, you can access you LAVA
instance by entering http://localhost:8080/ in your web browser.

Software Requirements
=====================

We currently recommend using Ubuntu 12.04.  This tool should work on
Ubuntu versions 11.10 (Oneiric) and newer.

If you'd like to help us with other distributions feel free to contact
us at linaro-validation (at) lists (dot) linaro (dot) org.

Hardware Requirements
=====================

A small LAVA instance can be deployed on any modest hardware. We
recommend at least one 1GB of RAM for runtime activity (this is
shared, on a single host, among the database server, the application
server and the web server). For storage please reserve about 20GB for
application data, especially if you wish to mirror current public LAVA
instance used by Linaro.  LAVA uses append-only models so the storage
requirements will grow at about several GB a year.

Multi-Node hardware requirements
--------------------------------

If the instance is going to be sent any job submissions from third
parties or if your own job submissions are going to use Multi-Node,
there are additional considerations for hardware requirements.

Multi-Node is explicitly about synchronising test operations across
multiple boards and running Multi-Node jobs on a particular instance
will have implications for the workload of that instance. This can
become a particular problem if the instance is running on virtualised
hardware with shared I/O, a limited amount of RAM or a limited number
of available cores.

.. note:: Downloading, preparing and deploying test images can result
 in a lot of synchronous I/O and if this instance is running the server
 and the dispatcher, running synchronised Multi-Node jobs can cause the
 load on that machine to rise significantly, possibly causing the
 server to become unresponsive.

It is strongly recommended that Multi-Node instances use a separate
dispatcher running on non-virtualised hardware so that the (possibly
virtualised) server can continue to operate.

Also, consider the number of boards connected to any one dispatcher. 
MultiNode jobs will commonly compress and decompress several test image
files of several hundred megabytes at precisely the same time. Even
with a powerful multi-core machine, this has been shown to cause
appreciable load. It is worth considering matching the number of boards
to the number of cores for parallel decompression and matching the
amount of available RAM to the number and size of test images which
are likely to be in use.

Before installing
=================

Before you can create your first LAVA instance (standalone, independent LAVA
installation) you must install some shared infrastructure on your machine.
Currently this is the Apache 2 web server, PostgreSQL database server
and Python (and a few python programs and libraries). Because this
installation method is not using pre-built packages you will also need
development headers and a working compiler to build some of the native (C)
extensions for python.

This step is largely automated. To perform it run this command::

 $ ./lava-deployment-tool setup

This step also prepares file-system places for LAVA. In particular it
creates ``/srv/lava/`` where all LAVA instances are later stored.

Creating an instance of LAVA
============================

An instance of LAVA is a self-contained installation of LAVA.  This
means the code that makes up LAVA, configuration data, a Postgres
database, and the log files and test result bundles produced by
running tests.

You can create multiple LAVA instances on a single machine, which is
very valuable for testing and developing LAVA itself.

The code part of an instance is described by a `buildout`_
configuration file, which lives in a branch of the `lava-manifest`_
project on Launchpad.  By default, lava-deployment-tool creates an
instance that uses the buildout.cfg file from the most recent revision
of the lp:lava-manifest branch.

To create an instance, run::

 $ ./lava-deployment-tool install NAME

This will ask you a few questions and then create a fresh instance
called NAME.

You can override details about how to construct the instance:

 1. To override the branch to deploy from, set LAVA_MANIFEST_BRANCH in
    the environment.

 2. To override the name of the buildout config file, set
    LAVA_BUILDOUT_CFG.

 3. To deploy a specific revision of LAVA_MANIFEST_BRANCH, add the
    revision number to the command line::

     $ ./lava-deployment-tool install NAME <revno>

 4. Pay attention to the hostname in the web configuration part. The
    installer will not make the LAVA instance the default virtualhost
    in the apache server. By default the installer will use the output
    of `hostname --fqdn` as the hostname in the Apache config. You can
    override that by setting the LAVA_APACHE_VHOST environment
    variable, or replying to the corresponing prompt at the
    configuartion wizard. Example::

     $ LAVA_APACHE_VHOST=mylavasite.com ./lava-deployment-tool install NAME

    If you want LAVA to be the only web application in that server, you
    can disable the default apache virtualhost before installing LAVA so
    that any hostname users use to reach your server, they will get the
    LAVA web interface::

     $ sudo a2dissite 000-default

See `different kinds of deployment`_ below for more about customizing
instances.

To create an administrator user for a newly-created instance::

 $ ./lava-deployment-tool manage NAME createsuperuser

This user can access the administration panel, edit permissions to other users
and add bundle streams, devices, etc...

.. _buildout: http://www.buildout.org/
.. _lava-manifest: https://launchpad.net/lava-manifest

A note on KVM device types
--------------------------

lava-deployment-tool does not assume that a KVM device-type is always
desirable, so the qemu-kvm package is not installed by default. For
KVM device types to work, install the qemu-kvm package on the
dispatcher. In qemu 1.5 and later, qemu-kvm is a transitional package
depending on qemu-system-x86 which is enough for a KVM device type.

A note on Heartbeat
===================
The heartbeat data of the dispatcher node is sent to the database via
xmlrpc. For this feature to work correctly the ``rpc2_url`` parameter
should be set properly. Login as an admin user and go to
http://localhost/admin/lava_scheduler_app/worker/ (replace localhost
with your server name/IP). Click on the machine which is your master
(in case of distributed deployment), or the machine that is listed in
the page (in case of single LAVA instance). In the page that opens,
set the "Master RPC2 URL:" with the correct value, if it is not set
properly, already. Do not touch any other values in this page except
the description, since all the other fields except description is
populated automatically. The following figure illustrates this:

.. image:: ./images/lava-worker-rpc2-url.png
    :width: 640
    :height: 480

Backing Up LAVA instance
========================

LAVA instances store persistent data in two locations:

 * On the filesystem, in the directory
   ``/srv/lava/$LAVA_INSTANCE/var/lib/lava-server/media``

 * In a PostgreSQL database named ``lava-$LAVA_INSTANCE`` in the
   cluster listening on port $LAVA_DB_PORT.

Backing up those two items is sufficient to preserve the entire system
state.  You can do this by running::

 $ lava-deployment-tool backup $LAVA_INSTANCE

which will create a backup with an ID based on the current date and
time in a directory named
"/srv/lava/backups/$LAVA_INSTANCE/$SNAPSHOT_ID/".  You can make
/srv/lava/backups a symlink to a more appropriate location if you
want.

Generally before backing up you should make sure that LAVA instance is
turned off. This depends on how your instance is started. If you were
using upstart the following shell command should turn LAVA off::

 $ sudo stop lava

If you take a backup while running, you will need to do some manual
cleanup when you restore from it.

Restoring from backup
=====================

Running the command ::

 $ lava-deployment-tool restore $LAVA_INSTANCE $SNAPSHOT_ID

will restore the given snapshot of the named instance.  This will
first erase the database and media files of the named instance, so be
careful what you type!

You can restore an instance from a backup taken from a distinct
instance with a command like::

 $ lava-deployment-tool restore $TARGET_INSTANCE $SOURCE_INSTANCE/$SNAPSHOT_ID

Currently to restore from a backup taken on a different machine, you
have to put it under /srv/lava/backups, then run an appropriate
"lava-deployment-tool restore" command (we will hopefully make this
more natural soon).

You cannot restore to an instance while it is running.

Updating LAVA instance
======================

In some sense, each revision of $LAVA_MANIFEST_BRANCH is a release and
can be updated to (from time to time a revision of lp:lava-manifest will
receive additional testing and be tagged as a release).  You can use
lava-deployment-tool to update to a revision of the LAVA_MANIFEST_BRANCH
that was used for that instance::

 $ ./lava-deployment-tool upgrade $LAVA_INSTANCE <revno>

There are some points to consider:

1) Upgrades may alter the database or persistent media files. It is
   wise to perform a full system backup before each upgrade. While we
   don't anticipate catastrophic failures it's better to be safe than
   sorry. Refer to the previous chapter for details.

2) Upgrades may introduce additional dependencies, which will be
   installed automatically. Periodically we make use of additional
   third party open source libraries. Those libraries will be
   installed for a single LAVA instance _only_. Your system libraries
   are not affected by this step.

3) Upgrades require network access. If you are behind a firewall or a
   corporate HTTP proxy you may experience failures. Please note that the
   upgrade process does not install components without first downloading all of
   the required pieces so in case of a network failure your current installation
   should not be affected. While typically only HTTP and HTTPS protocols are
   being used at times you may see attempts to connect to native protocols used
   by git, bazaar or mercurial.

4) The upgrade works by first installing the new code independently
   from the currently running code, updates a symlink to make the new
   code current, runs any database migrations that are needed and
   restarts the services.  This means that many, but not all, kinds of
   error during upgrade will not result in disruption to the running
   service.

5) Upgrading process rebuilds the collection of static assets served
   by Apache.  During that moment you may encounter a very brief
   failure to resolve some of the static assets (typically images,
   cascading style sheets and javascript libraries)

6) Upgrades may require additional setup stages, at which point the
   upgrade will halt and request that setup is run first.

Upgrading from a pip-based instance to a buildout based instance
----------------------------------------------------------------

In June 2012, we switched from a pip-based installation method to
using buildout. lava-deployment-tool can convert a pip-based
installation to a buildout-based one, but without care this can result
in changes to the set of packages/LAVA extensions installed.

If you have no special requirements as to the extensions that should
be installed you can just run "lava-deployment-tool upgrade
$instance", and say y when prompted.

If you have custom requirements, you should:

 1. create a test instance

 2. in this test instance, create custom buildout config file (see
    `Limited Deployments`_ below) that installs the components you
    want

 3. put this config file into the root of your existing instance as a
    filed called, say, custom.cfg

 4. run LAVA_BUILDOUT_CFG=../../custom.cfg lava-deployment-tool upgrade $instance

Testing this process several times before running it on your
production instance is advisable!

Installing multiple LAVA instances on single IP machine
=======================================================

After installing and starting a LAVA instance using the instructions above,
you can use "toggle" sub command to change how you access the instance.
This is particularly useful for development and testing where you may
not want to, or be able to setup vhosts for all of the instances you
install locally.

For instance, if you wanted to have two instances installed locally
called "test1" and "test2", you can use the "location" toggle to set it
so that you can access them on your local machine using:
http://localhost/test1
http://localhost/test2 ::

 $ lava-deployment-tool toggle $LAVA_INSTANCE location

Then you can access the LAVA instance via:
    http://IP/$LAVA_INSTANCE

You also can turn it back with the command below::

 $ lava-deployment-tool toggle $LAVA_INSTANCE vhost

Then you can access the LAVA instance via:
    http://virtual-host/

There is also a command to toggle all LAVA instances one time::

    lava-deployment-tool toggle_all location

Anatomy of a LAVA instance
==========================

An instance is composed of several parts:

 - A new system user account called lava-$LAVA_INSTANCE
 - A directory tree similar to standard unix filesystem rooted
   in $LAVA_PREFIX/$LAVA_INSTANCE/
 - A postgres user and database both named lava-$LAVA_INSTANCE in the
   cluster that is listening on port $LAVA_DB_PORT (defaulting to 5432
   if not specified, as is usual with postgres).

A note on Postgres versions
---------------------------

By default lava-deployment-tool creates its databases in the default
postgres cluster (on Ubuntu this is the 'main' cluster of whichever
version of postgres was installed first).  Using a different
version/cluster can be achieved by specifying a different value for
LAVA_DB_PORT when prompted when creating an instance.

Moving an instance between clusters is not currently supported (short
of backing up one instance and restoring into another that has its db
in a different cluster).

A note on wsgi buffers
----------------------

When submitting a large amount of data to the django application, 
it is possible to get an HTTP 500 internal server error. This problem
can be fixed by appending ``buffer-size = 65535`` to 
``/srv/lava/instance/<INSTANCE>/etc/lava-server/uwsgi.ini``

Different kinds of deployment
=============================

Production-like
---------------

For our production deployment, we use the buildout-production.cfg
buildout file which completely locks down the version of everything
that's being deployed.  If you want to run the same kind of deployment
as we do, set LAVA_BUILDOUT_CFG to ``buildout-production.cfg`` when
creating the instance::

 $ LAVA_BUILDOUT_CFG=buildout-production.cfg lava-deployment-tool install production

To update the version of some component that is deployed we release
that component, update the buildout-production.cfg file in
lp:lava-manigest to refer to the new version and deploy the new
revision.

Local Development
-----------------

For local development you should pass --developer-mode to
lava-deployment-tool when creating the instance.  This will set
DEBUG=True for Django and install a few extra packages needed to run
LAVA's own tests.

If you want an instance to use a custom branch of a component, you can
drop the branch or a symlink to the branch in
``/srv/lava/instances/$instances/code/current/local`` and re-run
buildout.  For example::

  $ git clone http://git.linaro.org/git-ro/lava/lava-scheduler.git
  $ cd /srv/lava/instances/$instance/code/current
  $ ln -s ~/src/lava-scheduler local/      # The name of the symlink doesn't matter;
                                           # buildout looks at the setup.py
  $ ./bin/buildout

Non-production instances contain some scripts that can help create and
remove symlinks::

  $ git clone http://git.linaro.org/git-ro/lava/lava-scheduler.git
  $ . /srv/lava/instances/testinstance/bin/activate
  $ lava-develop-local ~/src/lava-scheduler
  Determining egg name... lava-scheduler
  + ln -sfT ~/src/lava-scheduler /srv/lava/instances/testinstance/code/current/local/lava-scheduler
  ...
  ... hack ...
  $ lava-undevelop-local ~/src/lava-scheduler
  removed /srv/lava/instances/testinstance/code/current/local/lava-scheduler

Limited Deployments
-------------------

For a limited deployment, for example if you do not want to run the
scheduler, you can set ``LAVA_BUILDOUT_CFG`` to point to a buildout
config file you create.  Currently you can only do this after an
instance is created (unfortunately).  So create an instance::

 $ lava-deployment-tool install limited

Create the custom buildout.cfg::

 $ cat > /srv/lava/instances/limited/code/custom.cfg <<EOF
 [buildout]
 extends = buildout.cfg

 [server]
 eggs -= lava-scheduler
 EOF

And set it to be used in ``instance.conf``::

 $ vim /srv/lava/instances/limited/code/custom.cfg
 $ grep LAVA_BUILDOUT_CFG /srv/lava/instances/limited/code/custom.cfg
 LAVA_BUILDOUT_CFG='../custom.cfg'

Finally, 'upgrade' the instance to get it to use the new config file::

 $ ./lava-deployment-tool upgrade limited


User authentication
^^^^^^^^^^^^^^^^^^^

LAVA frontend is developed using Django_ web application framework
and user authentication and authorization is based on standard `Django
auth subsystems`_. This means that it is fairly easy to integrate authentication
against any source for which Django backend exists. Discussed below are
tested and supported authentication methods for LAVA.

.. _Django: https://www.djangoproject.com/
.. _`Django auth subsystems`: https://docs.djangoproject.com/en/dev/topics/auth/

Launchpad.net OpenID + local user database
==========================================

LAVA server by default is preconfigured to authenticate using
Launchpad.net OpenID service. Additionally, local Django user accounts
database is supported at the same time. Using Launchpad.net (registration
is free) allows for quick start with LAVA bring-up and testing.

As an alternative to external Launchpad.net accounts, local Django user
database can be used. In this case, user accounts should be created by Django
admin prior to use.

Please note that by default, both Launchpad.net OpenID and local database are
enabled, so any user with Launchpad.net account can login into your install.
For production usage, you may want to disable OpenID, or set up groups and
permissions for different users.

Arbitrary OpenID + local user database
------------------------------------------

Instead of using Launchpad.net as SSO (Single Sign-On) authenticator, login
with arbitrary OpenID can be supported. For this, OPENID_SSO_SERVER_URL
setting in ``/srv/lava/instances/<deployment_name>/code/current/server_code/settings/common.py``
should be commented and LAVA instance restarted (``sudo restart lava``).

Alternatively, OPENID_SSO_SERVER_URL can be set to point to another OpenID
server with support for "OpenID 2.0 identifier select mode" to support
SSO within your organization. See `django-openid-auth documentation`_ for
more information.

.. _`django-openid-auth documentation`: http://bazaar.launchpad.net/~django-openid-auth/django-openid-auth/trunk/files

Atlassian Crowd authentication
------------------------------

Atlassian Crowd is authentication hub often used in the enterprise. To install
LAVA with Crowd support, run lava-deployment-tool as::

 $ LAVA_BUILDOUT_CFG=buildout-production-crowd.cfg ./lava-deployment-tool install ...

Then to actually enable and configure Crowd integration:

 1. ``sudo stop lava``

 2. Go to ``/srv/lava/instances/<instance>/etc/lava-server/``.

 3. To settings.conf, add ``"AUTH_CROWD_SERVER_REST_URI"`` key with Crowd REST API URL.
    Follow JSON syntax, pay attention to punctuation.

 4. In the same directory, create file ``crowd.conf`` with the content::

     AUTH_CROWD_APPLICATION_USER='<appuser>'
     AUTH_CROWD_APPLICATION_PASSWORD='<apppasswd>'

    Replace content in angle brackets with your Crowd Application login/password. This
    file is in shell-compatible syntax, you should not use spaces around equal sign and
    additionally should use single quotes.

 5. ``sudo start lava``

 6. Try to login, watch ``/srv/lava/instances/<deployment_name>/var/log/lava-uwsgi.log`` for errors.

Contact and bug reports
========================

Please report bugs using
https://bugs.launchpad.net/lava-deployment-tool/+filebug

Feel free to contact us at validation (at) linaro (dot) org.
