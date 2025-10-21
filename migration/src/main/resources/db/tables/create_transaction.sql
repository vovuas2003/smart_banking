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


