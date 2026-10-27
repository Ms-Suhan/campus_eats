CREATE DATABASE IF NOT EXISTS campuseats;
USE campuseats;

DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  customer_name VARCHAR(100)  NOT NULL,
  item          VARCHAR(100)  NOT NULL,
  quantity      INT           NOT NULL DEFAULT 1,
  total         DECIMAL(8,2)  NOT NULL,
  status        VARCHAR(20)   NOT NULL DEFAULT 'PLACED',
  note          VARCHAR(255)  NULL
);

INSERT INTO orders (customer_name, item, quantity, total, status, note) VALUES
  ('Aarav Shah',  'Masala Dosa',   2, 120.00, 'DELIVERED', NULL),
  ('Diya Patel',  'Veg Sandwich',  1,  60.00, 'PREPARING', 'No onion'),
  ('Rohan Mehta', 'Cold Coffee',   3, 150.00, 'PLACED',    NULL),
  ('Isha Verma',  'Paneer Roll',   1,  90.00, 'PLACED',    'Extra spicy');
