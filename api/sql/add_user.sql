INSERT INTO "user" (login, password_hash, password_salt, name)
VALUES (%(login)s, %(password_hash)s, %(password_salt)s, %(name)s)
RETURNING *;