
CREATE TABLE migrations_applied (
    id serial primary key,
    name text not null,
    date TIMESTAMP WITH TIME ZONE not null
);
