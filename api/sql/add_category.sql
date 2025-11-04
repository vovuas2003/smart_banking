INSERT INTO category (owner_id, name, amount, is_active, description)
VALUES (%(owner_id)s, %(name)s, 0, true, %(description)s)
RETURNING *;
