ALTER TABLE distributors RENAME COLUMN address TO city;

ALTER TABLE distributors ALTER COLUMN street DROP NOT NULL;

