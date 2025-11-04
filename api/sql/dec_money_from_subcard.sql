INSERT INTO transaction (card_id_to, category_id_to, card_id_from, category_id_from, amount, description)
VALUES (NULL, NULL, %(card_id)s, %(category_id)s, %(dec_amount)s, %(description)s);

UPDATE subcard
SET amount = amount - %(dec_amount)s
WHERE card_id = %(card_id)s AND category_id = %(category_id)s
RETURNING *;
