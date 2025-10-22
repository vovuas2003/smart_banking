from db import Database
import psycopg2 # для классификации ошибок
from decimal import Decimal # amount в БД это numeric с цифрами после запятой

"""
from decimal import Decimal, ROUND_DOWN

value = Decimal('1.239')
rounded = value.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
print(rounded)  # Вывод: 1.23 (не 1.24, как при обычном округлении)
"""

MY_API_FOLDER = "sql/"

Database.configure(
    dsn = "postgresql://postgres:postgres@localhost:5432/smart_banking",
    minconn = 1,
    maxconn = 10,
)

def main():

    #"""
    print_help()
    return
    #"""

    #create_tables()

    """
    add_users()
    get_users()
    add_cards()
    add_categories()
    """

    """
    my_id = get_user_by_login("vovuas2003")[0]
    my_cards = get_active_cards_by_owner_id(my_id)
    print("My cards:", my_cards)
    my_categories = get_active_categories_by_owner_id(my_id)
    print("My categories:", my_categories)
    add_all_subcards(my_id)
    """

    #"""
    while True:
        s = input("q = quit or type: card_id, category_id, delta_amount, description: ")
        if s == "q":
            break
        rid, tid, delta, desc = s.split()
        rid = int(rid)
        tid = int(tid)
        delta = Decimal(delta)
        if delta > 0:
            ret = inc_money_to_subcard(card_id = rid, category_id = tid, inc_amount = delta, description = desc)
        elif delta < 0:
            delta *= -1
            ret = dec_money_from_subcard(card_id = rid, category_id = tid, dec_amount = delta, description = desc)
        else:
            raise Exception("delta_amount == 0")
        print(ret)
    #"""

    """
    id_to_del = my_cards[0][0]
    ret = delete_card_by_id(id_to_del)
    print("Delete card:", ret)
    my_cards = get_active_cards_by_owner_id(my_id)
    print("My cards:", my_cards)
    """

    """
    not_my_cards = get_active_cards_by_owner_id(get_user_by_login("Fokysn1k")[0])
    print("Not my cards:", not_my_cards)
    """

    #drop_tables()

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
            dec_money_from_subcard]
    for f in func:
        help(f)
        print()

def create_tables():
    folder = "../migration/src/main/resources/db"
    db = Database.instance()
    # migration/src/main/resources/db/_changelog/create_database_v_1_0.xml
    sequence = ["tables/create_user.sql",
                "tables/create_card.sql",
                "tables/create_category.sql",
                "tables/create_template.sql",
                "tables/create_subcard.sql",
                "tables/create_transaction.sql",
                "triggers/add_amount_from_subcard_to_card_and_category.sql"]
    for sql in sequence:
        db.execute(folder + "/" + sql)

def drop_tables():
    folder = "../migration/src/main/resources/db/_rollback"
    db = Database.instance()
    db.execute(folder + "/" + "delete_database_v_1_0.sql")

def add_users():
    ret = add_user(login = "vovuas2003", password_hash = "2003", password_salt = "1337", name = "Вова")
    print("Add user vovuas2003:", ret)
    ret = add_user(login = "vovuas2003", password_hash = "any", password_salt = "Mmm...", name = "Хакер")
    print("Add user vovuas2003 (2nd attemp):", ret)
    ret = add_user(login = "Fokysn1k", password_hash = "42", password_salt = "228", name = "Ярик")
    print("Add user Fokysn1k:", ret)

def add_user(**kwargs):
    """
    Добавляет пользователя в БД.
    Аргументы: login, password_hash, password_salt, name (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, логин занят).
    """
    db = Database.instance()
    try:
        # Вставляем и сразу получаем всю строку
        user_row = db.fetch_one_returning(MY_API_FOLDER + "add_user.sql", params = kwargs)
        return user_row
    except psycopg2.IntegrityError:
        # Логин уже занят (unique constraint)
        return None
    #return None  # Подумать, надо ли здесь этот return на всякий случай, если что-то пошло не так

def get_users():
    ret = get_user_by_id(1)
    print("Get user with id 1:", ret)
    ret = get_user_by_id(2)
    print("Get user with id 2:", ret)
    ret = get_user_by_login("vovuas2003")
    print("Get user vovuas2003:", ret)
    ret = get_user_by_login("Fokysn1k")
    print("Get user Fokysn1k:", ret)
    ret = get_user_by_login("X4k3pM@|-|")
    print("Get user X4k3pM@|-|:", ret)

def get_user_by_id(i):
    """
    Получает пользователя по ID.
    Возвращает строку из БД (кортеж) или None, если не найден.
    """
    db = Database.instance()
    user_row = db.fetch_one(MY_API_FOLDER + "get_user_by_id.sql", params = {'id': i})
    return user_row

def get_user_by_login(login):
    """
    Получает пользователя по логину.
    Возвращает строку из БД (кортеж) или None, если не найден.
    """
    db = Database.instance()
    user_row = db.fetch_one(MY_API_FOLDER + "get_user_by_login.sql", params = {'login': login})
    return user_row

def add_cards():
    i = get_user_by_login("vovuas2003")
    if i is None:
        raise Exception("Cannot find vovuas2003 in database!")
    i = i[0]
    print("vovuas2003 id is", i)
    ret = add_card(owner_id = i, name = "C63p", description = "Основная")
    print("Add card C63p for vovuas2003:", ret)
    ret = add_card(owner_id = i, name = "C63p", description = "Повтор owner_id + name")
    print("Add card C63p for vovuas2003 (2nd attemp):", ret)
    ret = add_card(owner_id = i, name = "Visa", description = "Ненужная")
    print("Add card Visa for vovuas2003:", ret)

