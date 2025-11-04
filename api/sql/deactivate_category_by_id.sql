UPDATE category
SET is_active = false
WHERE id = %(id)s;
