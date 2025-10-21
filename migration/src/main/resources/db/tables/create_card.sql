create table card
(
    id          int8              generated always as identity,
    owner_id    int8              not null,
    name        varchar(100)      not null,
    amount      numeric(30, 4)    not null,
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