def add_card(**kwargs):
    """
    Добавляет карту в БД (is_active True, amount 0).
    Аргументы: owner_id, name, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при конфликте (owner_id + name уже заняты).
    """
    db = Database.instance()
    try:
        card_row = db.fetch_one_returning(MY_API_FOLDER + "add_card.sql", params = kwargs)
        return card_row
    except psycopg2.IntegrityError:
        # Конфликт уникальности owner_id + name
        return None
    # аналогично add_user, подумать про return или другие ошибки

def delete_card_by_id(i):
    """
    Устанавливает is_active = False для карты по ID (мягкое удаление).
    Возвращает обновлённую строку из БД (кортеж) или None, если карта не найдена.
    """
    db = Database.instance()
    card_row = db.fetch_one_returning(MY_API_FOLDER + "delete_card_by_id.sql", params = {'id': i})
    return card_row

def get_active_cards_by_owner_id(owner_id):
    """
    Получает все активные карты пользователя по owner_id.
    Возвращает список строк из БД (кортежей) или пустой список.
    """
    db = Database.instance()
    cards_rows = db.fetch_all(MY_API_FOLDER + "get_active_cards_by_owner_id.sql", params = {'owner_id': owner_id})
    return cards_rows

def add_categories():
    i = get_user_by_login("vovuas2003")
    if i is None:
        raise Exception("Cannot find vovuas2003 in database!")
    i = i[0]
    print("vovuas2003 id is", i)
    ret = add_category(owner_id = i, name = "Еда", description = "По сути вкусно")
    print("Add category Еда for vovuas2003:", ret)
    ret = add_category(owner_id = i, name = "Еда", description = "Повтор owner_id + name")
    print("Add category Еда for vovuas2003 (2nd attemp):", ret)
    ret = add_category(owner_id = i, name = "Вода", description = "Режу воду 10 часов")
    print("Add category Вода for vovuas2003:", ret)

def add_category(**kwargs):
    """
    Добавляет категорию в БД (is_active True, amount 0).
    Аргументы: owner_id, name, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при конфликте (owner_id + name уже заняты).
    """
    db = Database.instance()
    try:
        card_row = db.fetch_one_returning(MY_API_FOLDER + "add_category.sql", params = kwargs)
        return card_row
    except psycopg2.IntegrityError:
        # Конфликт уникальности owner_id + name
        return None
    # аналогично add_user, подумать про return или другие ошибки


def get_active_categories_by_owner_id(owner_id):
    """
    Получает все активные категории пользователя по owner_id.
    Возвращает список строк из БД (кортежей) или пустой список.
    """
    db = Database.instance()
    categories_rows = db.fetch_all(MY_API_FOLDER + "get_active_categories_by_owner_id.sql", params = {'owner_id': owner_id})
    return categories_rows

def add_all_subcards(owner_id):
    car = get_active_cards_by_owner_id(owner_id)
    cat = get_active_categories_by_owner_id(owner_id)
    i = 0
    for r in car:
        for t in cat:
            ret = add_subcard(card_id = r[0], category_id = t[0], description = "add_all_subcards_" + str(i) + ": " + r[2] + t[2])
            print(ret)
            i += 1

def add_subcard(**kwargs):
    """
    Добавляет субкарту в БД (is_active True, amount 0).
    Аргументы: card_id, category_id, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при конфликте (card_id + category_id уже заняты).
    """
    db = Database.instance()
    try:
        subcard_row = db.fetch_one_returning(MY_API_FOLDER + "add_subcard.sql", params = kwargs)
        return subcard_row
    except psycopg2.IntegrityError:
        # Конфликт уникальности card_id + category_id
        return None
    # аналогично add_user, подумать про return или другие ошибки

def get_subcard_by_card_id_and_category_id(**kwargs):
    """
    Получает субкарту из БД.
    Аргументы: card_id, category_id (именованные).
    Возвращает строку из БД (кортеж) или None (если субкарты нет в БД).
    """
    db = Database.instance()
    return db.fetch_one(MY_API_FOLDER + "get_subcard_by_card_id_and_category_id.sql", params = kwargs)

def inc_money_to_subcard(**kwargs):
    """
    Добавляет деньги на субкарту в БД с занесением в логи.
    Аргументы: card_id, category_id, inc_amount, description (именованные).
    Возвращает строку из БД (кортеж) или None (если субкарты нет в БД).
    """
    if kwargs["inc_amount"] <= 0:
        raise ValueError("inc_amount must be positive")

    subcard = get_subcard_by_card_id_and_category_id(**kwargs)
    if subcard is None:
        return None

    db = Database.instance()
    subcard_row = db.fetch_one_returning(MY_API_FOLDER + "inc_money_to_subcard.sql", params = kwargs)
    return subcard_row

def dec_money_from_subcard(**kwargs):
    """
    Вычитает деньги из субкарты в БД с занесением в логи.
    Аргументы: card_id, category_id, dec_amount, description (именованные).
    Возвращает строку из БД (кортеж) или None (если субкарты нет в БД).
    """
    if kwargs["dec_amount"] <= 0:
        raise ValueError("dec_amount must be positive")

    subcard = get_subcard_by_card_id_and_category_id(**kwargs)
    if subcard is None:
        return None

    db = Database.instance()
    subcard_row = db.fetch_one_returning(MY_API_FOLDER + "dec_money_from_subcard.sql", params = kwargs)
    return subcard_row

if __name__ == "__main__":
    main()
