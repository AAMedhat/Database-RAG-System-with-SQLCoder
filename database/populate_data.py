import psycopg2
from psycopg2.extras import execute_values
import random
import faker

# Initialize faker
fake = faker.Faker()

# Database connection parameters for initial connection (without specifying a database)
INITIAL_DB_PARAMS = {
    'user': 'postgres',
    'password': '01154555448963',
    'host': 'localhost',
    'port': '5432'
}

# Database connection parameters for test_db
DB_PARAMS = {
    'dbname': 'test_db',
    'user': 'postgres',
    'password': '01154555448963',
    'host': 'localhost',
    'port': '5432'
}

def create_database_if_not_exists():
    """Create the test_db database if it doesn't exist"""
    try:
        # Connect to the default postgres database first
        conn = psycopg2.connect(**INITIAL_DB_PARAMS)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'test_db'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating test_db database...")
            cursor.execute("CREATE DATABASE test_db")
            print("Database created successfully!")
        else:
            print("Database test_db already exists.")
            
        cursor.close()
        conn.close()
        
        # Create tables in the test_db database
        check_and_create_tables()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        
def check_and_create_tables():
    """Check which tables need to be created"""
    try:
        # Connect to the test_db database
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Create tables that don't exist
        if 'users' not in existing_tables:
            create_users_table(cursor)
        if 'products' not in existing_tables:
            create_products_table(cursor)
        if 'categories' not in existing_tables:
            create_categories_table(cursor)
        if 'orders' not in existing_tables:
            create_orders_table(cursor)
        if 'order_items' not in existing_tables:
            create_order_items_table(cursor)
        if 'reviews' not in existing_tables:
            create_reviews_table(cursor)
        if 'suppliers' not in existing_tables:
            create_suppliers_table(cursor)
        if 'product_suppliers' not in existing_tables:
            create_product_suppliers_table(cursor)
            
        # Create indexes if needed
        create_indexes(cursor)
            
        cursor.close()
        conn.close()
        print("Table check and creation completed.")
    except Exception as e:
        print(f"Error checking/creating tables: {e}")

def create_users_table(cursor):
    cursor.execute("""
        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            full_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT true
        );
    """)
    print("Created users table")
    
