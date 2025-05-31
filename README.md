# AWE Server
This repo is responsible for developing the server for the AWE Website

## Local Database Setup
### Install Postgres server and PgAdmin4
#### For Windows
Download PostgreSQL (v17.4): https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

Download PgAdmin4 (v9.2): https://www.pgadmin.org/download/pgadmin-4-windows/

#### For Mac
Download Postgres.app: https://postgresapp.com/downloads.html

`Postgres.app with PostgreSQL 17 (Universal)`

### Creating local DB schema
Go to Tools -> Query Tool
```sql
CREATE DATABASE awe_db;
```

Second query
```sql
CREATE USER awe_admin WITH LOGIN SUPERUSER CREATEDB CREATEROLE INHERIT NOREPLICATION BYPASSRLS PASSWORD 'swe30003';
GRANT ALL PRIVILEGES ON DATABASE awe_db TO awe_admin;
```

## Local Server Setup
__Step 1:__

python -m venv .venv

__Step2:__

- Windows: .venv\Scripts\activate

- MacOS: source .venv/bin/activate

### If using IDE (PyCharm Community, Visual Studio, Intellij, etc.)

    Step 3:
    
    In your IDE, there should be a run config called runserver, choose that one and run in debug mode.

### If using code editor (e.g, VS Code) without the ability to run the config file

    Step 3:
    
    pip install -r requirements.txt
    
    Step 4:
    
    python manage.py makemigrations
    
    Step 5:
    
    python manage.py migrate
    
    Step 6:
    
    python manage.py runserver

## Verify server's working with DB
Go to PgAdmin, checks if this exists under the correct database![image](https://github.com/user-attachments/assets/37c7f98a-0aff-4e7a-b4da-6fbc2828ba2d)


Right-click on the table -> View/Edit data -> All Rows![image](https://github.com/user-attachments/assets/9ea3e73f-f576-4011-b57b-ce6ab75459a5)


Use POSTMAN or your browser, enter http://localhost:8000/api/user, verify that it returns an empty array![image](https://github.com/user-attachments/assets/45fa3041-022d-40b5-a854-974cf61b1c53)

## Load Fixtures
To load the JSON fixtures into your database, run:

-> python manage.py loaddata base/fixtures/fixtures.json
