import mysql from 'mysql2/promise';

// Connection pool. Override with environment variables if your MySQL differs.
const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'campuseats',
  waitForConnections: true,
  connectionLimit: 10,
});

export default pool;
