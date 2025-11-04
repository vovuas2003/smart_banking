SELECT *
FROM template
WHERE owner_id = %(owner_id)s
ORDER BY id;
