SELECT *
FROM category
WHERE owner_id = %(owner_id)s AND is_active = false
ORDER BY id;
