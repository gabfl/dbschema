CREATE TABLE t (c CHAR(20) CHARACTER SET utf8 COLLATE utf8_bin);

CREATE TABLE test (
    blob_col BLOB,
    INDEX(blob_col(10))
);

CREATE TABLE customer (
    id int,
    name varchar(255),
    street varchar(255),
    primary key (id)
);