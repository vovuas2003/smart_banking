UPDATE template
SET percents = %(percents)s, description = %(description)s
WHERE id = %(id)s
RETURNING *;
