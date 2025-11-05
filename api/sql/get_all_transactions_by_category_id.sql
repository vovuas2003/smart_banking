SELECT *
FROM transaction
WHERE category_id_from = %(category_id)s
   OR category_id_to = %(category_id)s;
