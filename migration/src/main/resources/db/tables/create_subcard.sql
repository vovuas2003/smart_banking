create table subcard
(
    id          int8              generated always as identity,
    card_id     int8              not null,
    category_id int8              not null,
    amount      numeric(30, 4)    not null,
    description varchar(300),
    is_active   boolean           not null,
    --
    constraint subcard_id_pk primary key (id),
    constraint subcard_card_id_category_id_unique unique (card_id, category_id),
    constraint subcard_card_id_fk foreign key (card_id) references card (id),
    constraint subcard_category_id_fk foreign key (category_id) references category (id)
);

create index subcard_card_id_category_id_idx on subcard (card_id, category_id);
