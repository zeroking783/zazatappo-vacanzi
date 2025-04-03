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