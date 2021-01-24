# tesla-race-analyzer
Tool to analyze lap-based races using data from Tesla API scrapers (TeslaMate)

## Installation

### Database
I strongly suggeest to create a dedicated database for TRAn data.

If you have Teslamate running, you can run following commands using it's credentials
```shell
psql -h 127.0.0.1 -p 5432 -U teslamate -d teslamate -W
```
```sql
drop database tran;  -- if the database exists already
drop user tran;
create database tran;
create user tran with password 'tran_secret';
```

The tables will be created on first app run. The explicit migration is not used for now.

### Docker Compose
Add the following to Teslamate's docker-compose.yml (basically add new service)
```yaml
  tran:
    image: krezac/tesla-race-analyzer:latest
    restart: always
    depends_on:
      - database
    env_file:
      - .env
    # enable this only if you need access thru a port on local machine
    #ports:
    #    - "8888:80"
    labels:
      - 'traefik.enable=true'
      - "traefik.http.middlewares.tm-tran-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.tm-tran-insecure.rule=Host(`sub1.example.com`)"
      - "traefik.http.routers.tm-tran-insecure.middlewares=tm-tran-redirect"
      - "traefik.http.routers.tm-tran.rule=Host(`sub1.example.com`)"
      - "traefik.http.routers.tm-tran.entrypoints=websecure"
      - "traefik.http.routers.tm-tran.tls.certresolver=examplenetchallenge"
    networks:
      - default
      - project1
    volumes:
      - ./etc:/etc/tran  # if you don't want to overwrite config from app, you can add :ro
```

You can delete all the labels if you are not using Traefik to route the requests on your system.

### .env file
You most probably already have .env file containing configuration for Teslamate (i.e. TM_DB_.... variables).
Just add new stuff there. Keep in mind, the TM_DB_... need to be there anyway as they are used by TRAn.

**Important:** Remember to generate your own SECRET_KEY and SECURITY_PASSWORD_SALT to keep your passwords safe.
```shell
# these are probably there already. They NEED to be here

TM_DB_HOST=localhost
TM_DB_PORT=5432
TM_DB_USER=teslamate
TM_DB_PASS=secret
TM_DB_NAME=teslamate

######################################
# the new stuff for TRAn starts here #
######################################

# database configuration
TRAN_DB_HOST=localhost
TRAN_DB_PORT=5432
TRAN_DB_USER=tran
TRAN_DB_PASS=tran_secret
TRAN_DB_NAME=tran

FLASK_APP=src/__init__.py

# generate new one using secrets.token_urlsafe()
SECRET_KEY=Z6hiiEeViGnaf7oGA1ROrVd1SDDcKVs6nj6HGalgdB4

# generate new one using secrets.SystemRandom().getrandbits(128)
SECURITY_PASSWORD_SALT = 245566430388240650680293166088556633912

SECURITY_REGISTERABLE = false # allow registering new users
SECURITY_CHANGEABLE = false  # allow user password change

# this is to create initial admin user. You can remove after first successful run.
# Remember to change the password (and preferably the username as well) to non default one
TRAN_ADMIN_EMAIL=admin@example.com
TRAN_ADMIN_PASSWORD=Super-Secret-Public-Passphrase-43687w465-you-should-always-change-to-something-else
```

### Configuration
Create the etc directory in current directory (otherwise, you will need to change the mapping in docker-compose.yml).
Create a file named **config.json**, the content is like:
```json
{
  "anonymous_index_page": "web_bp.dashboard",
  "admin_index_page": "admin.index",
  "car_id": 3,
  "start_latitude": 49.532277,
  "start_longitude": 12.135311,
  "start_time": "2021-01-02T12:30:00+00:00",
  "hours": 24,
  "start_radius": 0.1,
  "merge_from_lap": 1.0,
  "laps_merged": 1.0,
  "show_previous_laps": 25,
  "previous_laps_table_vertical": false,
  "previous_laps_table_reversed": true,
  "charging_table_vertical": false,
  "charging_table_reversed": true,
  "forecast_exclude_first_laps": 1,
  "forecast_use_last_laps": 5,
  "update_run_background": true,
  "update_status_seconds": 3,
  "update_laps_seconds": 9
}
```
Adjust the values as needed. 

## Ready to go

Start the system
```shell
docker-compose up -d
```
and try to access the application. If you configured the port as above, it would be on http://127.0.0.1:8888, 
if you use the Traefik as above, it would be on https://sub1.example.com

In default configuration, you will be pointed to the dashboard screen.

For the rest of documentation we will assume the app is accessible thru http://127.0.0.1:8888


## Public UI
There are multiple pages available for anonymous user
 * http://127.0.0.1:8888/dashboard - the main screen showing summary of all data
 * http://127.0.0.1:8888/map - just map wit the position and couple of data in bubble
 * http://127.0.0.1:8888/laps - list of lap data

## Admin UI
There is no link to the admin UI from public one intentionally, so random users are not tempted to try.
Go to http://127.0.0.1:8888/login and log in using the credentials you configured above.


------------------------
------------------------
------------------------
## for future use, ignore for now
db migration
flask db init
flask db migrate
flask db upgrade