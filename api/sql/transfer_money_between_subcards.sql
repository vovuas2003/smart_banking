INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
VALUES (%(card_id_from)s, %(category_id_from)s, %(card_id_to)s, %(category_id_to)s, %(change_amount)s, %(description)s);

UPDATE subcard
SET amount = amount + %(change_amount)s
WHERE card_id = %(card_id_to)s AND category_id = %(category_id_to)s;

UPDATE subcard
SET amount = amount - %(change_amount)s
WHERE card_id = %(card_id_from)s AND category_id = %(category_id_from)s;