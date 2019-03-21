--Sets up jgress user role and privileges
-- Usage:
--     $ psql --set=ingester_role=<ingester> --set=user_role=<user> --set=db_name=<name> -f setup_permissions.sql
--
-- Variables:
--   ingester_role - name of the role used by jgress ingester
--   user_role - name of the role for users writing & evaluating policy over
--   db_name - name of the postgres database used for jgress ingestion

CREATE ROLE :user_role LOGIN;
ALTER DEFAULT PRIVILEGES FOR USER :ingester_role GRANT USAGE ON schemas TO :user_role;
ALTER DEFAULT PRIVILEGES FOR USER :ingester_role GRANT SELECT ON tables TO :user_role;
GRANT ALL PRIVILEGES ON DATABASE :db_name TO :user_role;
