
CREATE TABLE two (
    id serial primary key,
    name text not null,
    date TIMESTAMP WITH TIME ZONE not null
);

CREATE UNIQUE INDEX ON migrations_applied (id);
