#########################
# Класс для работы с БД #
#########################

from .db import Database

Database.configure(
    dsn = "postgresql://python_smart_banking_dml:python_smart_banking_dml@localhost:5433/smart_banking",
    minconn = 1,
    maxconn = 10,
)
DB = Database.instance()

###################################
# Декораторы для обработки ошибок #
###################################

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

########################################
# API для работы с пользователями в БД #
########################################

@try_return_none
def add_user(**kwargs):
    """
    Добавляет пользователя в БД.
    Аргументы: login, password, name (именованные).
    Возвращает id из БД при успехе или None при ошибке (например, логин занят).
    """
    return DB.fetch_one("""
        INSERT INTO "user" (login, password, name)
        VALUES (%(login)s, %(password)s, %(name)s)
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
        SELECT id, login, password, name
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
        SELECT id, login, password, name
        FROM "user"
        WHERE login = %(login)s;
    """, params = {'login': login})

@try_return_bool
def change_user_by_id(**kwargs):
    """
    Меняет пароль и/или имя пользователя.
    Аргументы: id, password_hash, password_salt, name (именованные).
    Возвращает True при успехе, иначе False.
    """
    DB.execute("""
        UPDATE "user"
        SET password_hash = %(password_hash)s, password_salt = %(password_salt)s, name = %(name)s
        WHERE id = %(id)s;
    """, params = kwargs)

#################################
# API для работы с картами в БД #
#################################

@try_return_none
def add_card(**kwargs):
    """
    Добавляет карту в БД (is_active true, amount 0). Не пытается восстановить существующую неактивную карту.
    Аргументы: owner_id, name, description (именованные).
    Возвращает id из БД при успехе или None при ошибке (в том числе, owner_id + name уже заняты).
    """
    return DB.fetch_one("""
        INSERT INTO card (owner_id, name, amount, is_active, description)
        VALUES (%(owner_id)s, %(name)s, 0, true, %(description)s)
        RETURNING id;
    """, params = kwargs)[0]

@try_return_none
def get_card_by_id(card_id):
    """
    Получает карту по id.
    Аргумент: card_id.
    Возвращает строку из БД (кортеж) или None, если не найдена или ошибка.
    """
    return DB.fetch_one("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM card
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
def get_inactive_cards_by_owner_id(owner_id):
    """
    Получает все неактивные карты пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM card
        WHERE owner_id = %(owner_id)s AND is_active IS false
        ORDER BY id;
    """, params = {'owner_id': owner_id})

