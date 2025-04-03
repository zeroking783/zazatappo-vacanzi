CREATE OR REPLACE FUNCTION deactive_old_vacancy()
RETURNS TRIGGER AS $$
BEGIN 
    UPDATE vacancies SET actual WHERE link_num = NEW.link_num AND actual = TRUE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_deactive_old_vacancy
BEFORE INSERT ON vacancies
FOR EACH ROW
EXECUTE FUNCTION deactive_old_vacancy();

CREATE OR REPLACE FUNCTION insert_if_not_exists()
RETURNS TRIGGER AS $$
BEGIN 
    IF EXISTS (
        SELECT 1 FROM vacancies WHERE link_num = NEW.link_num AND name = NEW.name AND description = NEW.description
    ) THEN
        RETURN NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_insert_if_not_exists
BEFORE INSERT ON vacancies
FOR EACH ROW
EXECUTE FUNCTION insert_if_not_exists();