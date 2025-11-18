#########################
# Класс для работы с БД #
#########################

# для вызова справки при запуске этого файла без подключения к базе
if __name__ != "__main__":
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

# TODO: подумать над проверкой активности / восстановлением карты и категории
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
    Получает субкарту по id.
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

# TODO: подумать над проверкой активности / восстановлением карты и категории
@try_return_bool
def inc_money_to_subcard(**kwargs):
    """
    Добавляет (inc = increase) деньги на субкарту с занесением в логи. Подразумевается, что субкарта есть в БД и активна (следует из веб-интерфейса).
    На всякий случай проверяется активность субкарты, но если субкарты нет или она неактивна, то ничего не происходит.
    Аргументы: subcard_id, inc_amount, description (именованные).
    Возвращает True при успехе (даже если субкарты нет в БД или она неактивна), иначе False (в том числе, при неположительном inc_amount).
    """
    if kwargs["inc_amount"] <= 0:
        raise ValueError("inc_amount must be positive")
    DB.execute("""
        WITH updated AS (
            UPDATE subcard
            SET amount = amount + %(inc_amount)s
            WHERE id = %(subcard_id)s AND is_active IS true
            RETURNING card_id, category_id
        )
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        SELECT NULL, NULL, card_id, category_id, %(inc_amount)s, %(description)s
        FROM updated;
    """, params = kwargs)

# TODO: подумать над проверкой активности / восстановлением карты и категории
@try_return_bool
def dec_money_from_subcard(**kwargs):
    """
    Вычитает (dec = decrease) деньги из субкарты с занесением в логи. Подразумевается, что субкарта есть в БД и активна (следует из веб-интерфейса).
    На всякий случай проверяется активность субкарты, но если субкарты нет или она неактивна, то ничего не происходит.
    Также проверяется, что хотим вычесть не больше, чем есть сейчас.
    Аргументы: subcard_id, dec_amount, description (именованные).
    Возвращает True при успехе (даже если субкарты нет в БД, или она неактивна, или недостаточно денег), иначе False (в том числе, при неположительном dec_amount).
    """
    if kwargs["dec_amount"] <= 0:
        raise ValueError("dec_amount must be positive")
    DB.execute("""
        WITH updated AS (
            UPDATE subcard
            SET amount = amount - %(dec_amount)s
            WHERE id = %(subcard_id)s AND is_active IS true AND amount >= %(dec_amount)s
            RETURNING card_id, category_id
        )
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        SELECT card_id, category_id, NULL, NULL, %(dec_amount)s, %(description)s
        FROM updated;
    """, params = kwargs)

# TODO: подумать над проверкой активности / восстановлением карты и категории
@try_return_bool
def transfer_money_between_subcards(**kwargs):
    """
    Переводит деньги между субкартами с занесением в логи.

    Подразумевается, что субкарта, с которой делается перевод, есть в БД и активна.
    В веб-интерфейсе на странице перевода показываем только активные карты и категории, точно нет смысла снимать деньги с несуществующей субкарты
    С неактивной снимать тоже нет смысла, потому что я старался написать API так, чтобы на неактивной субкарте не было денег.
    В общем, неявно проверяется активность этой субкарты, но если субкарты нет или она неактивна, то ничего не происходит.
    Также проверяется, что хотим вычесть не больше, чем есть сейчас.

    Но субкарты, на которую делается перевод (card_id_to + category_id_to), может и не быть в БД (или она есть, но неактивна).
    В таком случае нужная субкарта автоматически создаётся (или активируется).
    Однако в самом начале проверяется, что субкарта, с которой делается перевод, не является комбинацией карты и категории, куда хотим сделать перевод.

    Аргументы: card_id_from, category_id_from, card_id_to, category_id_to, change_amount, description (именованные).
    Возвращает True при успехе (даже если subcard_from нет в БД, или она неактивна, или недостаточно денег), иначе False (в том числе, при неположительном change_amount).
    """
    if kwargs["change_amount"] <= 0:
        raise ValueError("change_amount must be positive")
    DB.execute("""
        WITH from_subcard AS (
            SELECT id AS from_id, card_id AS from_card_id, category_id AS from_category_id, amount 
            FROM subcard 
            WHERE card_id = %(card_id_from)s
                AND category_id = %(category_id_from)s
                AND is_active IS true
                AND amount >= %(change_amount)s
                AND (card_id, category_id) != (%(card_id_to)s, %(category_id_to)s)  -- Запрет перевода на ту же субкарту (бесполезно и засоряет логи)
        ),
        to_upsert AS (
            INSERT INTO subcard (card_id, category_id, amount, description, is_active)
            SELECT %(card_id_to)s, %(category_id_to)s, 0, 'Создано автоматически при переводе.', true
            FROM from_subcard  -- INSERT выполнится только если from_subcard не пуст (т.е. проверка прошла)
            ON CONFLICT (card_id, category_id)
            DO UPDATE SET is_active = true  -- При конфликте (существующая субкарта): активируем, но НЕ меняем amount и description
            RETURNING id AS to_id
        ),
        transfer_out AS (
            UPDATE subcard 
            SET amount = amount - %(change_amount)s 
            WHERE id = (SELECT from_id FROM from_subcard)
        ),
        transfer_in AS (
            UPDATE subcard 
            SET amount = amount + %(change_amount)s 
            WHERE id = (SELECT to_id FROM to_upsert)
        )
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        SELECT from_card_id, from_category_id, %(card_id_to)s, %(category_id_to)s, %(change_amount)s, %(description)s
        FROM from_subcard;
    """, params = kwargs)

