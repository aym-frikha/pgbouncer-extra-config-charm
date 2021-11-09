# charm-pgbouncer-extra-config

# Overview


Pgbouncer is a connection pooler for PostgreSQL databases. This charm is able to send extra configuration for the pgbouncer charm in order to add extra databases support (database section) as well as allow users that are not listed in userlist.txt file to be authenticated.

# Usage

## Configuration

This section covers common and/or important configuration options. See file
`config.yaml` for the full list of options, along with their descriptions and
default values. See the [Juju documentation][juju-docs-config-apps] for details
on configuring applications.

## Deployment
The following is an example deployment of the postgresql cluster with pgbouncer and the extra configuration through this charm.
First of all we need to create a local juju environment on a ubuntu machine

``` juju bootstrap localhost ```

### Postgresql cluster bundle

To use the current charm (pgbouncer-extra-config) efficiently we need to integrate it with pgbouncer charm and postgresql charm. The following is an example bundle:

```yaml
    series: focal
    applications:
      postgresql:
        charm: cs:postgresql
        num_units: 3
      pgbouncer:
        charm: cs:pgbouncer
        num_units: 3
      pgbouncer-extra-config:
        charm: cs:pgbouncer-extra-config
        options:
          auth_user: "test_auth"
          auth_query: "SELECT usename, passwd FROM pg_shadow WHERE usename = $1 ;"  
    relations:
    - ["postgresql:db-admin", "pgbouncer:backend-db-admin"]
    - ["pgbouncer-extra-config", "pgbouncer"]
```



### Postgresql cluster deployment and usage

Now we are able to deploy the postgresql cluster:

 juju deploy ./bundle-test.yaml

After the deployment is finished, we can run this small script to allow us accessing the postgresql databse and create new databases:

```
#!/bin/bash
auth_user=`juju config pgbouncer-extra-config auth_user`   

password=`juju run --unit  pgbouncer/0 "cat /etc/pgbouncer/userlist.txt | grep $auth_user" | awk '{print $2}'`

primary_postgres_db=`juju run --unit postgresql/leader "unit-get private-address"`

juju config pgbouncer-extra-config extra_db_config="postgres = host=$primary_postgres_db  port=5432 dbname=postgres user=$auth_user"

primary_pgbouncer=`juju run --unit pgbouncer/leader "unit-get private-address"`

echo -e "Now you are able tot connect to your postgresql server and create users and dbs using this command"

echo -e "psql -h $primary_pgbouncer  -p 6432 -U $auth_user postgres "

echo -e "Please use this password to connect: $password"
```

This script output will give us the psql command to access the postgres database as well as the password:

psql -h $primary_pgbouncer  -p 6432 -U test_auth postgres

We can create a new database and a new user using this command:


``` create database mydb;
    create user myuser with encrypted password 'mypass';
    grant all privileges on database mydb to myuser;
```
Pgbouncer should handle this new database after configuring the charm with this command:

``` juju config pgbouncer-extra-config extra_db_config="mydb_primary = host=<postgresql leader ip>  port=5432 dbname=mydb" ```



# Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

# Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. You can run tests with tox.
