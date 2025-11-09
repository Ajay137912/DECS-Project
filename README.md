#  Key-Value Store Server (FIFO Policy)

A lightweight **HTTP-based Key-Value Store** implemented in **C++**, featuring an **in-memory FIFO cache** with a **PostgreSQL backend** for persistent storage.  
The server efficiently handles concurrent requests using **thread pooling** and a **PostgreSQL connection pool**.

---

##  Features
-  In-memory **FIFO cache** for fast key-value retrieval.  
-  Persistent storage using **PostgreSQL** (`kv_store` table).  
-  **Multi-threaded** request handling via `httplib` thread pool.  
-  **Database connection pooling** for optimal performance.  
-  RESTful **HTTP API** with `GET`, `POST`, and `DELETE` endpoints.  

---

##  Requirements
- **C++17** or later  
- **PostgreSQL** installed and running locally  
- Libraries:
  - [`cpp-httplib`](https://github.com/yhirose/cpp-httplib)
  - `libpq` (PostgreSQL C client library)
  - `pthread` (for multithreading support)

---

## Database Setup
Run the following SQL commands in your PostgreSQL shell:

```sql
CREATE DATABASE kvstore;
\c kvstore
CREATE TABLE kv_store (
    k INT PRIMARY KEY,
    v TEXT
);
