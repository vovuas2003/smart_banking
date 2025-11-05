SELECT *
FROM transaction
WHERE (card_id_from = %(card_id)s
       OR card_id_to = %(card_id)s)
  AND timestamptz BETWEEN %(time_from)s AND %(time_to)s;
