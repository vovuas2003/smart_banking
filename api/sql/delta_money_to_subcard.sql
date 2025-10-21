UPDATE subcard
SET amount = amount + %(delta_amount)s
WHERE id = %(subcard_id)s
RETURNING id, card_id, category_id, amount, description, is_active;