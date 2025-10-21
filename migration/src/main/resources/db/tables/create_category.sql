create table category
(
    id          int8            generated always as identity,
    owner_id    int8            not null,
    name        varchar(50)     not null,
    amount      numeric(30, 4)  not null,
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
