from .db import Database

import functools

def try_return_none(func):
    """
    Декоратор, возвращающий результат выполнения функции или None при исключении.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None
    return wrapper

def try_return_bool(func):
    """
    Декоратор, возвращающий True или False в зависимости от наличия исключения при выполнении функции.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
            return True
        except Exception:
            return False
    return wrapper

Database.configure(
    dsn = "postgresql://postgres:postgres@localhost:5433/smart_banking",
    minconn = 1,
    maxconn = 10,
)
DB = Database.instance()

@try_return_none
def add_user(**kwargs):
    """
    Добавляет пользователя в БД.
    Аргументы: login, password_hash, password_salt, name (именованные).
    Возвращает id из БД при успехе или None при ошибке (например, логин занят).
    """
    return DB.fetch_one_returning("""
        INSERT INTO "user" (login, password_hash, password_salt, name)
        VALUES (%(login)s, %(password_hash)s, %(password_salt)s, %(name)s)
        RETURNING id;
    """, params = kwargs)[0]

@try_return_none
def get_user_by_id(user_id):
    """
    Получает пользователя по id.
    Аргумент: user_id.
    Возвращает строку из БД (кортеж) или None, если не найден или ошибка.
    """
    return DB.fetch_one("""
        SELECT id, login, password_hash, password_salt, name
        FROM "user"
        WHERE id = %(id)s;
    """, params = {'id': user_id})

@try_return_none
def get_user_by_login(login):
    """
    Получает пользователя по логину.
    Аргумент: login.
    Возвращает строку из БД (кортеж) или None, если не найден или ошибка.
    """
    return DB.fetch_one("""
        SELECT id, login, password_hash, password_salt, name
        FROM "user"
        WHERE login = %(login)s;
    """, params = {'login': login})

@try_return_none
def add_card(**kwargs):
    """
    Добавляет карту в БД (is_active True, amount 0).
    Аргументы: owner_id, name, description (именованные).
    Возвращает id из БД при успехе или None при ошибке (например, owner_id + name уже заняты).
    """
    return DB.fetch_one_returning("""
        INSERT INTO card (owner_id, name, amount, is_active, description)
        VALUES (%(owner_id)s, %(name)s, 0, true, %(description)s)
        RETURNING id;
    """, params = kwargs)[0]

@try_return_bool
def delete_card_by_id(card_id):
    """
    Устанавливает is_active = False для карты по id (мягкое удаление).
    Аргумент: card_id.
    Возвращает True при успехе или False при ошибке.
    """
    DB.execute("""
        UPDATE card
        SET is_active = false
        WHERE id = %(id)s;
    """, params = {'id': card_id})

@try_return_none
def get_active_cards_by_owner_id(owner_id):
    """
    Получает все активные карты пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM card
        WHERE owner_id = %(owner_id)s AND is_active IS true
        ORDER BY id;
    """, params = {'owner_id': owner_id})

@try_return_none
def add_category(**kwargs):
    """
    Добавляет категорию в БД (is_active True, amount 0).
    Аргументы: owner_id, name, description (именованные).
    Возвращает id из БД при успехе или None при ошибке (например, owner_id + name уже заняты).
    """
    return DB.fetch_one_returning("""
        INSERT INTO category (owner_id, name, amount, is_active, description)
        VALUES (%(owner_id)s, %(name)s, 0, true, %(description)s)
        RETURNING id;
    """, params = kwargs)[0]

@try_return_none
def get_category_by_id(category_id):
    """
    Получает категорию по id.
    Аргумент: category_id.
    Возвращает строку из БД (кортеж) или None, если не найдена или ошибка.
    """
    return DB.fetch_one_returning("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM category
        WHERE id = %(id)s;
    """, params = {'id': category_id})

@try_return_none
def get_card_by_id(card_id):
    """
    Получает карту по id.
    Аргумент: card_id.
    Возвращает строку из БД (кортеж) или None, если не найдена или ошибка.
    """
    return DB.fetch_one_returning("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM card
        WHERE id = %(id)s;
    """, params = {'id': card_id})

@try_return_none
def get_active_categories_by_owner_id(owner_id):
    """
    Получает все активные категории пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM category
        WHERE owner_id = %(owner_id)s AND is_active IS true
        ORDER BY id;
    """, params = {'owner_id': owner_id})

@try_return_none
def add_subcard(**kwargs):
    """
    Добавляет субкарту в БД (is_active True, amount 0).
    Аргументы: card_id, category_id, description (именованные).
    Возвращает id из БД при успехе или None при ошибке (например, card_id + category_id уже заняты).
    """
    return DB.fetch_one_returning("""
        INSERT INTO subcard (card_id, category_id, amount, description, is_active)
        VALUES (%(card_id)s, %(category_id)s, 0, %(description)s, true)
        RETURNING id;
    """, params = kwargs)[0]

