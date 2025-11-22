from db import Database

Database.configure(
    dsn = "postgresql://smart_banking:smart_banking@localhost:5433/smart_banking",
    minconn = 1,
    maxconn = 10,
)
DB = Database.instance()

create = True

cr = """
create table "user"
(
    id            int8          generated always as identity,
    login         varchar(30)   not null,
    password text          not null,
    name          varchar(50)   not null,
    --
    constraint user_id_pk primary key (id),
    constraint user_login_unique unique (login)
);

-- create index
create index user_login_idx on "user" (login);


-- comment
comment on table "user" is 'Таблица пользователей';

comment on column "user".login         is 'Логин пользователя';
comment on column "user".password       is 'Захешированный и посоленный пароль пользователя';
comment on column "user".name          is 'Имя пользователя';

create table card
(
    id          int8              generated always as identity,
    owner_id    int8              not null,
    name        varchar(100)      not null,
    amount      numeric(30, 2)    not null,
    is_active   boolean           not null,
    description varchar(300),
    --
    constraint card_id_pk primary key (id),
    constraint card_owner_id_fk foreign key (owner_id) references "user"(id),
    constraint card_owner_id_name_unique unique (owner_id, name)
);

-- create index
create index card_owner_id_idx on card (owner_id);


-- comment
comment on table card is 'Таблица карт пользователя (физическое представление)';

comment on column card.owner_id    is 'Id владельца карты';
comment on column card.name        is 'Название карты';
comment on column card.is_active   is 'Флаг активности карты';
comment on column card.description is 'Описание предназначения карты';

create table category
(
    id          int8            generated always as identity,
    owner_id    int8            not null,
    name        varchar(50)     not null,
    amount      numeric(30, 2)  not null,
    is_active   boolean         not null,
    description varchar(300),
    --
    constraint category_id_pk primary key (id),
    constraint category_owner_id_name_unique unique (owner_id, name),
    constraint category_owner_id_fk foreign key (owner_id) references "user"(id)
);

-- create index
create index category_owner_id_name_idx on category (owner_id, name);


-- comment
comment on table category is 'Таблица категорий пользователя';

comment on column category.owner_id     is 'Id владельца категории';
comment on column category.name         is 'Название категории';
comment on column category.is_active    is 'Флаг активности категории';
comment on column category.description  is 'Описание категории';

create table template
(
    id          int8            generated always as identity,
    owner_id    int8            not null,
    percents    json           not null,
    description varchar(300),
    --
    constraint template_id_pk primary key (id),
    constraint template_owner_id_fk foreign key (owner_id) references "user"(id)
);

-- create index
create index template_owner_id_idx on template (owner_id);

-- comment
comment on table template is 'Таблица шаблонов пользователя';

comment on column template.owner_id     is 'Id владельца шаблона';
comment on column template.percents     is 'Шаблон в формате json';
comment on column template.description  is 'Описание шаблона';

create table subcard
(
    id          int8              generated always as identity,
    card_id     int8              not null,
    category_id int8              not null,
    amount      numeric(30, 2)    not null,
    description varchar(300),
    is_active   boolean           not null,
    --
    constraint subcard_id_pk primary key (id),
    constraint subcard_card_id_category_id_unique unique (card_id, category_id),
    constraint subcard_card_id_fk foreign key (card_id) references card (id),
    constraint subcard_category_id_fk foreign key (category_id) references category (id)
);

create index subcard_card_id_category_id_idx on subcard (card_id, category_id);

create table transaction
(
    id                int8             generated always as identity,
    timestamptz       timestamptz      not null default now(),
    card_id_from      int8,
    card_id_to        int8,
    category_id_from  int8,
    category_id_to    int8,
    amount            numeric(30, 2)   not null,
    description       text,
    --
    constraint transaction_id_pk primary key (id),
    constraint transaction_card_id_from_fk foreign key (card_id_from) references card(id),
    constraint transaction_card_id_to_id_fk foreign key (card_id_to) references card(id),
    constraint transaction_category_id_from_fk foreign key (category_id_from) references category(id),
    constraint transaction_category_id_to_fk foreign key (category_id_to) references category(id)
);

-- create index
create index transaction_card_id_from_idx on transaction (card_id_from);
create index transaction_card_id_to_idx   on transaction (card_id_to);


-- comment
comment on table transaction is 'Таблица шаблонов пользователя';

comment on column transaction.timestamptz          is 'Время, когда была совершена операция';
comment on column transaction.card_id_from         is 'Id карты откуда произошло списание';
comment on column transaction.card_id_to           is 'Id карты куда произошло пополнение';
comment on column transaction.category_id_from     is 'Id категории откуда произошло списание';
comment on column transaction.category_id_to       is 'Id категории куда произошло пополнение';
comment on column transaction.amount               is 'Сумма транзакции';
comment on column transaction.description          is 'Описание транзакции';

create or replace function add_amount_from_subcard_to_card_and_category_fn()
    returns trigger
    language plpgsql
as $$
begin
    if TG_OP = 'INSERT' then
        update card
        set amount = amount + NEW.amount
        where id = NEW.card_id;

        update category
        set amount = amount + NEW.amount
        where id = NEW.category_id;

        return NEW;

    elsif TG_OP = 'UPDATE' then
        -- запрещаем менять связи
        if NEW.card_id <> OLD.card_id then
            raise exception 'Changing card_id in subcard is not allowed';
        end if;

        if NEW.category_id <> OLD.category_id then
            raise exception 'Changing category_id in subcard is not allowed';
        end if;

        -- обновляем суммы только если изменилась сумма subcard
        if NEW.amount <> OLD.amount then
            update card
            set amount = amount + (NEW.amount - OLD.amount)
            where id = NEW.card_id;

            update category
            set amount = amount + (NEW.amount - OLD.amount)
            where id = NEW.category_id;
        end if;

        return NEW;
    end if;

    return NEW;
end;
$$;

create trigger add_amount_from_subcard_to_card_and_category
    after insert or update on subcard
    for each row
execute function add_amount_from_subcard_to_card_and_category_fn();
"""

de = """
drop trigger add_amount_from_subcard_to_card_and_category on subcard;

drop table transaction;
drop table subcard;
drop table template;
drop table card;
drop table category;
drop table "user";
"""

if create:
    DB.execute(cr)
else:
    DB.execute(de)
