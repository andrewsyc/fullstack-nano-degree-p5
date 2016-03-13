# Server Configuration Project 5

# Live Site URL
- Login does not work, a custom domain name needs to be assigned, Google+ and Facebook OAuth won't work otherwise.
- http://192.241.253.135/

# SSH
* IP Address: 192.241.253.135
* SSH Port: 2200 or 2222 (22 has been disabled)
* private key for the grader
To login you will use a line something like:
  `ssh -i ~/.ssh/grader.rsa grader@192.241.253.135 -p 2200`
where the `grader.rsa` file is the file that contains the private key for the grader account. This key will be provided in the Notes To Reviewer.

## User Management
### Instructions
* Create a new user named `grader`
* Give the grader the permission to sudo

### Instructions
* Update all packages with 'sudo apt-get update'
* Changed the SSH port from 22 to 2200
* Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80)

### Procedure
```
This setup does a system wide install of dependencies rather than a python virtual environment that is then configured.
```
1. Install and configure Apache to serve a Python mod_wsgi application: `sudo apt-get -y install apache2 libapache2-mod-wsgi`
2. Configure local timezone to UTC
  1. `sudo nano /etc/timezone`
  2. if it's not already, change the timezone to `Etc/UTC` and save the file.
  3. `sudo service cron restart`
3. Install and configure PostgreSQL
  1. `sudo mkdir /var/postgres`
  2. `sudo apt-get -y install postgresql-9.3`
4. Log into Postgres and create a new user named `eventlist` that has limited permissions to your eventlist application database
  1. `su postgres`
  2. CREATE USER eventlist
  3. CREATE DATABASE eventlist
  4. ALTER USER eventlist WITH PASSWORD 'eventlist'
  5. GRANT ALL ON DATABASE eventlist TO eventlist
5. Install git: `sudo apt-get -y install git`
6. I didn't have a GITHUB repo so I just ssh transfered the files to the server.
  1. `sudo mkdir /var/www/catalog/catalog`
  2. Transfer all files to folder from unpacked zip file
7. Install libraries needed for the project to run
  1. `sudo apt-get -y install python-pip libpq-dev python-dev`
  2. `sudo pip install psycopg2` to use postgresql
8. Setup the  database `python /var/www/catalog/catalog/database_setup.py`
10. Create the wsgi file to launch the application:
  1. `sudo nano /var/www/catalog/catalog.wsgi`
```
import sys
sys.path.insert(0, "/var/www/catalog/catalog")
from project import app as application
application.secret_key = 'ultra_secret_key'
```
11. Create the apache webserver configuration file:
  1. `sudo nano /etc/apache2/sites-enabled/000-default.conf`
  2. Delete the entire contents
  3. Paste in:
```
<VirtualHost *:80>
        ServerName 192.241.253.135
        WSGIDaemonProcess catalog
        WSGIScriptAlias / /var/www/catalog/catalog.wsgi
        ErrorLog ${APACHE_LOG_DIR}/error_catalog.log
        CustomLog ${APACHE_LOG_DIR}/access_catalog.log combined
        DocumentRoot /var/www/catalog/catalog
<Directory /var/www/catalog/>
        WSGIProcessGroup catalog
        WSGIApplicationGroup %{GLOBAL}
        Order allow,deny
        Allow from all
</Directory>
        ServerAlias 192.241.253.135
</VirtualHost>
```
  4. `sudo apache2ctl restart` or `sudo service apache2 restart`
  5. Go to ip address assigned to server and application should funtion.