@try_return_none
def get_subcard_by_card_id_and_category_id(**kwargs):
    """
    Получает субкарту из БД.
    Аргументы: card_id, category_id (именованные).
    Возвращает строку из БД (кортеж) или None (если субкарты нет в БД или ошибка).
    """
    return DB.fetch_one("""
        SELECT id, card_id, category_id, amount, description, is_active
        FROM subcard
        WHERE card_id = %(card_id)s AND category_id = %(category_id)s;
    """, params = kwargs)

@try_return_bool
def inc_money_to_subcard(**kwargs):
    """
    Добавляет (inc = increase) деньги на субкарту в БД с занесением в логи.
    Аргументы: card_id, category_id, inc_amount, description (именованные).
    Возвращает True при успехе или False при ошибке (при неположительном inc_amount, или если субкарты нет в БД, или в случае другой ошибки).
    """
    if kwargs["inc_amount"] <= 0:
        raise ValueError("inc_amount must be positive")
    subcard = get_subcard_by_card_id_and_category_id(**kwargs)
    if subcard is None:
        raise LookupError("subcard not found")
    DB.execute("""
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        VALUES (NULL, NULL, %(card_id)s, %(category_id)s, %(inc_amount)s, %(description)s);

        UPDATE subcard
        SET amount = amount + %(inc_amount)s
        WHERE card_id = %(card_id)s AND category_id = %(category_id)s;
    """, params = kwargs)

@try_return_bool
def dec_money_from_subcard(**kwargs):
    """
    Вычитает (dec = decrease) деньги из субкарты в БД с занесением в логи.
    Аргументы: card_id, category_id, dec_amount, description (именованные).
    Возвращает True при успехе или False при ошибке (при неположительном dec_amount, или если субкарты нет в БД, или в случае другой ошибки).
    """
    if kwargs["dec_amount"] <= 0:
        raise ValueError("dec_amount must be positive")
    subcard = get_subcard_by_card_id_and_category_id(**kwargs)
    if subcard is None:
        raise LookupError("subcard not found")
    DB.execute("""
        INSERT INTO transaction (card_id_to, category_id_to, card_id_from, category_id_from, amount, description)
        VALUES (NULL, NULL, %(card_id)s, %(category_id)s, %(dec_amount)s, %(description)s);

        UPDATE subcard
        SET amount = amount - %(dec_amount)s
        WHERE card_id = %(card_id)s AND category_id = %(category_id)s;
    """, params = kwargs)

@try_return_none
def add_template(**kwargs):
    """
    Добавляет шаблон в БД.
    Аргументы: owner_id, percents (по категориям), description (именованные).
    Возвращает id из БД или None при ошибке.
    """
    return DB.fetch_one_returning("""
        INSERT INTO template (owner_id, percents, description)
        VALUES (%(owner_id)s, %(percents)s, %(description)s)
        RETURNING id;
    """, params = kwargs)[0]

@try_return_none
def get_templates_by_owner_id(owner_id):
    """
    Получает все шаблоны пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, owner_id, percents, description
        FROM template
        WHERE owner_id = %(owner_id)s
        ORDER BY id;
    """, params = {'owner_id': owner_id})

@try_return_bool
def delete_template_by_id(template_id):
    """
    Удаляет шаблон.
    Аргумент: template_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute("""
        DELETE FROM template WHERE id = %(id)s;
    """, params = {'id': template_id})

@try_return_bool
def change_template_by_id(**kwargs):
    """
    Меняет шаблон в БД.
    Аргументы: id, percents (по категориям), description (именованные).
    Возвращает True, если успех, иначе False.
    """
    DB.execute("""
        UPDATE template
        SET percents = %(percents)s, description = %(description)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_bool