def create_products_table(cursor):
    cursor.execute("""
        CREATE TABLE products (
            product_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            category VARCHAR(50),
            stock_quantity INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Created products table")
    
def create_categories_table(cursor):
    cursor.execute("""
        CREATE TABLE categories (
            category_id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            parent_id INTEGER REFERENCES categories(category_id)
        );
    """)
    print("Created categories table")
    
def create_orders_table(cursor):
    cursor.execute("""
        CREATE TABLE orders (
            order_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            shipping_address TEXT
        );
    """)
    print("Created orders table")
    
def create_order_items_table(cursor):
    cursor.execute("""
        CREATE TABLE order_items (
            order_item_id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(order_id),
            product_id INTEGER REFERENCES products(product_id),
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL
        );
    """)
    print("Created order_items table")
    
def create_reviews_table(cursor):
    cursor.execute("""
        CREATE TABLE reviews (
            review_id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(product_id),
            user_id INTEGER REFERENCES users(user_id),
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Created reviews table")
    
def create_suppliers_table(cursor):
    cursor.execute("""
        CREATE TABLE suppliers (
            supplier_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            contact_person VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(20),
            address TEXT
        );
    """)
    print("Created suppliers table")
    
def create_product_suppliers_table(cursor):
    cursor.execute("""
        CREATE TABLE product_suppliers (
            product_id INTEGER REFERENCES products(product_id),
            supplier_id INTEGER REFERENCES suppliers(supplier_id),
            supply_price DECIMAL(10,2),
            PRIMARY KEY (product_id, supplier_id)
        );
    """)
    print("Created product_suppliers table")
    
def create_indexes(cursor):
    # Check existing indexes
    cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename IN ('users', 'products', 'orders', 'order_items', 'reviews', 'categories', 'product_suppliers')
    """)
    existing_indexes = {row[0] for row in cursor.fetchall()}
    
    # Create indexes that don't exist
    indexes = [
        ("idx_users_username", "CREATE INDEX idx_users_username ON users(username);"),
        ("idx_users_email", "CREATE INDEX idx_users_email ON users(email);"),
        ("idx_products_category", "CREATE INDEX idx_products_category ON products(category);"),
        ("idx_orders_user_id", "CREATE INDEX idx_orders_user_id ON orders(user_id);"),
        ("idx_orders_status", "CREATE INDEX idx_orders_status ON orders(status);"),
        ("idx_order_items_order_id", "CREATE INDEX idx_order_items_order_id ON order_items(order_id);"),
        ("idx_reviews_product_id", "CREATE INDEX idx_reviews_product_id ON reviews(product_id);"),
        ("idx_reviews_user_id", "CREATE INDEX idx_reviews_user_id ON reviews(user_id);"),
        ("idx_categories_parent_id", "CREATE INDEX idx_categories_parent_id ON categories(parent_id);"),
        ("idx_product_suppliers_product_id", "CREATE INDEX idx_product_suppliers_product_id ON product_suppliers(product_id);"),
        ("idx_product_suppliers_supplier_id", "CREATE INDEX idx_product_suppliers_supplier_id ON product_suppliers(supplier_id);")
    ]
    
    for index_name, create_statement in indexes:
        if index_name not in existing_indexes:
            cursor.execute(create_statement)
            print(f"Created index {index_name}")

def connect_db():
    return psycopg2.connect(**DB_PARAMS)

def populate_users(conn, num_records=1000):
    # First check if table is empty
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        
        if count > 0:
            print(f"Users table already has {count} records. Skipping.")
            return
    
    # Generate fake usernames and emails
    usernames = set()
    emails = set()
    users_data = []
    
    for _ in range(num_records * 2):  # Generate more than needed to account for duplicates
        username = fake.user_name()
        email = fake.email()
        
        # Skip if username or email already in our lists
        if username in usernames or email in emails:
            continue
            
        usernames.add(username)
        emails.add(email)
        
        users_data.append((
            username,
            email,
            fake.name(),
            fake.date_time_this_year(),
            random.choice([True, False])
        ))
        
        # Stop once we have enough unique users
        if len(users_data) >= num_records:
            break
    
    # Double-check that we don't have any users in the database already
    with conn.cursor() as cur:
        # Check for duplicate usernames
        placeholders = ','.join(['%s'] * len(usernames))
        cur.execute(f"SELECT username FROM users WHERE username IN ({placeholders})", 
                    list(usernames))
        existing_usernames = {row[0] for row in cur.fetchall()}
        
        # Check for duplicate emails
        placeholders = ','.join(['%s'] * len(emails))
        cur.execute(f"SELECT email FROM users WHERE email IN ({placeholders})", 
                    list(emails))
        existing_emails = {row[0] for row in cur.fetchall()}
        
        # Filter out users with existing usernames or emails
        filtered_users = [
            user for user in users_data 
            if user[0] not in existing_usernames and user[1] not in existing_emails
        ]
        
        if not filtered_users:
            print("No new unique users to add.")
            return
            
        # Insert only unique users
        execute_values(cur, """
            INSERT INTO users (username, email, full_name, last_login, is_active)
            VALUES %s
        """, filtered_users)
        
    conn.commit()
    print(f"Added {len(filtered_users)} new users")

def populate_categories(conn):
    categories = [
        ('Electronics', 'Electronic devices and accessories'),
        ('Clothing', 'Fashion items and accessories'),
        ('Books', 'Physical and digital books'),
        ('Home & Garden', 'Home improvement and gardening items'),
        ('Sports', 'Sports equipment and accessories')
    ]
    
    # First check which categories already exist
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM categories")
        existing_categories = {row[0] for row in cur.fetchall()}
        
        # Filter out categories that already exist
        new_categories = [cat for cat in categories if cat[0] not in existing_categories]
        
        # Insert only new categories
        if new_categories:
            execute_values(cur, """
                INSERT INTO categories (name, description)
                VALUES %s
            """, new_categories)
            print(f"Added {len(new_categories)} new categories")
        else:
            print("No new categories to add")
    conn.commit()

def populate_products(conn, num_records=1000):
    # Check if products already exist
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM products")
        product_count = cur.fetchone()[0]
        
        if product_count > 0:
            print(f"Products table already has {product_count} records. Skipping.")
            return
            
    # If no products exist, generate and insert new products
    products_data = []
    categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports']
    
    for _ in range(num_records):
        # Use fake.word() + random words instead of product_name
        product_name = fake.word().capitalize() + " " + fake.word().capitalize()
        
        products_data.append((
            product_name,
            fake.text(max_nb_chars=200),
            round(random.uniform(10, 1000), 2),
            random.choice(categories),
            random.randint(0, 100)
        ))
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO products (name, description, price, category, stock_quantity)
            VALUES %s
        """, products_data)
    conn.commit()
    print(f"Added {len(products_data)} new products")

def populate_suppliers(conn, num_records=50):
    # Check if suppliers already exist
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM suppliers")
        supplier_count = cur.fetchone()[0]
        
        if supplier_count > 0:
            print(f"Suppliers table already has {supplier_count} records. Skipping.")
            return
            
    # If no suppliers exist, generate and insert new suppliers
    suppliers_data = []
    for _ in range(num_records):
        # Generate a shorter phone number that fits within 20 characters
        phone = fake.numerify(text="###-###-####")  # Simple format that won't exceed 20 chars
        
        suppliers_data.append((
            fake.company(),
            fake.name(),
            fake.email(),
            phone,
            fake.address()
        ))
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO suppliers (name, contact_person, email, phone, address)
            VALUES %s
        """, suppliers_data)
    conn.commit()
    print(f"Added {len(suppliers_data)} new suppliers")

def populate_orders(conn, num_records=1000):
    # Check if orders already exist (this is also checked in main, but adding here for consistency)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM orders")
        order_count = cur.fetchone()[0]
        
        if order_count > 0:
            print(f"Orders table already has {order_count} records. Skipping.")
            return
            
    # Get valid user IDs from the database
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM users")
        valid_user_ids = [row[0] for row in cur.fetchall()]
        
    if not valid_user_ids:
        print("No users found in the database. Cannot create orders.")
        return
            
    # If no orders exist, generate and insert new orders
    orders_data = []
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    for _ in range(num_records):
        orders_data.append((
            random.choice(valid_user_ids),  # Use a valid user_id
            fake.date_time_this_year(),
            round(random.uniform(50, 1000), 2),
            random.choice(statuses),
            fake.address()
        ))
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO orders (user_id, order_date, total_amount, status, shipping_address)
            VALUES %s
        """, orders_data)
    conn.commit()
    print(f"Added {len(orders_data)} new orders")

