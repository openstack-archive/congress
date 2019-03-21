-- policy for monitoring which VMs do not have instance HA configured
CREATE SCHEMA vm_ha;

-- ignore a VM if it has one of these tags
CREATE TABLE vm_ha._except_tag AS
SELECT * FROM (VALUES ('transient'), ('dev'), ('test')) AS t (tag);

-- wrap the table in a view to allow easier extension if the list
-- of tags should be a query rather than a base table.
CREATE VIEW vm_ha.except_tag AS SELECT * FROM vm_ha._except_tag;

-- `warning` view consisting of VMs which do not have HA configured
CREATE VIEW vm_ha.warning AS
SELECT d->>'id' AS server_id
FROM   _compute.servers
WHERE  NOT d->'tags' ?| (SELECT array_agg(tag) FROM vm_ha.except_tag)
AND    NOT d->'metadata' @> '{"HA_Enabled": true}';
