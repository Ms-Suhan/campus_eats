import express from 'express';
import cors from 'cors';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import pool from './db.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const typeDefs = readFileSync(path.join(__dirname, 'schema.graphql'), 'utf8');

// Map a SQL row (snake_case) to the GraphQL Order shape (camelCase).
const toOrder = (r) => ({
  id: r.id,
  customerName: r.customer_name,
  item: r.item,
  quantity: r.quantity,
  total: Number(r.total), // DECIMAL comes back as a string from mysql2
  status: r.status,
  note: r.note,
});

const resolvers = {
  Query: {
    // SELECT every order
    orders: async () => {
      const [rows] = await pool.query('SELECT * FROM orders ORDER BY id');
      return rows.map(toOrder);
    },
    // SELECT ... WHERE id = ?  (the id argument becomes the WHERE clause)
    order: async (_, { id }) => {
      const [rows] = await pool.query('SELECT * FROM orders WHERE id = ?', [id]);
      return rows.length ? toOrder(rows[0]) : null;
    },
  },
  Mutation: {
    // INSERT a new row, then read it back so the client gets the generated id
    addOrder: async (_, { input }) => {
      const { customerName, item, quantity, total, note } = input;
      const [result] = await pool.query(
        'INSERT INTO orders (customer_name, item, quantity, total, note) VALUES (?, ?, ?, ?, ?)',
        [customerName, item, quantity, total, note ?? null]
      );
      const [rows] = await pool.query('SELECT * FROM orders WHERE id = ?', [result.insertId]);
      return toOrder(rows[0]);
    },
  },
};

const app = express();
const apollo = new ApolloServer({ typeDefs, resolvers });
await apollo.start();

app.use(cors());
app.use('/graphql', express.json(), expressMiddleware(apollo));
app.use(express.static(path.join(__dirname, 'public')));

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`GraphQL endpoint: http://localhost:${PORT}/graphql`);
  console.log(`Front-end page:   http://localhost:${PORT}/`);
});
