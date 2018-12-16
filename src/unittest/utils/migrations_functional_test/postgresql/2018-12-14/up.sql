CREATE OR REPLACE FUNCTION increment(i integer) RETURNS integer AS $$
        BEGIN
                RETURN i + 1;
        END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION increment_2(i integer) RETURNS integer
AS $$
        BEGIN
                RETURN i + 2;
        END;
$$ LANGUAGE plpgsql;