def populate_order_items(conn, num_records=2000):
    # Check if order_items already exist (this is also checked in main, but adding here for consistency)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM order_items")
        order_items_count = cur.fetchone()[0]
        
        if order_items_count > 0:
            print(f"Order_items table already has {order_items_count} records. Skipping.")
            return
            
    # Get valid order IDs and product IDs
    with conn.cursor() as cur:
        cur.execute("SELECT order_id FROM orders")
        valid_order_ids = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT product_id FROM products")
        valid_product_ids = [row[0] for row in cur.fetchall()]
    
    if not valid_order_ids or not valid_product_ids:
        print("No orders or products found. Cannot create order items.")
        return
            
    # If no order_items exist, generate and insert new order_items
    order_items_data = []
    for _ in range(num_records):
        order_items_data.append((
            random.choice(valid_order_ids),  # Use a valid order_id
            random.choice(valid_product_ids),  # Use a valid product_id
            random.randint(1, 5),
            round(random.uniform(10, 100), 2)
        ))
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES %s
        """, order_items_data)
    conn.commit()
    print(f"Added {len(order_items_data)} new order items")

def populate_reviews(conn, num_records=2000):
    # Check if reviews already exist (this is also checked in main, but adding here for consistency)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM reviews")
        reviews_count = cur.fetchone()[0]
        
        if reviews_count > 0:
            print(f"Reviews table already has {reviews_count} records. Skipping.")
            return
            
    # Get valid product IDs and user IDs
    with conn.cursor() as cur:
        cur.execute("SELECT product_id FROM products")
        valid_product_ids = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT user_id FROM users")
        valid_user_ids = [row[0] for row in cur.fetchall()]
    
    if not valid_product_ids or not valid_user_ids:
        print("No products or users found. Cannot create reviews.")
        return
            
    # If no reviews exist, generate and insert new reviews
    reviews_data = []
    for _ in range(num_records):
        reviews_data.append((
            random.choice(valid_product_ids),  # Use a valid product_id
            random.choice(valid_user_ids),  # Use a valid user_id
            random.randint(1, 5),
            fake.text(max_nb_chars=200)
        ))
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO reviews (product_id, user_id, rating, comment)
            VALUES %s
        """, reviews_data)
    conn.commit()
    print(f"Added {len(reviews_data)} new reviews")