# TODO: подумать над проверкой активности / восстановлением карты и категории
@try_return_bool
def apply_distribution_to_card(card_id, distributed_amounts, description = None):
    """
    Применяет распределение поступающих денег на карту (поддержка функции зачисления денег по шаблону после подтверждения пользователем на фронтенде).
    В случае необходимости создаёт субкарты или восстанавливает их, отражает все зачисления в логах.
    Аргументы: card_id, distributed_amounts (словарь с ключами category_id и значениями amount_for_category).
    Опциональный аргумент (для логов): description (по умолчанию равен None, в таком случае создаётся дефолтное описание).
    Возвращает True при успехе, иначе False.
    """
    if description is None:
        description = "Зачисление по шаблону."
    if any(amount <= 0 for amount in distributed_amounts.values()):
        raise ValueError("all amounts must be positive")
    params_seq = [
        {"card_id": card_id, "category_id": cat_id, "amount": amt, "description": description}
        for cat_id, amt in distributed_amounts.items()
    ]   
    DB.executemany("""
        WITH activate_categories AS (
            -- Принудительная активация категории, если она неактивна
            UPDATE category
            SET is_active = true
            WHERE id = %(category_id)s AND is_active IS false
            RETURNING id
        ),
        checks AS (
            -- Проверка активности только карты
            SELECT 1
            WHERE EXISTS (SELECT 1 FROM card WHERE id = %(card_id)s AND is_active IS true)
        ),
        inserted_subcards AS (
            -- Создание или восстановление субкарты (description для новой субкарты по умолчанию)
            INSERT INTO subcard (card_id, category_id, amount, description, is_active)
            SELECT %(card_id)s, %(category_id)s, 0, 'Автоматическое создание при зачислении по шаблону.', true
            FROM checks
            ON CONFLICT (card_id, category_id) DO UPDATE SET
                is_active = true
            RETURNING id
        ),
        updated AS (
            -- Обновление amount на субкарте (только если субкарта активна после возможного восстановления)
            UPDATE subcard
            SET amount = amount + %(amount)s
            FROM checks
            WHERE subcard.card_id = %(card_id)s
              AND subcard.category_id = %(category_id)s
              AND subcard.is_active IS true
            RETURNING subcard.card_id, subcard.category_id, %(amount)s AS amount
        )
        -- Логирование транзакций
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        SELECT NULL, NULL, u.card_id, u.category_id, u.amount, %(description)s
        FROM updated u;
    """, params_seq = params_seq)

