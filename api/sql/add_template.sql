INSERT INTO template (owner_id, percents, description)
VALUES (%(owner_id)s, %(percents)s, %(description)s)
RETURNING *;