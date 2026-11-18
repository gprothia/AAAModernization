CREATE TABLE users    (username VARCHAR(40) PRIMARY KEY, password VARCHAR(40), role VARCHAR(10), member_id VARCHAR(12));
CREATE TABLE members  (member_id VARCHAR(12) PRIMARY KEY, name VARCHAR(80), phone VARCHAR(20),
                       plan VARCHAR(10), status VARCHAR(10), expires DATE, paid DECIMAL(8,2));
CREATE TABLE payments (id IDENTITY, member_id VARCHAR(12), amount DECIMAL(8,2), kind VARCHAR(10), at TIMESTAMP);

-- Demo data used by the characterisation harness (fixed dates make results repeatable)
INSERT INTO users VALUES ('alice', 'alice', 'MEMBER', 'M-1001'), ('bob', 'bob', 'MEMBER', 'M-1002'),
                         ('ana', 'ana', 'AGENT', NULL);
INSERT INTO members VALUES
  ('M-1001', 'Alice Ng',  '+1 555 010 4455', 'PLUS',    'ACTIVE', DATE '2026-12-31', 124.00),
  ('M-1002', 'Bob Ortiz', '+1 555 010 7788', 'CLASSIC', 'ACTIVE', DATE '2026-03-31',  69.00),
  ('M-1003', 'Cara Diaz', '+1 555 010 2211', 'PREMIER', 'LAPSED', DATE '2025-09-15', 164.00),
  ('M-1004', 'Dan Lee',   '+1 555 010 9933', 'PREMIER', 'ACTIVE', DATE '2026-12-31', 164.00);
