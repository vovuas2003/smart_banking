from db import Database

import functools

def try_return_none(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None
    return wrapper

def try_return_bool(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
            return True
        except Exception:
            return False
    return wrapper

MY_API_FOLDER = "sql/"
ADD_USER = MY_API_FOLDER + "add_user.sql"
GET_USER_BY_ID = MY_API_FOLDER + "get_user_by_id.sql"
GET_USER_BY_LOGIN = MY_API_FOLDER + "get_user_by_login.sql"
ADD_CARD = MY_API_FOLDER + "add_card.sql"
DELETE_CARD_BY_ID = MY_API_FOLDER + "delete_card_by_id.sql"
GET_ACTIVE_CARDS_BY_OWNER_ID = MY_API_FOLDER + "get_active_cards_by_owner_id.sql"
ADD_CATEGORY = MY_API_FOLDER + "add_category.sql"
GET_ACTIVE_CATEGORIES_BY_OWNER_ID = MY_API_FOLDER + "get_active_categories_by_owner_id.sql"
ADD_SUBCARD = MY_API_FOLDER + "add_subcard.sql"
GET_SUBCARD_BY_CARD_ID_AND_CATEGORY_ID = MY_API_FOLDER + "get_subcard_by_card_id_and_category_id.sql"
INC_MONEY_TO_SUBCARD = MY_API_FOLDER + "inc_money_to_subcard.sql"
DEC_MONEY_FROM_SUBCARD = MY_API_FOLDER + "dec_money_from_subcard.sql"
ADD_TEMPLATE = MY_API_FOLDER + "add_template.sql"
GET_TEMPLATES_BY_OWNER_ID = MY_API_FOLDER + "get_templates_by_owner_id.sql"
DELETE_TEMPLATE_BY_ID = MY_API_FOLDER + "delete_template_by_id.sql"
CHANGE_TEMPLATE_BY_ID = MY_API_FOLDER + "change_template_by_id.sql"
CHANGE_USER_BY_ID = MY_API_FOLDER + "change_user_by_id.sql"
GET_INACTIVE_CATEGORIES_BY_OWNER_ID = MY_API_FOLDER + "get_inactive_categories_by_owner_id.sql"
DEACTIVATE_CATEGORY_BY_ID = MY_API_FOLDER + "deactivate_category_by_id.sql"
REACTIVATE_CATEGORY_BY_ID = MY_API_FOLDER + "reactivate_category_by_id.sql"
CHANGE_CATEGORY_BY_ID = MY_API_FOLDER + "change_category_by_id.sql"
CHANGE_CARD_BY_ID = MY_API_FOLDER + "change_card_by_id.sql"
DEACTIVATE_SUBCARD_BY_ID = MY_API_FOLDER + "deactivate_subcard_by_id.sql"
REACTIVATE_SUBCARD_BY_ID = MY_API_FOLDER + "reactivate_subcard_by_id.sql"
GET_ACTIVE_SUBCARDS_BY_CARD_ID = MY_API_FOLDER + "get_active_subcards_by_card_id.sql"
TRANSFER_MONEY_BETWEEN_SUBCARDS = MY_API_FOLDER + "transfer_money_between_subcards.sql"
GET_ALL_TRANSACTIONS_BY_CARD_ID = MY_API_FOLDER + "get_all_transactions_by_card_id.sql"
GET_TIME_BOUND_TRANSACTIONS_BY_CARD_ID = MY_API_FOLDER + "get_time_bound_transactions_by_card_id.sql"
GET_ALL_TRANSACTIONS_BY_CATEGORY_ID = MY_API_FOLDER + "get_all_transactions_by_category_id.sql"
GET_TIME_BOUND_TRANSACTIONS_BY_CATEGORY_ID = MY_API_FOLDER + "get_time_bound_transactions_by_category_id.sql"

Database.configure(
    dsn = "postgresql://postgres:postgres@localhost:5432/smart_banking",
    minconn = 1,
    maxconn = 10,
)
DB = Database.instance()

def main():
    print_help()

def print_help():
    func = [add_user,
            get_user_by_id,
            get_user_by_login,
            add_card,
            delete_card_by_id,
            get_active_cards_by_owner_id,
            add_category,
            get_active_categories_by_owner_id,
            add_subcard,
            get_subcard_by_card_id_and_category_id,
            inc_money_to_subcard,
            dec_money_from_subcard,
            add_template,
            get_templates_by_owner_id,
            delete_template_by_id,
            change_template_by_id,
            change_user_by_id,
            get_inactive_categories_by_owner_id,
            deactivate_category_by_id,
            reactivate_category_by_id,
            change_category_by_id,
            change_card_by_id,
            deactivate_subcard_by_id,
            reactivate_subcard_by_id,
            get_active_subcards_by_card_id,
            transfer_money_between_subcards,
            get_all_transactions_by_card_id,
            get_time_bound_transactions_by_card_id,
            get_all_transactions_by_category_id,
            get_time_bound_transactions_by_category_id]
    for f in func:
        help(f)
        print()

@try_return_none
def add_user(**kwargs):
    """
    Добавляет пользователя в БД.
    Аргументы: login, password_hash, password_salt, name (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, логин занят).
    """
    return DB.fetch_one_returning(ADD_USER, params = kwargs)

@try_return_none
def get_user_by_id(user_id):
    """
    Получает пользователя по id.
    Аргумент: user_id.
    Возвращает строку из БД (кортеж) или None, если не найден или ошибка.
    """
    return DB.fetch_one(GET_USER_BY_ID, params = {'id': user_id})

@try_return_none
def get_user_by_login(login):
    """
    Получает пользователя по логину.
    Аргумент: login.
    Возвращает строку из БД (кортеж) или None, если не найден или ошибка.
    """
    return DB.fetch_one(GET_USER_BY_LOGIN, params = {'login': login})

@try_return_none
def add_card(**kwargs):
    """
    Добавляет карту в БД (is_active True, amount 0).
    Аргументы: owner_id, name, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, owner_id + name уже заняты).
    """
    return DB.fetch_one_returning(ADD_CARD, params = kwargs)

@try_return_none
def delete_card_by_id(card_id):
    """
    Устанавливает is_active = False для карты по id (мягкое удаление).
    Аргумент: card_id.
    Возвращает обновлённую строку из БД (кортеж) или None, если карта не найдена или ошибка.
    """
    return DB.fetch_one_returning(DELETE_CARD_BY_ID, params = {'id': card_id})

@try_return_none
def get_active_cards_by_owner_id(owner_id):
    """
    Получает все активные карты пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_ACTIVE_CARDS_BY_OWNER_ID, params = {'owner_id': owner_id})

@try_return_none
def add_category(**kwargs):
    """
    Добавляет категорию в БД (is_active True, amount 0).
    Аргументы: owner_id, name, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, owner_id + name уже заняты).
    """
    return DB.fetch_one_returning(ADD_CATEGORY, params = kwargs)

@try_return_none
def get_active_categories_by_owner_id(owner_id):
    """
    Получает все активные категории пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_ACTIVE_CATEGORIES_BY_OWNER_ID, params = {'owner_id': owner_id})

