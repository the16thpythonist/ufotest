Setting up a CI Station
=======================

The main purpose of the testing functionality is mainly intended to be used for some kind of continuous integration
environment. The testing functionality of the ufotest tool is only one part of the whole setup that goes into such an
environment. The following sections will go into some detail about how the ufotest tool can be used to realize such a
CI like setup for the ufo camera.

Viewing Test Reports
--------------------

One main function of the ufotest tool is the creation of test reports. Whenever a test suite is executed, a new test
report is being generated. This test report is mainly represented as a markdown file which is being saved into an
archive folder for future reviews. This archive folder is located at the path *$HOME/.ufotest/archive*. For every test
run a new folder is created within this archive. These individual folders are named using the date and time at which
the test run was started. Witihin these folders there will always be a *report.md* file which contains the results of
the test run.

But of course this way of presenting the reports is very limited. It relies on the fact that at some point, someone
manually goes to the CI machine and looks up these report files. So there exists another possibility of viewing these
reports as html files from a remote location. This requires some additional effort though. Specifically, this requires
the installation of a web server on the target machine to be able to deliver static content. Additionally the CI
machine should also be accessable using a public domain name to be able to access it from anywhere.

As for the webserver *nginx* would be recommended due to the ease of usage. Install the nginx server using the OS
package manager:

.. code-block:: console

    $ sudo apt-get install nginx

Then configure the config file of nginx at */etc/nginx/nginx.conf* to look like the following

.. code-block:: text

    server {

        listen 80;
        server_name localhost;
        charset utf-8;

        location /archive {
            alias $HOME/.ufotest/archive;
        }
    }

Then you need to restart the server deamon:

.. code-block:: console

    $ sudo service nginx restart

.. note::

    It would be very beneficial if the machine would have a public domain name. This could for example be achieved with
    with comparebly low effort by using a public IPv6 address and a dynamic dns provider such as NoIP. If this were the
    case, the nginx config would have to be adjusted with the chosen hostname.
