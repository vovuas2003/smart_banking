create table template
(
    id          int8            generated always as identity,
    owner_id    int8            not null,
    percents    jsonb[]         not null,
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
comment on column template.percents     is 'Шаблон в формате jsonb[] - [{"category_id": N, "percentage": N}, {}...]';
comment on column template.description  is 'Описание шаблона';