@try_return_none
def add_subcard(**kwargs):
    """
    Добавляет субкарту в БД (is_active True, amount 0).
    Аргументы: card_id, category_id, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, card_id + category_id уже заняты).
    """
    return DB.fetch_one_returning(ADD_SUBCARD, params = kwargs)

@try_return_none
def get_subcard_by_card_id_and_category_id(**kwargs):
    """
    Получает субкарту из БД.
    Аргументы: card_id, category_id (именованные).
    Возвращает строку из БД (кортеж) или None (если субкарты нет в БД или ошибка).
    """
    return DB.fetch_one(GET_SUBCARD_BY_CARD_ID_AND_CATEGORY_ID, params = kwargs)

@try_return_none
def inc_money_to_subcard(**kwargs):
    """
    Добавляет (inc = increase) деньги на субкарту в БД с занесением в логи.
    Аргументы: card_id, category_id, inc_amount, description (именованные).
    Возвращает строку из БД (кортеж) или None (при неположительном inc_amount, или если субкарты нет в БД, или в случае ошибки).
    """
    if kwargs["inc_amount"] <= 0:
        raise ValueError("inc_amount must be positive")
    subcard = get_subcard_by_card_id_and_category_id(**kwargs)
    if subcard is None:
        return None
    return DB.fetch_one_returning(INC_MONEY_TO_SUBCARD, params = kwargs)

@try_return_none
def dec_money_from_subcard(**kwargs):
    """
    Вычитает (dec = decrease) деньги из субкарты в БД с занесением в логи.
    Аргументы: card_id, category_id, dec_amount, description (именованные).
    Возвращает строку из БД (кортеж) или None (при неположительном dec_amount, или если субкарты нет в БД, или в случае ошибки).
    """
    if kwargs["dec_amount"] <= 0:
        raise ValueError("dec_amount must be positive")
    subcard = get_subcard_by_card_id_and_category_id(**kwargs)
    if subcard is None:
        return None
    return DB.fetch_one_returning(DEC_MONEY_FROM_SUBCARD, params = kwargs)

@try_return_none
def add_template(**kwargs):
    """
    Добавляет шаблон в БД.
    Аргументы: owner_id, percents (по категориям), description (именованные).
    Возвращает строку из БД (кортеж) или None при ошибке.
    """
    return DB.fetch_one_returning(ADD_TEMPLATE, params = kwargs)

