UPDATE category
SET name = %(name)s, description = %(description)s
WHERE id = %(id)s
RETURNING *;
