# Installation

This is a step by step guide for installing Enkidu. While Enkidu can theoretically run on any modern Unix server (and potentially Windows servers), it has only been tested on Ubuntu. Therefore, we recommend using an Ubuntu server when using Enkidu.

Enkidu is designed to work for a single course at a time. Multiple installations of Enkidu can work alongside each other to provide for multiple courses, but a few changes will be needed to made in the following instructions. These are:
* Installing the instances of Enkidu in different locations.
* Having a copy of the Nginx config file (i.e. the provided file `install/enkidu`) for each instance of Enkidu you plan to run.

## Installing Enkidu

The first step for installing Enkidu is to download the files. Create a directory named `enkidu` (another name may be chosen, but make sure to use that in place of `enkidu` whenever it is mentioned in this installation guide) wherever is suitable for you. From this directory, run the following command `git clone https://github.com/eyeofthetiger/codereview.git`. You now have the initial files needed to run Enkidu.

## Dependencies

The following dependencies will be needed to run Enkidu:

* Nginx
* Gunicorn
* Docker
* RabbitMQ
* Python 2.7

For Python, the following libraries will need to be installed:
* Django 1.6
* Celery
* Requests

## Settings

In the file `enkidu/codereview/settings.py`, change the following settings:
* Set `TIME_ZONE` and `LANGUAGE_CODE` to the appropriate values.
 * For timezone options see [this list](http://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
 * For language options see [this list](http://www.i18nguy.com/unicode/language-identifiers.html)
* Configure email settings to use your own email host.
* Set `DEBUG` and `TEMPLATE_DEBUG` to `False`.

## Database

To create a new database:
* Run the following from the directory `enkidu` - `python manage.py syncdb`.
* During this process, create a superuser account when asked.
* Login to the admin screen at http://####/admin, where ##### is the URL to the installed instance of Enkidu.
* On the Admin screen, create a single Course instance. This should be the course that this installation of Enkidu will be used for.

## Server

Enkidu has only been tested on Unix servers, so this installation guide will only cover installation on a Unix server. In particular this guide has been tailored for installation on a server running Ubuntu 14.x.

The server will need a combination of Nginx and Gunicorn to run Enkidu. Within the `sites-enabled` folder of Nginx (usually located at `/etc/nginx/sites-enabled/`), place the provided file `install\enkidu`. At lines 19 and 24, replace `/path/to` with the absolute path to the install location of Enkidu.

Once this is complete, run the command `service nginx restart`.

The final step is to start Gunicorn with Enkidu. To do this, run the following command `gunicorn /path/to/enkidu/codereview/wsgi.py` to start Enkidu. Enkidu should now be accessible on the web.

## Starting Celery

The final step is to enable system messaging by running the script `enkidu\celery.sh`. It is recommended that this is run as a background process.
