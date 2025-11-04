SELECT *
FROM subcard
WHERE card_id = %(card_id)s
  AND is_active = true;