@try_return_bool
def change_card_by_id(**kwargs):
    """
    Меняет имя и/или описание карты.
    Аргументы: id, name, description (именованные).
    Возвращает True при успехе, иначе False (в том числе, owner_id + name уже заняты).
    """
    DB.execute("""
        UPDATE card
        SET name = %(name)s, description = %(description)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_bool
def delete_card_by_id(card_id, description = None):
    """
    Деактивирует карту по id вместе со снятием всех денег (с отражением в логах) со всех её субкарт и их деактивацией.
    Аргумент: card_id.
    Опциональный аргумент (для логов): description (по умолчанию равен None, в таком случае создаётся дефолтное описание).
    Возвращает True при успехе, иначе False.
    """
    if description is None:
        description = "Удаление карты."
    DB.execute("""
        -- Деактивация карты
        UPDATE card
        SET is_active = false
        WHERE id = %(card_id)s;

        -- Деактивация всех субкарт, связанных с картой (только активных)
        UPDATE subcard
        SET is_active = false
        WHERE card_id = %(card_id)s AND is_active IS true;

        -- Снятие баланса с субкарт (если amount != 0) и занесение в логи
        -- Используем CTE для захвата данных перед обновлением, затем обновление и вставка
        WITH subcards_to_process AS (
            SELECT category_id, amount
            FROM subcard
            WHERE card_id = %(card_id)s AND amount != 0
        ),
        update_amounts AS (
            UPDATE subcard
            SET amount = 0
            WHERE card_id = %(card_id)s AND amount != 0
        ),
        insert_logs AS (
            INSERT INTO transaction (card_id_to, category_id_to, card_id_from, category_id_from, amount, description)
            SELECT NULL, NULL, %(card_id)s, category_id, amount, %(description)s
            FROM subcards_to_process
        );
    """, params = {'card_id': card_id, 'description': description})

@try_return_bool
def reactivate_card_by_id(card_id):
    """
    Восстанавливает карту по id (is_active = true). Не восстанавливает субкарты.
    Аргумент: card_id.
    Возвращает True при успехе, иначе False.
    """
    DB.execute("""
        UPDATE card
        SET is_active = true
        WHERE id = %(id)s;
    """, params = {'id': card_id})

#####################################
# API для работы с категориями в БД #
#####################################

@try_return_none
def add_category(**kwargs):
    """
    Добавляет категорию в БД (is_active true, amount 0). Не пытается восстановить существующую неактивную категорию.
    Аргументы: owner_id, name, description (именованные).
    Возвращает id из БД при успехе или None при ошибке (в том числе, owner_id + name уже заняты).
    """
    return DB.fetch_one("""
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
    return DB.fetch_one("""
        SELECT id, owner_id, name, amount, is_active, description
        FROM category
        WHERE id = %(id)s;
    """, params = {'id': category_id})

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
def change_category_by_id(**kwargs):
    """
    Меняет имя и/или описание категории.
    Аргументы: id, name, description (именованные).
    Возвращает True при успехе, иначе False (в том числе, owner_id + name уже заняты).
    """
    DB.execute("""
        UPDATE category
        SET name = %(name)s, description = %(description)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_bool
def delete_category_by_id(category_id, description = None):
    """
    Деактивирует категорию по id вместе со снятием всех денег (с отражением в логах) со всех её субкарт и их деактивацией.
    Аргумент: category_id.
    Опциональный аргумент (для логов): description (по умолчанию равен None, в таком случае создаётся дефолтное описание).
    Возвращает True при успехе, иначе False.
    """
    if description is None:
        description = "Удаление категории."
    DB.execute("""
        -- Деактивация категории
        UPDATE category
        SET is_active = false
        WHERE id = %(category_id)s;

        -- Деактивация всех субкарт, связанных с категорией (только активных)
        UPDATE subcard
        SET is_active = false
        WHERE category_id = %(category_id)s AND is_active IS true;

        -- Снятие баланса с субкарт (если amount != 0) и занесение в логи
        -- Используем CTE для захвата данных перед обновлением, затем обновление и вставка
        WITH subcards_to_process AS (
            SELECT card_id, amount
            FROM subcard
            WHERE category_id = %(category_id)s AND amount != 0
        ),
        update_amounts AS (
            UPDATE subcard
            SET amount = 0
            WHERE category_id = %(category_id)s AND amount != 0
        ),
        insert_logs AS (
            INSERT INTO transaction (card_id_to, category_id_to, card_id_from, category_id_from, amount, description)
            SELECT NULL, NULL, card_id, %(category_id)s, amount, %(description)s
            FROM subcards_to_process
        );
    """, params = {'category_id': category_id, 'description': description})

@try_return_bool
def reactivate_category_by_id(category_id):
    """
    Восстанавливает категорию по id (is_active = true). Не восстанавливает субкарты.
    Аргумент: category_id.
    Возвращает True при успехе, иначе False.
    """
    DB.execute("""
        UPDATE category
        SET is_active = true
        WHERE id = %(id)s;
    """, params = {'id': category_id})

###################################
# API для работы с шаблонами в БД #
###################################

@try_return_none
def add_template(**kwargs):
    """
    Добавляет шаблон в БД.
    Аргументы: owner_id, percents (по категориям), description (именованные).
    Возвращает id из БД или None при ошибке.
    """
    return DB.fetch_one("""
        INSERT INTO template (owner_id, percents, description)
        VALUES (%(owner_id)s, %(percents)s, %(description)s)
        RETURNING id;
    """, params = kwargs)[0]

@try_return_none
def get_template_by_id(template_id):
    """
    Получает шаблон по id.
    Аргумент: template_id.
    Возвращает строку из БД (кортеж) или None, если не найден или ошибка.
    """
    return DB.fetch_one("""
        SELECT id, owner_id, percents, description
        FROM template
        WHERE id = %(id)s;
    """, params = {'id': template_id})

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
def change_template_by_id(**kwargs):
    """
    Меняет шаблон.
    Аргументы: id, percents (по категориям), description (именованные).
    Возвращает True при успехе, иначе False.
    """
    DB.execute("""
        UPDATE template
        SET percents = %(percents)s, description = %(description)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_bool
def delete_template_by_id(template_id):
    """
    Удаляет шаблон из БД.
    Аргумент: template_id.
    Возвращает True при успехе, иначе False.
    """
    DB.execute("""
        DELETE FROM template WHERE id = %(id)s;
    """, params = {'id': template_id})

####################################
# API для работы с субкартами в БД #
####################################

@try_return_none
def add_subcard(**kwargs):
    """
    Добавляет субкарту в БД (is_active true, amount 0).
    Пытается восстановить субкарту, если она уже есть (если при вставке нарушается уникальность card_id + category_id).

    Вызов функции add_subcard в соответствии с архитектурой приложения может быть только из меню карт, причём показываются только активные субкарты.
    В отличие от карт и категорий (неактивные отображаются на странице с добавлением новой карты или категории, пользователь может их восстановить или создать совсем новую),
    активностью субкарты полностью распоряжается внутренняя логика приложения (API), поэтому отдельной функции восстановления субкарты нет.
    Пользователь (и фронтенд) при добавлении категории на карту не знает, что в БД уже может быть эта субкарта в неактивном состоянии (из-за 'удаления' субкарты, карты или категории).
    Можно использовать эту функцию также и для изменения описания субкарты, если не хотим возвращать с фронтенда subcard_id.

    Аргументы: card_id, category_id, description (именованные).
    Возвращает id из БД при успехе или None при ошибке.
    """
    return DB.fetch_one("""
        INSERT INTO subcard (card_id, category_id, amount, description, is_active)
        VALUES (%(card_id)s, %(category_id)s, 0, %(description)s, true)
        ON CONFLICT (card_id, category_id) DO UPDATE SET
            description = EXCLUDED.description,
            is_active = true
        RETURNING id;
    """, params = kwargs)[0]

@try_return_none
def get_subcard_by_id(subcard_id):
    """
    Получает субкарту id.
    Аргумент: subcard_id.
    Возвращает строку из БД (кортеж) или None (если субкарты нет в БД или ошибка).
    """
    return DB.fetch_one("""
        SELECT id, card_id, category_id, amount, description, is_active
        FROM subcard
        WHERE id = %(id)s;
    """, params = {'id': subcard_id})

@try_return_none
def get_subcard_by_card_id_and_category_id(**kwargs):
    """
    Получает субкарту по паре card_id + category_id.
    Аргументы: card_id, category_id (именованные).
    Возвращает строку из БД (кортеж) или None (если субкарты нет в БД или ошибка).
    """
    return DB.fetch_one("""
        SELECT id, card_id, category_id, amount, description, is_active
        FROM subcard
        WHERE card_id = %(card_id)s AND category_id = %(category_id)s;
    """, params = kwargs)

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
def change_subcard_description_by_id(**kwargs):
    """
    Меняет описание субкарты.
    Аргументы: id, description (именованные).
    Возвращает True при успехе, иначе False.
    """
    DB.execute("""
        UPDATE subcard
        SET description = %(description)s
        WHERE id = %(id)s;
    """, params = kwargs)

@try_return_bool
def delete_subcard_by_id(subcard_id, description = None):
    """
    Деактивирует субкарту по id вместе со снятием денег (с отражением в логах) с неё. Для активации использовать функцию add_subcard.
    Аргумент: subcard_id.
    Опциональный аргумент (для логов): description (по умолчанию равен None, в таком случае создаётся дефолтное описание).
    Возвращает True при успехе, иначе False.
    Подразумевается, что субкарта с таким id существует в БД (если нет, ничего не выполнится и вернётся True).
    """
    if description is None:
        description = "Удаление категории с карты."
    DB.execute("""
        WITH old_data AS (
            SELECT card_id, category_id, amount
            FROM subcard
            WHERE id = %(id)s
        ), updated AS (
            UPDATE subcard
            SET is_active = false, amount = 0
            WHERE id = %(id)s
        )
        INSERT INTO transaction (card_id_to, category_id_to, card_id_from, category_id_from, amount, description)
        SELECT NULL, NULL, card_id, category_id, amount, %(description)s
        FROM old_data
        WHERE amount != 0;
    """, params = {'id': subcard_id, 'description': description})

#########################################
# API для различных операций с деньгами #
#########################################

# old TODO: одним sql запросом делать is_active = true, а также создавать субкарту, если её нет
# new TODO: принимать сразу subcard_id; подразумевать, но тихо проверять, что такая субкарта есть в БД
@try_return_bool
def inc_money_to_subcard(**kwargs):
    """
    Добавляет (inc = increase) деньги на субкарту в БД с занесением в логи.
    Аргументы: card_id, category_id, inc_amount, description (именованные).
    Возвращает True при успехе, иначе False (при неположительном inc_amount, или если субкарты нет в БД, или в случае другой ошибки).
    """
    if kwargs["inc_amount"] <= 0:
        raise ValueError("inc_amount must be positive")
    if CHECK_SUBCARD_EXISTS:
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

# TODO: аналогично, как в inc_money_to_subcard
@try_return_bool
def dec_money_from_subcard(**kwargs):
    """
    Вычитает (dec = decrease) деньги из субкарты в БД с занесением в логи.
    Аргументы: card_id, category_id, dec_amount, description (именованные).
    Возвращает True при успехе, иначе False (при неположительном dec_amount, или если субкарты нет в БД, или в случае другой ошибки).
    """
    if kwargs["dec_amount"] <= 0:
        raise ValueError("dec_amount must be positive")
    if CHECK_SUBCARD_EXISTS:
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

# TODO: аналогично, как в inc_money_to_subcard
@try_return_bool
def transfer_money_between_subcards(**kwargs):
    """
    Переводит деньги между субкартами в БД с занесением в логи.
    Аргументы: card_id_from, category_id_from, card_id_to, category_id_to, change_amount, description (именованные).
    Возвращает True при успехе, иначе False.
    """
    if kwargs["change_amount"] <= 0:
        raise ValueError("change_amount must be positive")
    if CHECK_SUBCARD_EXISTS:
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

# TODO
@try_return_bool
def apply_distribution_to_card(card_id, distributed_amounts, description = None):
    """
    Применяет распределение поступающих денег на карту (поддержка функции зачисления денег по шаблону после подтверждения пользователем на фронтенде).
    В случае необходимости создаёт субкарты или восстанавливает их, отражает все зачисления в логах.
    Аргументы: card_id, distributed_amounts (словарь с ключами category_id и значениями amount_for_category).
    Опциональный аргумент (для логов): description (по умолчанию равен None, в таком случае создаётся дефолтное описание).
    Возвращает True при успехе, иначе False.
    """
    pass

# old TODO: переписать на join
# new TODO: категории и так у каждого юзера свои, так что всё проще, но всё остальное как в inc_money_to_subcard
# ???? следить за активностью субкарт
# !!!! сделать позиционные аргументы
@try_return_bool
def collect_category_money_on_one_subcard(**kwargs):
    """
    Собирает все деньги одной категории на одну карту.
    Аргументы: card_id, category_id (именованные).
    Опциональный аргумент (для логов): description (именованный).
    Возвращает True, если не было критичных ошибок, иначе False.
    Эта высокоуровневая функция в процессе работы вызывает низкоуровевые функции, которые обёрнуты в декораторы (поэтому ошибки от них по возможности игнорируются).
    Требуется явная проверка существования субкарты, т.к. для дальнейшей работы нужны данные по субкарте, отсутствующие в аргументах.
    """
    # нужны дальше + не передаём возможный опциональный аргумент description через **kwargs
    card_id = kwargs['card_id']
    category_id = kwargs['category_id']
    subcard = get_subcard_by_card_id_and_category_id(card_id = card_id, category_id = category_id)
    if subcard is None:
        raise LookupError("subcard not found or error")
    subcard_id = subcard[0]
    card = get_card_by_id(card_id)
    if card is None:
        raise LookupError("unexpected error")
    owner_id = card[1]
    owner_cards = get_active_cards_by_owner_id(owner_id)
    if owner_cards is None:
        raise LookupError("unexpected error")
    if 'description' in kwargs:
        description = kwargs['description']
    else:
        description = "Сбор всех денег одной категории на одну карту." # значение description по умолчанию
    for another_card in owner_cards:
        another_card_id = another_card[0]
        if another_card_id == card_id: # пропускаем карту, на которую хотим перевести деньги
            continue
        another_subcard = get_subcard_by_card_id_and_category_id(card_id = another_card_id, category_id = category_id)
        if another_subcard is None: # нет такой категории на такой карте или ошибка
            continue
        change_amount = another_subcard[3]
        if change_amount <= 0: # хотим переводить только положительный баланс (логика согласована с функцией перевода денег)
            continue
        # не проверяем результат, т.е. не считаем критичной возможную ошибку тут, т.к. каждый вызов функции перевода - отдельная SQL транзакция (логика класса в db.py), в случае ошибки всё равно не сможем откатить уже прошедшие переводы
        transfer_money_between_subcards(card_id_from = another_card_id, category_id_from = category_id, card_id_to = card_id, category_id_to = category_id, change_amount = change_amount, description = description)

#################################
# API для работы с логами из БД #
#################################

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

##################################
# Вызов справки по всем функциям #
##################################

if __name__ == "__main__":
    import inspect
    for name, obj in list(globals().items()):
        if inspect.isfunction(obj):
            help(obj)
