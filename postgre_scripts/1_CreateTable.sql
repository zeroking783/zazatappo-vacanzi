CREATE TABLE vacancies (
    id UUID PRIMARY KEY,
    link_num INT,
    name CHAR(255),
    subdivision CHAR(255),
    date_pab DATE DEFAULT CURRENT_DATE,
    sity VARCHAR(100),
    description TEXT,
    no_experience BOOLEAN DEFAULT FALSE
);

CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(64),
    email VARCHAR(255),
    name VARCHAR(32),
    surname VARCHAR(32),
    phone VARCHAR(20)
);

CREATE TABLE responses (
    vacancie_id UUID,
    user_id INT,
    date_resp DATE DEFAULT CURRENT_DATE,
    decision BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (vacancie_id) REFERENCES vacancies(id) ON DELETE SET NULL
);