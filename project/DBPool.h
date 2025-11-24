#ifndef DBPOOL_H
#define DBPOOL_H

#include <pqxx/pqxx>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <string>
#include <iostream> // For std::cerr
#include <stdexcept> // For std::exception

class LibpqxxPool {
private:
  std::queue<pqxx::connection *> pool;
  std::mutex mtx;
  std::condition_variable cv;
  std::string conn_string;

public:
  LibpqxxPool(int size, const std::string &connStr) : conn_string(connStr) {
    for (int i = 0; i < size; i++) {
      try {
        pool.push(new pqxx::connection(conn_string));
      } catch (const std::exception &e) {
        std::cerr << "DB connection failed in pool: " << e.what() << std::endl;
        exit(1);
      }
    }
  }

  pqxx::connection *acquire() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock, [&] { return !pool.empty(); });
    pqxx::connection *conn = pool.front();
    pool.pop();
    return conn;
  }

  void release(pqxx::connection *conn) {
    std::unique_lock<std::mutex> lock(mtx);
    pool.push(conn);
    lock.unlock();
    cv.notify_one();
  }

  ~LibpqxxPool() {
    while (!pool.empty()) {
      delete pool.front();
      pool.pop();
    }
  }
};

#endif