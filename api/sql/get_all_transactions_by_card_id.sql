SELECT *
FROM transaction
WHERE card_id_from = %(card_id)s
   OR card_id_to = %(card_id)s;
