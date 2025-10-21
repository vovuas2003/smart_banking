UPDATE card
SET is_active = false
WHERE id = %(id)s
RETURNING id, owner_id, name, is_active, description;