# TODO: подумать над проверкой активности / восстановлением карты и категории
@try_return_bool
def collect_category_money_on_one_card(**kwargs):
    """
    Собирает все деньги одной категории на одну карту. Снимаются деньги только с активных субкарт с ненулевым балансом.
    Если на этой карте (на которую собираем деньги) нет нужной субкарты (или она неактивна), то она создаётся (активируется).

    Аргументы: card_id, category_id (именованные).
    Опциональный аргумент (для логов): description (именованный, если равен None или отсутствует, создаётся дефолтное описание).
    Возвращает True при успехе, иначе False.
    """
    card_id = kwargs['card_id']
    category_id = kwargs['category_id']
    description = kwargs.get('description', None)
    if description is None:
        description = "Сбор денег категории на одну карту."
    DB.execute("""
        WITH activate_category AS (
            -- Принудительная активация категории, если она неактивна
            UPDATE category
            SET is_active = true
            WHERE id = %(category_id)s AND is_active IS false
            RETURNING id
        ),
        checks AS (
            -- Проверка активности карты
            SELECT 1
            WHERE EXISTS (SELECT 1 FROM card WHERE id = %(card_id)s AND is_active IS true)
        ),
        target_subcard AS (
            -- Создание или активация субкарты на целевой карте (description для новой субкарты по умолчанию)
            INSERT INTO subcard (card_id, category_id, amount, description, is_active)
            SELECT %(card_id)s, %(category_id)s, 0, 'Автоматическое создание при сборе денег категории на одну карту.', true
            FROM checks
            ON CONFLICT (card_id, category_id) DO UPDATE SET
                is_active = true
            RETURNING id
        ),
        source_subcards AS (
            -- Получение списка субкарт-источников: активные, ненулевой баланс, та же категория, не целевая карта
            SELECT sc.card_id, sc.category_id, sc.amount
            FROM subcard sc
            WHERE sc.category_id = %(category_id)s
              AND sc.card_id != %(card_id)s
              AND sc.is_active IS true
              AND sc.amount != 0
        ),
        updated_sources AS (
            -- Обнуление балансов источников (сбор денег)
            UPDATE subcard
            SET amount = 0
            FROM source_subcards ss
            WHERE subcard.card_id = ss.card_id
              AND subcard.category_id = ss.category_id
            RETURNING ss.card_id, ss.category_id, ss.amount
        ),
        updated_target AS (
            -- Добавление собранной суммы на целевую субкарту
            UPDATE subcard
            SET amount = amount + COALESCE((SELECT SUM(amount) FROM updated_sources), 0)
            FROM checks, target_subcard
            WHERE subcard.card_id = %(card_id)s
              AND subcard.category_id = %(category_id)s
              AND subcard.is_active IS true
            RETURNING subcard.card_id, subcard.category_id, COALESCE((SELECT SUM(amount) FROM updated_sources), 0) AS total_amount
        )
        -- Логирование транзакций для каждого перевода
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        SELECT us.card_id, us.category_id, ut.card_id, ut.category_id, us.amount, %(description)s
        FROM updated_sources us
        CROSS JOIN updated_target ut
        WHERE ut.total_amount != 0;
    """, params = {'card_id': card_id, 'category_id': category_id, 'description': description})

# TODO: подумать над проверкой активности / восстановлением карты и категории
@try_return_bool
def delete_category_and_transfer_money_to_new(**kwargs):
    """
    Деактивация указанной категории (и всех субкарт на ней), создание новой категории с переводом всех денег на неё (с созданием субкарт).
    Аргументы: old_category_id, new_category_name, new_category_description (именованные).
    Опциональный аргумент (для логов): description (именованный, если равен None или отсутствует, создаётся дефолтное описание).
    Возвращает True при успехе, иначе False (в том числе, если не удалось создать новую категорию из-за конфликта уникальности name).
    """
    old_category_id = kwargs['old_category_id']
    new_category_name = kwargs['new_category_name']
    new_category_description = kwargs['new_category_description']
    description = kwargs.get('description', None)
    if description is None:
        description = "Закрытие категории с созданием новой."
    DB.execute("""
        WITH old_category_data AS (
            -- Получение данных старой категории (owner_id для новой)
            SELECT owner_id, name AS old_name
            FROM category
            WHERE id = %(old_category_id)s
        ),
        deactivate_old AS (
            -- Деактивация старой категории
            UPDATE category
            SET is_active = false
            WHERE id = %(old_category_id)s
            RETURNING id
        ),
        deactivate_subcards AS (
            -- Деактивация всех субкарт старой категории
            UPDATE subcard
            SET is_active = false
            WHERE category_id = %(old_category_id)s
            RETURNING card_id, amount
        ),
        create_new_category AS (
            -- Создание новой категории (с owner_id из старой)
            INSERT INTO category (name, description, owner_id, is_active)
            SELECT %(new_category_name)s, %(new_category_description)s, ocd.owner_id, true
            FROM old_category_data ocd
            WHERE NOT EXISTS (SELECT 1 FROM category WHERE name = %(new_category_name)s AND owner_id = ocd.owner_id)
            RETURNING id AS new_category_id
        ),
        transfer_funds AS (
            -- Создание субкарт новой категории на тех же картах и перенос сумм (только с ненулевым балансом)
            INSERT INTO subcard (card_id, category_id, amount, description, is_active)
            SELECT ds.card_id, cnc.new_category_id, ds.amount, 'Автоматическое создание при закрытии категории с созданием новой.', true
            FROM deactivate_subcards ds
            CROSS JOIN create_new_category cnc
            WHERE ds.amount != 0
            ON CONFLICT (card_id, category_id) DO UPDATE SET
                amount = subcard.amount + EXCLUDED.amount,
                is_active = true
            RETURNING card_id, category_id, amount
        )
        -- Логирование переводов (от старой категории к новой на каждой карте)
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        SELECT tf.card_id, %(old_category_id)s, tf.card_id, tf.category_id, tf.amount, %(description)s
        FROM transfer_funds tf;
    """, params = {'old_category_id': old_category_id, 'new_category_name': new_category_name, 'new_category_description': new_category_description, 'description': description})

