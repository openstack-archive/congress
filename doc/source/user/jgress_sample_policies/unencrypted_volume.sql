-- policy for warning unencryption volumes
CREATE SCHEMA unencrypted_volume;

-- `warning` view consisting of unencrypted volumes in use (attached)
CREATE VIEW unencrypted_volume.warning AS
SELECT d->>'id'          AS volume_id,
       d->'attachements' AS attachements
FROM   _volume.volumes
WHERE  NOT d @> '{"encrypted": true}'::jsonb
AND    jsonb_array_length(d->'attachments') != 0;