def populate_product_suppliers(conn, num_records=2000):
    # Check if product_suppliers already exist (this is also checked in main, but adding here for consistency)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product_suppliers")
        product_suppliers_count = cur.fetchone()[0]
        
        if product_suppliers_count > 0:
            print(f"Product_suppliers table already has {product_suppliers_count} records. Skipping.")
            return
            
    # Get valid product IDs and supplier IDs
    with conn.cursor() as cur:
        cur.execute("SELECT product_id FROM products")
        valid_product_ids = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT supplier_id FROM suppliers")
        valid_supplier_ids = [row[0] for row in cur.fetchall()]
    
    if not valid_product_ids or not valid_supplier_ids:
        print("No products or suppliers found. Cannot create product-supplier relationships.")
        return
    
    # If no product_suppliers exist, generate and insert new product_suppliers
    # We need to ensure we don't violate the PRIMARY KEY constraint (product_id, supplier_id)
    used_pairs = set()
    product_suppliers_data = []
    
    # Try to create the specified number of records, but avoid duplicates
    attempts = 0
    max_attempts = num_records * 3  # Avoid infinite loop
    
    while len(product_suppliers_data) < num_records and attempts < max_attempts:
        attempts += 1
        product_id = random.choice(valid_product_ids)
        supplier_id = random.choice(valid_supplier_ids)
        
        # Skip if this pair already exists
        if (product_id, supplier_id) in used_pairs:
            continue
            
        used_pairs.add((product_id, supplier_id))
        product_suppliers_data.append((
            product_id,
            supplier_id,
            round(random.uniform(5, 500), 2)
        ))
    
    if product_suppliers_data:
        with conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO product_suppliers (product_id, supplier_id, supply_price)
                VALUES %s
            """, product_suppliers_data)
        conn.commit()
        print(f"Added {len(product_suppliers_data)} new product suppliers")
    else:
        print("Could not create any product-supplier relationships.")

def main():
    # First, ensure database exists and tables are created
    create_database_if_not_exists()
    
    conn = connect_db()
    try:
        print("Checking database content...")
        
        # Check each table individually and populate as needed
        populate_categories(conn)        
        populate_users(conn)        
        populate_products(conn)        
        populate_suppliers(conn)
        
        # Check orders before populating
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            order_count = cur.fetchone()[0]
            
        if order_count == 0:
            populate_orders(conn)
            print("Orders populated")
        else:
            print(f"Orders table already has {order_count} records. Skipping.")
        
        # Check order_items before populating
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM order_items")
            order_items_count = cur.fetchone()[0]
            
        if order_items_count == 0:
            populate_order_items(conn)
            print("Order items populated")
        else:
            print(f"Order_items table already has {order_items_count} records. Skipping.")
        
        # Check reviews before populating
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM reviews")
            reviews_count = cur.fetchone()[0]
            
        if reviews_count == 0:
            populate_reviews(conn)
            print("Reviews populated")
        else:
            print(f"Reviews table already has {reviews_count} records. Skipping.")
        
        # Check product_suppliers before populating
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM product_suppliers")
            product_suppliers_count = cur.fetchone()[0]
            
        if product_suppliers_count == 0:
            populate_product_suppliers(conn)
            print("Product suppliers populated")
        else:
            print(f"Product_suppliers table already has {product_suppliers_count} records. Skipping.")
        
        print("Database population completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 