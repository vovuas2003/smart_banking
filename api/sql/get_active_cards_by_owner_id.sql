SELECT id, owner_id, name, is_active, description
FROM card
WHERE owner_id = %(owner_id)s AND is_active = true
ORDER BY id;