def change_user_by_id(**kwargs):
    """
    Меняет пароль и/или имя пользователя в БД.
    Аргументы: id, password_hash, password_salt, name (именованные).
    Возвращает True, если успех, иначе False.
    """
    DB.execute("""
        UPDATE "user"
        SET password_hash = %(password_hash)s, password_salt = %(password_salt)s, name = %(name)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_none
def get_inactive_categories_by_owner_id(owner_id):
    """
    Получает все неактивные категории пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM category
        WHERE owner_id = %(owner_id)s AND is_active IS false
        ORDER BY id;
    """, params = {'owner_id': owner_id})

@try_return_bool
def deactivate_category_by_id(category_id):
    """
    'Удаляет' категорию (is_active = False).
    Аргумент: category_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute("""
        UPDATE category
        SET is_active = false
        WHERE id = %(id)s;
    """, params = {'id': category_id})

@try_return_bool
def reactivate_category_by_id(category_id):
    """
    'Восстанавливает' категорию (is_active = True).
    Аргумент: category_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute("""
        UPDATE category
        SET is_active = true
        WHERE id = %(id)s;
    """, params = {'id': category_id})

@try_return_bool
def change_category_by_id(**kwargs):
    """
    Меняет имя и/или описание категории.
    Аргументы: id, name, description (именованные).
    Возвращает True, если успех, иначе False (например, нарушена уникальность).
    """
    DB.execute("""
        UPDATE category
        SET name = %(name)s, description = %(description)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_bool
def change_card_by_id(**kwargs):
    """
    Меняет имя и/или описание карты.
    Аргументы: id, name, description (именованные).
    Возвращает True, если успех, иначе False (например, нарушена уникальность).
    """
    DB.execute("""
        UPDATE card
        SET name = %(name)s, description = %(description)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_bool
def deactivate_subcard_by_id(subcard_id):
    """
    'Удаляет' субкарту (is_active = False).
    Аргумент: subcard_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute("""
        UPDATE subcard
        SET is_active = false
        WHERE id = %(id)s;
    """, params = {'id': subcard_id})

@try_return_bool
def reactivate_subcard_by_id(subcard_id):
    """
    'Восстанавливает' субкарту (is_active = True).
    Аргумент: subcard_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute("""
        UPDATE subcard
        SET is_active = true
        WHERE id = %(id)s;
    """, params = {'id': subcard_id})

@try_return_none
def get_active_subcards_by_card_id(card_id):
    """
    Получает все активные субкарты на карте.
    Аргумент: card_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, card_id, category_id, amount, description, is_active
        FROM subcard
        WHERE card_id = %(card_id)s
          AND is_active IS true;
    """, params = {'card_id': card_id})

@try_return_bool
def transfer_money_between_subcards(**kwargs):
    """
    Переводит деньги между субкартами в БД с занесением в логи.
    Аргументы: card_id_from, category_id_from, card_id_to, category_id_to, change_amount, description (именованные).
    Возвращает True, если успех, иначе False.
    """
    if kwargs["change_amount"] <= 0:
        raise ValueError("change_amount must be positive")
    subcard_from = get_subcard_by_card_id_and_category_id(card_id = kwargs["card_id_from"], category_id = kwargs["category_id_from"])
    if subcard_from is None:
        raise LookupError("subcard_from not found")
    subcard_to = get_subcard_by_card_id_and_category_id(card_id = kwargs["card_id_to"], category_id = kwargs["category_id_to"])
    if subcard_to is None:
        raise LookupError("subcard_to not found")
    DB.execute("""
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        VALUES (%(card_id_from)s, %(category_id_from)s, %(card_id_to)s, %(category_id_to)s, %(change_amount)s, %(description)s);

        UPDATE subcard
        SET amount = amount + %(change_amount)s
        WHERE card_id = %(card_id_to)s AND category_id = %(category_id_to)s;

        UPDATE subcard
        SET amount = amount - %(change_amount)s
        WHERE card_id = %(card_id_from)s AND category_id = %(category_id_from)s;
    """, params = kwargs)

@try_return_none
def get_all_transactions_by_card_id(card_id):
    """
    Получает все транзакции по карте из логов.
    Аргумент: card_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, timestamptz, card_id_from, card_id_to, category_id_from, category_id_to, amount, description
        FROM transaction
        WHERE card_id_from = %(card_id)s
           OR card_id_to = %(card_id)s;
    """, params = {'card_id': card_id})

@try_return_none
def get_time_bound_transactions_by_card_id(**kwargs):
    """
    Получает транзакции в заданном временном промежутке по карте из логов.
    Аргументы: card_id, time_from, time_to (именованные).
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, timestamptz, card_id_from, card_id_to, category_id_from, category_id_to, amount, description
        FROM transaction
        WHERE (card_id_from = %(card_id)s
               OR card_id_to = %(card_id)s)
          AND timestamptz BETWEEN %(time_from)s AND %(time_to)s;
    """, params = kwargs)

@try_return_none
def get_all_transactions_by_category_id(category_id):
    """
    Получает все транзакции по категории из логов.
    Аргумент: category_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, timestamptz, card_id_from, card_id_to, category_id_from, category_id_to, amount, description
        FROM transaction
        WHERE category_id_from = %(category_id)s
           OR category_id_to = %(category_id)s;
    """, params = {'category_id': category_id})

@try_return_none
def get_time_bound_transactions_by_category_id(**kwargs):
    """
    Получает транзакции в заданном временном промежутке по категории из логов.
    Аргументы: category_id, time_from, time_to (именованные).
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, timestamptz, card_id_from, card_id_to, category_id_from, category_id_to, amount, description
        FROM transaction
        WHERE (category_id_from = %(category_id)s
               OR category_id_to = %(category_id)s)
          AND timestamptz BETWEEN %(time_from)s AND %(time_to)s;
    """, params = kwargs)

if __name__ == "__main__":
    import inspect
    for name, obj in list(globals().items()):
        if inspect.isfunction(obj):
            help(obj)
