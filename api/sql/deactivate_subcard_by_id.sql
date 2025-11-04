UPDATE subcard
SET is_active = false
WHERE id = %(id)s;
