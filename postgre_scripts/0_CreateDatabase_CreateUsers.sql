CREATE DATABASE auto_cv_db;

CREATE USER auto_cv_user WITH PASSWORD 'password';

ALTER DATABASE auto_cv_db OWNER TO auto_cv_user;

GRANT ALL PRIVILEGES ON DATABASE auto_cv_db TO auto_cv_user;

ALTER USER auto_cv_user WITH CREATEROLE;
