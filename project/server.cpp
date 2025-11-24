// g++ server.cpp -lpqxx -lpq -lpthread -o server
// grep nameserver /etc/resolv.conf
// ip route | grep default | awk '{print $3}'
#include "httplib.h"
#include <iostream>
#include <pqxx/pqxx>
#include <stdexcept>
#include <string>

#include "dbpool.h"
#include "kvcache.h"

using namespace std;

using namespace httplib;
namespace db = pqxx;

int parse_id(const string &s) {
  try {
    return stoi(s);
  } catch (...) {
    return -1;
  }
}

int main() {
  // const string conn_str =
  //     //"dbname=decs user=postgres password=kali host=Nani.mshome.net";
  //     "dbname=decs user=postgres password=kali host=172.23.32.1";
  //  Use 127.0.0.1 to force a TCP connection (which uses the password)
  string db_host;
  cout << "Enter DB Host IP (e.g., 172.23.32.1): ";
  cin >> db_host;

  // Construct the connection string dynamically
  const string conn_str =
      "dbname=decs user=postgres password=kali host=" + db_host;

  cout << "Enter pool size: " << endl;
  ;
  int pool_size;
  cin >> pool_size;
  cout << "Enter cache size: " << endl;
  ;
  int cache_size;
  cin >> cache_size;
  LibpqxxPool pool(pool_size, conn_str);
  try {
    db::connection *init_conn = pool.acquire();
    {
      db::work setup_txn{*init_conn};
      setup_txn.exec("CREATE TABLE IF NOT EXISTS kv_store ("
                     "  id INT PRIMARY KEY,"
                     "  value TEXT NOT NULL"
                     ");");
      setup_txn.commit();
    }
    cout << "Database table 'kv_store' is ready." << endl;
    pool.release(init_conn);
  } catch (const std::exception &e) {
    cerr << "Fatal error: Could not initialize database. " << e.what() << endl;
    return 1;
  }

  KVCache cache(cache_size);
  Server srv;
  cout << "Enter http_threads: ";
  int http_thread;
  cin >> http_thread;
  srv.new_task_queue = [http_thread] {
    return new httplib::ThreadPool(http_thread);
  };

  srv.Get("/", [](const Request &req, Response &res) {
    string s =
        "Your IP: " + req.remote_addr + to_string(req.remote_port) + "\n";
    res.set_content(s, "text/plain");
  });

  // GET
  srv.Get("/val", [&](const Request &req, Response &res) {
    //cout<<"GET";
    if (!req.has_param("id")) {
      res.status = 400;
      res.set_content("Error: 'id' parameter is missing.", "text/plain");
      return;
    }


    int id_int = parse_id(req.get_param_value("id"));
    if (id_int == -1) {
      res.status = 400;
      res.set_content("Invalid ID", "text/plain");
      return;
    }

    string cached_value;

    if (cache.get(id_int, cached_value)) {
      res.set_content(cached_value, "text/plain");
      return;
    }

    db::connection *conn = nullptr;
    try {
      conn = pool.acquire();
      db::work txn{*conn};
      db::result r =
          txn.exec_params("SELECT value FROM kv_store WHERE id = $1", id_int);
      txn.commit();
      pool.release(conn);

      if (r.empty()) {
        res.status = 404;
        res.set_content("No value found for id: " + to_string(id_int),
                        "text/plain");
      } else {
        string db_val = r[0][0].as<string>();
        cache.put(id_int, db_val);
        res.set_content(db_val, "text/plain");
      }
    } catch (const std::exception &e) {
      if (conn)
        pool.release(conn);
      res.status = 500;
      res.set_content(string("Database error: ") + e.what(), "text/plain");
    }
  });

  // POST
  srv.Post("/save", [&](const Request &req, Response &res) {
    if (!req.has_param("id") || !req.has_param("val")) {
      res.status = 400;
      res.set_content("Error: Missing 'id' or 'val'.", "text/plain");
      return;
    }

    //cout<<"POST";
    int id_int = parse_id(req.get_param_value("id"));
    string val = req.get_param_value("val");

    if (id_int == -1) {
      res.status = 400;
      res.set_content("Invalid ID", "text/plain");
      return;
    }

    db::connection *conn = nullptr;

    try {
      conn = pool.acquire();
      db::work txn{*conn};

      // Use the UPSERT command
      const string sql = "INSERT INTO kv_store (id, value) VALUES ($1, $2) "
                         "ON CONFLICT (id) DO UPDATE SET value = $2";

      txn.exec_params(sql, id_int, val);
      txn.commit();
      pool.release(conn);

      cache.put(id_int, val);
      res.set_content("Key saved/updated: " + to_string(id_int), "text/plain");

    } catch (const std::exception &e) {
      if (conn)
        pool.release(conn);
      res.status = 500;
      res.set_content(string("Database error: ") + e.what(), "text/plain");
    }
  });

  // DELETE
  srv.Delete("/delete", [&](const Request &req, Response &res) {
    if (!req.has_param("id")) {
      res.status = 400;
      res.set_content("Error: Missing 'id'.", "text/plain");
      return;
    }

    //cout<<"DELETE";

    int id_int = parse_id(req.get_param_value("id"));
    if (id_int == -1) {
      res.status = 400;
      res.set_content("Invalid ID", "text/plain");
      return;
    }

    db::connection *conn = nullptr;
    try {
      db::connection *conn = pool.acquire();
      db::work txn{*conn};
      db::result r =
          txn.exec_params("DELETE FROM kv_store WHERE id = $1", id_int);
      txn.commit();
      pool.release(conn);

      if (r.affected_rows() == 0) {
        res.status = 404;
        res.set_content("No entry for ID: " + to_string(id_int), "text/plain");
      } else {
        cache.erase(id_int);
        res.set_content("Deleted ID: " + to_string(id_int), "text/plain");
      }
    } catch (const std::exception &e) {
      if (conn)
        pool.release(conn);
      res.status = 500;
      res.set_content(string("Database error: ") + e.what(), "text/plain");
    }
  });

  // GET No Cache
  srv.Get("/nocache/val", [&](const Request &req, Response &res) {
    if (!req.has_param("id")) {
      res.status = 400;
      res.set_content("Error: 'id' parameter is missing.", "text/plain");
      return;
    }

    int id_int = parse_id(req.get_param_value("id"));
    if (id_int == -1) {
      res.status = 400;
      res.set_content("Invalid ID", "text/plain");
      return;
    }

    string cached_value;

    db::connection *conn = nullptr;
    try {
      db::connection *conn = pool.acquire();
      db::work txn{*conn};
      db::result r =
          txn.exec_params("SELECT value FROM kv_store WHERE id = $1", id_int);
      txn.commit();
      pool.release(conn);

      if (r.empty()) {
        res.status = 404;
        res.set_content("No value found for id: " + to_string(id_int),
                        "text/plain");
      } else {
        string db_val = r[0][0].as<string>();
        res.set_content(db_val, "text/plain");
      }
    } catch (const std::exception &e) {
      if (conn)
        pool.release(conn);
      res.status = 500;
      res.set_content(string("Database error: ") + e.what(), "text/plain");
    }
  });

  cout << "🚀 Server running on http://localhost:1234 ..." << endl;
  srv.listen("0.0.0.0", 1234);
  return 0;
}