@try_return_none
def get_templates_by_owner_id(owner_id):
    """
    Получает все шаблоны пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_TEMPLATES_BY_OWNER_ID, params = {'owner_id': owner_id})

@try_return_bool
def delete_template_by_id(template_id):
    """
    Удаляет шаблон.
    Аргумент: template_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute(DELETE_TEMPLATE_BY_ID, params = {'id': template_id})

@try_return_none
def change_template_by_id(**kwargs):
    """
    Меняет шаблон в БД.
    Аргументы: id, percents (по категориям), description (именованные).
    Возвращает строку из БД (кортеж) или None при ошибке.
    """
    return DB.fetch_one_returning(CHANGE_TEMPLATE_BY_ID, params = kwargs)

@try_return_none
def change_user_by_id(**kwargs):
    """
    Меняет пароль и/или имя пользователя в БД.
    Аргументы: id, password_hash, password_salt, name (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке.
    """
    return DB.fetch_one_returning(CHANGE_USER_BY_ID, params=kwargs)

@try_return_none
def get_inactive_categories_by_owner_id(owner_id):
    """
    Получает все неактивные категории пользователя.
    Аргумент: owner_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_INACTIVE_CATEGORIES_BY_OWNER_ID, params = {'owner_id': owner_id})

@try_return_bool
def deactivate_category_by_id(category_id):
    """
    'Удаляет' категорию (is_active = False).
    Аргумент: category_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute(DEACTIVATE_CATEGORY_BY_ID, params = {'id': category_id})

@try_return_bool
def reactivate_category_by_id(category_id):
    """
    'Восстанавливает' категорию (is_active = True).
    Аргумент: category_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute(REACTIVATE_CATEGORY_BY_ID, params = {'id': category_id})

@try_return_none
def change_category_by_id(**kwargs):
    """
    Меняет имя и/или описание категории.
    Аргументы: id, name, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, нарушена уникальность).
    """
    return DB.fetch_one_returning(CHANGE_CATEGORY_BY_ID", params = kwargs)

@try_return_none
def change_card_by_id(**kwargs):
    """
    Меняет имя и/или описание карты.
    Аргументы: id, name, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, нарушена уникальность).
    """
    return DB.fetch_one_returning(CHANGE_CARD_BY_ID, params = kwargs)

@try_return_bool
def deactivate_subcard_by_id(subcard_id):
    """
    'Удаляет' субкарту (is_active = False).
    Аргумент: subcard_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute(DEACTIVATE_SUBCARD_BY_ID, params = {'id': subcard_id})

@try_return_bool
def reactivate_subcard_by_id(subcard_id):
    """
    'Восстанавливает' субкарту (is_active = True).
    Аргумент: subcard_id.
    Возвращает True, если успех, иначе False.
    """
    DB.execute(REACTIVATE_SUBCARD_BY_ID, params = {'id': subcard_id})

@try_return_none
def get_active_subcards_by_card_id(card_id):
    """
    Получает все активные субкарты на карте.
    Аргумент: card_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_ACTIVE_SUBCARDS_BY_CARD_ID, params = {'card_id': card_id})

@try_return_bool
def transfer_money_between_subcards(**kwargs):
    """
    Переводит деньги между субкартами в БД с занесением в логи.
    Аргументы: card_id_from, category_id_from, card_id_to, category_id_to, change_amount, description (именованные).
    Возвращает True, если успех, иначе False.
    """
    if kwargs["change_amount"] <= 0:
        raise ValueError("change_amount must be positive")
    DB.execute(TRANSFER_MONEY_BETWEEN_SUBCARDS, params = kwargs)

@try_return_none
def get_all_transactions_by_card_id(card_id):
    """
    Получает все транзакции по карте из логов.
    Аргумент: card_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_ALL_TRANSACTIONS_BY_CARD_ID, params = {'card_id': card_id})

@try_return_none
def get_time_bound_transactions_by_card_id(**kwargs):
    """
    Получает транзакции в заданном временном промежутке по карте из логов.
    Аргументы: card_id, time_from, time_to (именованные).
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_TIME_BOUND_TRANSACTIONS_BY_CARD_ID, params = kwargs)

@try_return_none
def get_all_transactions_by_category_id(category_id):
    """
    Получает все транзакции по категории из логов.
    Аргумент: category_id.
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_ALL_TRANSACTIONS_BY_CATEGORY_ID, params = {'category_id': category_id})

@try_return_none
def get_time_bound_transactions_by_category_id(**kwargs):
    """
    Получает транзакции в заданном временном промежутке по категории из логов.
    Аргументы: category_id, time_from, time_to (именованные).
    Возвращает список (возможно пустой) строк из БД (кортежей), None при ошибке.
    """
    return DB.fetch_all(GET_TIME_BOUND_TRANSACTIONS_BY_CATEGORY_ID, params = kwargs)

if __name__ == "__main__":
    main()