# TODO: подумать над проверкой активности / восстановлением карты и категории
@try_return_bool
def delete_category_and_transfer_money_to_existing(**kwargs):
    """
    Деактивация одной категории (и всех субкарт на ней) с переводом всех денег на другую существующую категорию (с созданием/активацией субкарт).
    Аргументы: old_category_id, new_category_id (именованные).
    Опциональный аргумент (для логов): description (именованный, если равен None или отсутствует, создаётся дефолтное описание).
    Возвращает True при успехе, иначе False.
    """
    old_category_id = kwargs['old_category_id']
    new_category_id = kwargs['new_category_id']
    description = kwargs.get('description', None)
    if description is None:
        description = "Закрытие категории с переводом денег на существующую."
    DB.execute("""
        WITH owner_check AS (
            -- Проверка равенства owner_id старой и новой категорий
            SELECT 1
            WHERE (SELECT owner_id FROM category WHERE id = %(old_category_id)s) = (SELECT owner_id FROM category WHERE id = %(new_category_id)s)
        ),
        deactivate_old AS (
            -- Деактивация старой категории
            UPDATE category
            SET is_active = false
            WHERE id = %(old_category_id)s
            RETURNING id
        ),
        deactivate_subcards AS (
            -- Деактивация всех субкарт старой категории
            UPDATE subcard
            SET is_active = false
            WHERE category_id = %(old_category_id)s
            RETURNING card_id, amount
        ),
        activate_new AS (
            -- Активация новой категории (если неактивна)
            UPDATE category
            SET is_active = true
            WHERE id = %(new_category_id)s AND is_active IS false
            RETURNING id
        ),
        transfer_funds AS (
            -- Создание/активация субкарт новой категории на тех же картах и перенос сумм (только с ненулевым балансом)
            INSERT INTO subcard (card_id, category_id, amount, description, is_active)
            SELECT ds.card_id, %(new_category_id)s, ds.amount, 'Автоматическое создание при закрытии категории с переводом денег на существующую.', true
            FROM deactivate_subcards ds
            CROSS JOIN owner_check oc
            WHERE ds.amount != 0
            ON CONFLICT (card_id, category_id) DO UPDATE SET
                amount = subcard.amount + EXCLUDED.amount,
                is_active = true
            RETURNING card_id, category_id, amount
        )
        -- Логирование переводов (от старой категории к новой на каждой карте)
        INSERT INTO transaction (card_id_from, category_id_from, card_id_to, category_id_to, amount, description)
        SELECT tf.card_id, %(old_category_id)s, tf.card_id, tf.category_id, tf.amount, %(description)s
        FROM transfer_funds tf;
    """, params = {'old_category_id': old_category_id, 'new_category_id': new_category_id, 'description': description})

#################################
# API для работы с логами из БД #
#################################

# TODO: возвращать в человекочитаемом виде, возможно сразу в excel или сделать отдельную функцию save_to_file и бесплатно задублировать api, также дописать API для общего анализа (только суммарные зачисления + траты + переводы с/на)

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
