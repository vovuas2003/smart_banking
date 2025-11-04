UPDATE "user"
SET password_hash = %(password_hash)s, password_salt = %(password_salt)s, name = %(name)s
WHERE id = %(id)s
RETURNING *;
