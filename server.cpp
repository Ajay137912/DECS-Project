#include "httplib.h"
#include <iostream>
#include <unordered_map>
#include <mutex>
#include <string>
#include <libpq-fe.h>
#include <queue>
#include <condition_variable>

using namespace std;
using namespace httplib;

#define CACHE_CAPACITY 10
#define THREAD_POOL_SIZE 32

class PostgresConnectionPool {
private:
    vector<PGconn*> connectionPool;
    mutex poolMutex;
    condition_variable poolCondition;
    int poolSize;

public:
    PostgresConnectionPool(int size) : poolSize(size) {
        for (int i = 0; i < size; i++) {
            PGconn *conn = PQconnectdb("host=localhost port=5432 dbname=kvstore user=postgres");
            if (PQstatus(conn) != CONNECTION_OK) {
                cerr << "Database connection failed: " << PQerrorMessage(conn) << endl;
                exit(1);
            }
            connectionPool.push_back(conn);
        }
        cout << "PostgreSQL connection pool initialized with " << size << " connections.\n";
    }

    PGconn* acquireConnection() {
        unique_lock<mutex> lock(poolMutex);
        poolCondition.wait(lock, [&]{ return !connectionPool.empty(); });
        PGconn *conn = connectionPool.back();
        connectionPool.pop_back();
        return conn;
    }

    void releaseConnection(PGconn* conn) {
        unique_lock<mutex> lock(poolMutex);
        connectionPool.push_back(conn);
        lock.unlock();
        poolCondition.notify_one();
    }

    ~PostgresConnectionPool() {
        for (auto &conn : connectionPool)
            PQfinish(conn);
    }
};

PostgresConnectionPool postgresPool(THREAD_POOL_SIZE);
PGconn *mainDBConnection = nullptr;

void initializeDatabaseConnection() {
    mainDBConnection = PQconnectdb("host=localhost port=5432 dbname=kvstore user=postgres");
    if (PQstatus(mainDBConnection) != CONNECTION_OK) {
        cerr << "Database connection failed: " << PQerrorMessage(mainDBConnection) << endl;
        exit(1);
    }
    cout << "Connected to PostgreSQL database.\n";
}

void insertOrUpdateKeyValue(int key, const string &value) {
    PGconn* conn = postgresPool.acquireConnection();
    string query = "INSERT INTO kv_store (k, v) VALUES (" + to_string(key) + ", '" + value +
                   "') ON CONFLICT (k) DO UPDATE SET v='" + value + "';";
    PGresult *result = PQexec(conn, query.c_str());
    PQclear(result);
    postgresPool.releaseConnection(conn);
}

string fetchValueFromDatabase(int key) {
    PGconn* conn = postgresPool.acquireConnection();
    string query = "SELECT v FROM kv_store WHERE k=" + to_string(key);
    PGresult *result = PQexec(conn, query.c_str());
    string value = "";
    if (PQresultStatus(result) == PGRES_TUPLES_OK && PQntuples(result) > 0)
        value = PQgetvalue(result, 0, 0);
    PQclear(result);
    postgresPool.releaseConnection(conn);
    return value;
}

bool deleteKeyFromDatabase(int key) {
    PGconn* conn = postgresPool.acquireConnection();
    string query = "DELETE FROM kv_store WHERE k=" + to_string(key);
    PGresult *result = PQexec(conn, query.c_str());
    bool deleted = (string(PQcmdTuples(result)) != "0");
    PQclear(result);
    postgresPool.releaseConnection(conn);
    return deleted;
}

class InMemoryFIFOCache {
private:
    int maxCapacity;
    unordered_map<int, string> keyValueStore;
    queue<int> insertionOrder;
    mutex cacheMutex;

public:
    InMemoryFIFOCache(int capacity) : maxCapacity(capacity) {}

    void put(int key, const string &value) {
        lock_guard<mutex> lock(cacheMutex);
        if (keyValueStore.count(key)) {
            keyValueStore[key] = value;
            return;
        }
        if (keyValueStore.size() == maxCapacity) {
            int oldestKey = insertionOrder.front();
            insertionOrder.pop();
            keyValueStore.erase(oldestKey);
            cout << "Evicted (FIFO) key: " << oldestKey << endl;
        }
        keyValueStore[key] = value;
        insertionOrder.push(key);
    }

    string get(int key) {
        lock_guard<mutex> lock(cacheMutex);
        if (!keyValueStore.count(key)) return "";
        cout << "Fetched from cache (FIFO)\n";
        return keyValueStore[key];
    }

    bool remove(int key) {
        lock_guard<mutex> lock(cacheMutex);
        if (!keyValueStore.count(key)) return false;
        keyValueStore.erase(key);
        queue<int> updatedQueue;
        while (!insertionOrder.empty()) {
            int currentKey = insertionOrder.front();
            insertionOrder.pop();
            if (currentKey != key) updatedQueue.push(currentKey);
        }
        swap(insertionOrder, updatedQueue);
        return true;
    }
};

int main() {
    initializeDatabaseConnection();
    InMemoryFIFOCache inMemoryCache(CACHE_CAPACITY);
    Server kvServer;

    kvServer.Post("/set", [&](const Request &req, Response &res) {
        if (!req.has_param("id")) {
            res.status = 400;
            res.set_content("Error: Missing 'id' parameter.\n", "text/plain");
            return;
        }
        int key = stoi(req.get_param_value("id"));
        string value = req.body;
        cout<< "hello" << key << value << "\n";
        inMemoryCache.put(key, value);
        insertOrUpdateKeyValue(key, value);
        res.set_content("Key-value stored successfully.\n", "text/plain");
    });

    kvServer.Get("/get", [&](const Request &req, Response &res) {
        if (!req.has_param("id")) {
            res.status = 400;
            res.set_content("Error: Missing 'id' parameter.\n", "text/plain");
            return;
        }
        int key = stoi(req.get_param_value("id"));
        string value = inMemoryCache.get(key);
        if (value.empty()) {
            value = fetchValueFromDatabase(key);
            if (value.empty()) {
                res.status = 404;
                res.set_content("Error: Key not found.\n", "text/plain");
                return;
            }
            inMemoryCache.put(key, value);
        }
        res.set_content(value + "\n", "text/plain");
    });

    kvServer.Delete("/delete", [&](const Request &req, Response &res) {
        if (!req.has_param("id")) {
            res.status = 400;
            res.set_content("Error: Missing 'id' parameter.\n", "text/plain");
            return;
        }
        int key = stoi(req.get_param_value("id"));
        bool cacheRemoved = inMemoryCache.remove(key);
        bool dbRemoved = deleteKeyFromDatabase(key);
        if (cacheRemoved || dbRemoved)
            res.set_content("Key deleted successfully.\n", "text/plain");
        else {
            res.status = 404;
            res.set_content("Error: Key not found.\n", "text/plain");
        }
    });

    kvServer.new_task_queue = [] {
        return new httplib::ThreadPool(THREAD_POOL_SIZE);
    };

    cout << "\nKey-Value Store Server (FIFO Policy) running at http://127.0.0.1:8080\n";
    kvServer.listen("0.0.0.0", 8080);
}