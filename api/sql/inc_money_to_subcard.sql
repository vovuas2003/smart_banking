INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
VALUES (NULL, NULL, %(card_id)s, %(category_id)s, %(inc_amount)s, %(description)s);

UPDATE subcard
SET amount = amount + %(inc_amount)s
WHERE card_id = %(card_id)s AND category_id = %(category_id)s
RETURNING *;
