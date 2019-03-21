-- policy for monitoring users with forever passwords

CREATE SCHEMA forever_password;

-- `warning` view consisting of enabled users with forever passwords
CREATE VIEW forever_password.warning AS
SELECT d->>'id'        AS user_id,
       d->>'name'      AS user_name,
       d->>'domain_id' AS domain
FROM   _identity.users
WHERE  (d @> '{"password_expires_at": null}'::jsonb
        OR NOT d ? 'password_expires_at')
AND    d @> '{"enabled": true}'::jsonb;
