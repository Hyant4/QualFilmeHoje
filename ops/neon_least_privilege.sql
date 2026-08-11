-- Execute uma unica vez com o papel neondb_owner usando o psql.
-- A senha e solicitada sem eco e nao fica gravada neste arquivo.
\set ON_ERROR_STOP on
\prompt -s 'Senha forte para qualfilmehoje_app: ' app_password

BEGIN;

CREATE ROLE qualfilmehoje_app
    LOGIN
    PASSWORD :'app_password'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS;

-- PUBLIC e herdado por todos os papeis. Remover CREATE/TEMP daqui impede que
-- o usuario da aplicacao contorne as revogacoes criando objetos persistentes
-- ou temporarios. O proprietario do banco mantem seus privilegios implicitos.
REVOKE CREATE, TEMPORARY ON DATABASE neondb FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

REVOKE ALL PRIVILEGES ON DATABASE neondb FROM qualfilmehoje_app;
REVOKE ALL PRIVILEGES ON SCHEMA public FROM qualfilmehoje_app;

GRANT CONNECT ON DATABASE neondb TO qualfilmehoje_app;
GRANT USAGE ON SCHEMA public TO qualfilmehoje_app;
GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public
    TO qualfilmehoje_app;
-- A aplicacao pode consultar o historico, mas migrations continuam exclusivas
-- do owner e nao podem ser forjadas pela credencial de runtime.
REVOKE INSERT, UPDATE, DELETE
    ON TABLE public.django_migrations
    FROM qualfilmehoje_app;
GRANT SELECT ON TABLE public.django_migrations TO qualfilmehoje_app;
GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public
    TO qualfilmehoje_app;

-- As migrations futuras continuam sendo executadas por neondb_owner. Estes
-- defaults entregam somente DML ao runtime para cada tabela/sequencia nova.
ALTER DEFAULT PRIVILEGES FOR ROLE neondb_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO qualfilmehoje_app;
ALTER DEFAULT PRIVILEGES FOR ROLE neondb_owner IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO qualfilmehoje_app;

COMMIT;

-- Nao conceda CREATE, TRUNCATE, REFERENCES ou TRIGGER a este papel.
