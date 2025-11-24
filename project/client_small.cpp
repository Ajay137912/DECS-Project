// g++ client.cpp -std=c++17 -lpthread -o client
// HTTPS ->  g++ client.cpp -lssl -lcrypto
// HTTPS ->  #define CPPHTTPLIB_OPENSSL_SUPPORT

#include "httplib.h"
#include <iostream>
#include <string>
#include <thread>
#include <vector>

using namespace std;
using namespace httplib;

void delete_all(int tno) {
  Client cli("localhost", 1234);
  cli.set_keep_alive(true);

  for (int i = tno * 100; i < (tno + 1) * 100; i++) {

    httplib::Result res;
    string path;
    path = "/delete?id=" + to_string(i);
    try {
      res = cli.Delete(path);
      if (!res) {
        cout << "E";
      }

    } catch (const std::exception &e) {
      cout << "X";
    }

    cout.flush();
  }
}

void fill_all(int tno) {

  Client cli("localhost", 1234);
  cli.set_keep_alive(true);

  for (int i = tno * 100; i < (tno + 1) * 100; i++) {

    httplib::Result res;
    string path;
    path = "/save?id=" + to_string(i) + "&val=" + to_string(i);
    try {
      res = cli.Post(path);
      if (!res) {
        cout << "E";
      }else{
        cout<<res->body<<endl;
      }

    } catch (const std::exception &e) {
      cout << "X";
    }

    cout.flush();
  }
}

void get_all(int tno) {
  Client cli("localhost", 1234);
  cli.set_keep_alive(true);

  for (int i = tno * 100; i < (tno + 1) * 100; i++) {

    httplib::Result res;
    string path;
    path = "/val?id=" + to_string(i);
    try {
      res = cli.Get(path);
      if (!res) {
        cout << "E";
      }else{
        cout<<res->body<<endl;
      }

    } catch (const std::exception &e) {
      cout << "X";
    }

    cout.flush();
  }
}
void get(int key) {
  Client cli("localhost", 1234);
  cli.set_keep_alive(true);

  httplib::Result res;
  string path;
  path = "/val?id=" + to_string(key);
  try {
    res = cli.Get(path);
    if (!res) {
      cout << "E";
    }else{
      cout << res->body<<endl;
    }

  } catch (const std::exception &e) {
    cout << "X";
  }
}
void save(int key,string val) {
  Client cli("localhost", 1234);
  cli.set_keep_alive(true);

  httplib::Result res;
  string path;
  path = "/save?id=" + to_string(key) + "&val=" + val;
  try {
    res = cli.Post(path);
    if (!res) {
      cout << "E";
    }else{
      cout << res->body<<endl;
    }

  } catch (const std::exception &e) {
    cout << "X";
  }
}
void del(int key) {
  Client cli("localhost", 1234);
  cli.set_keep_alive(true);

  httplib::Result res;
  string path;
  path = "/delete?id=" + to_string(key);
  try {
    res = cli.Delete(path);
    if (!res) {
      cout << "E";
    }else{
      cout << res->body<<endl;
    }

  } catch (const std::exception &e) {
    cout << "X";
  }
}
int main() {
  int num_threads = 0;
  int mode = 0;

  cout << "Enter type of request:" << endl;
  cout << "  1: GET" << endl;
  cout << "  2: POST" << endl;
  cout << "  3: DELETE" << endl;
  cout << "  4: CLEAR DATABASE" << endl;
  cout << "  5: GET DATABASE" << endl;
  cout << "  6: FILL DATABASE" << endl;
  cout << "Choice: ";
  cin >> mode;

  if(mode==1){
    cout<<"Enter key: ";
    int key;cin>>key;
    get(key);
  }

  if(mode==3){
    cout<<"Enter key: ";
    int key;cin>>key;
    del(key);
  }

  if(mode==2){
    cout<<"Enter key: ";
    int key;cin>>key;
    cout<<"Enter value: ";
    string val;
    cin>>val;
    save(key,val);
  }

  if (mode == 4) {
    vector<thread> threads;
    auto start_time = chrono::high_resolution_clock::now();

    for (int i = 0; i < 10; i++) {
      threads.push_back(thread(delete_all, i ));
    }

    for (auto &t : threads) {
      t.join();
    }
  }
  if (mode == 5) {
    vector<thread> threads;
    auto start_time = chrono::high_resolution_clock::now();

    for (int i = 0; i < 10; i++) {
      threads.push_back(thread(get_all, i ));
    }

    // Wait for all threads to finish
    for (auto &t : threads) {
      t.join();
    }
  }
  if (mode == 6) {
    vector<thread> threads;
    auto start_time = chrono::high_resolution_clock::now();

    for (int i = 0; i < 30; i++) {
      threads.push_back(thread(fill_all, i ));
    }

    for (auto &t : threads) {
      t.join();
    }
  }

  return 0;
}