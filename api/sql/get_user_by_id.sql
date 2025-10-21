SELECT id, login, password_hash, password_salt, name
FROM "user"
WHERE id = %(id)s;
