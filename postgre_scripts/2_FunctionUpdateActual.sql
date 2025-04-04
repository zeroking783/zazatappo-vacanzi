CREATE OR REPLACE FUNCTION handle_vacancy_insert()
RETURNS TRIGGER AS $$
BEGIN 
    IF EXISTS (
        SELECT 1 FROM vacancies 
        WHERE link_num = NEW.link_num AND name = NEW.name AND description = NEW.description
    ) THEN
        RETURN NULL;
    END IF;

    UPDATE vacancies SET actual = FALSE 
    WHERE link_num = NEW.link_num AND actual = TRUE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_handle_vacancy_insert
BEFORE INSERT ON vacancies
FOR EACH ROW
EXECUTE FUNCTION handle_vacancy_insert();
