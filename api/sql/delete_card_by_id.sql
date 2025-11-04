UPDATE card
SET is_active = false
WHERE id = %(id)s
RETURNING *;
