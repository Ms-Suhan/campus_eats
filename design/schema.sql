

CREATE TABLE Users (
    user_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE Menu (
    menu_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE Food_Items (
    food_item_id INT PRIMARY KEY,
    menu_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    price DECIMAL(10,2) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (menu_id) REFERENCES Menu(menu_id)
);

CREATE TABLE Cart (
    cart_id INT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Cart_Items (
    cart_item_id INT PRIMARY KEY,
    cart_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES Cart(cart_id)
);

CREATE TABLE Orders (
    order_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Order_Items (
    order_item_id INT PRIMARY KEY,
    order_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
);

CREATE TABLE Payments (
    payment_id INT PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    paid_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
