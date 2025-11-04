INSERT INTO subcard (card_id, category_id, amount, description, is_active)
VALUES (%(card_id)s, %(category_id)s, 0, %(description)s, true)
RETURNING *;
