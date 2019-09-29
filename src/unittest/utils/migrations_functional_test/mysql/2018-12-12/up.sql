CREATE TABLE t1 (
  col1 VARCHAR(10),
  col2 VARCHAR(20),
  col3 VARCHAR(20),
  INDEX (col1, col2(10))
);

CREATE INDEX idx1 ON t1 (col1);
CREATE INDEX idx2 ON t1 (col2);
ALTER TABLE t1 ADD INDEX (col3 DESC);