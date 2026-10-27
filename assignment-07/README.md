# CampusEats Orders: GraphQL (CS543 Assignment 7)

**Team:** 
_< M S Suhan - 20252651036>_, 
_< Gaurav Vyas - 20252651020>_,
_< Shubham- 20252651054>_,
_< Manish - 20252651033>_,
_< Kunal Roy - 2025265103>_,

**Run it:** start MySQL, run `mysql -u root -p < schema.sql`, then `npm install && npm start` and open http://localhost:4000 (set `DB_USER` / `DB_PASSWORD` / `DB_NAME` if your MySQL differs).

## Answers

**1. Which CampusEats service did you pick?**
The **Orders** service (the same one the earlier assignments extend). It is modelled as one `Order` type (id, customerName, item, quantity, total, status, note) over a MySQL `orders` table.

**2. Name one field a client can skip and one it cannot (why we use the `!` sign).**
- Can skip: `note`. It is declared `String` with no `!`, so it is nullable and a client may leave it out of `addOrder` (it is stored as `NULL`).
- Cannot skip: `customerName`. It is declared `String!`, so GraphQL rejects any `addOrder` call without it before a resolver runs. The `!` makes the contract explicit: the server guarantees this field is never null, and the client must send it on input.

**3. Map it to SQL: which part of your query became the WHERE, and which resolver ran the INSERT?**
- The `id` argument of `order(id: ID!)` becomes the WHERE clause. The `Query.order` resolver runs `SELECT * FROM orders WHERE id = ?`. The list query `orders` has no argument, so it has no WHERE.
- The `Mutation.addOrder` resolver runs `INSERT INTO orders (customer_name, item, quantity, total, note) VALUES (?, ?, ?, ?, ?)`, then reads the new row back with `WHERE id = insertId` so the client gets the generated id.

## Example operations

```graphql
query { orders { id customerName item total status } }

query { order(id: 2) { id customerName item note } }

mutation {
  addOrder(input: { customerName: "Kabir Joshi", item: "Samosa", quantity: 2, total: 40 }) {
    id customerName item total
  }
}
```

## Files

`schema.graphql` · `schema.sql` · `db.js` · `server.js` · `public/index.html` · `package.json`


