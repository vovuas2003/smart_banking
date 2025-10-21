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