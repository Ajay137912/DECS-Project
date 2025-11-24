// g++ client.cpp -std=c++17 -lpthread -o client
// HTTPS ->  g++ client.cpp -lssl -lcrypto 
// HTTPS ->  #define CPPHTTPLIB_OPENSSL_SUPPORT

#include "httplib.h"
#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <random> 
#include <chrono> 

using namespace std;
using namespace httplib;

void client_worker(int tno, int mode) {
    auto seed = chrono::high_resolution_clock::now().time_since_epoch().count() + tno;
    mt19937 gen(seed);
    uniform_int_distribution<> distrib(0, 1); 

    Client cli("localhost", 1234);
    cli.set_keep_alive(true);

    for (int i = 0; i < 100; i++) {
        string id_str = to_string((tno * 100) + i);
        string val_str = "value_" + id_str;
        string path;

        httplib::Result res;

        try {
            switch (mode) {
                case 1: 
                    path = "/val?id=" + id_str;
                    res = cli.Get(path);
                    break;

                case 2: 
                    path = "/save?id=" + id_str + "&val=" + val_str;
                    res = cli.Post(path);
                    break;

                case 3: 
                    if (distrib(gen) == 0) {
                        path = "/val?id=" + id_str;
                        res = cli.Get(path);
                    } else {
                        path = "/put?id=" + id_str + "&val=" + val_str + "_updated";
                        res = cli.Put(path);
                    }
                    break;
            }

            if (!res) {
                cout << "E"; 
            } 

        } catch (const std::exception& e) {
            cout << "X"; 
        }
        
        cout.flush();
    }
}

int main() {
    int num_threads = 0;
    int mode = 0;

    cout << "Enter number of concurrent clients (threads): ";
    cin >> num_threads;

    cout << "Enter request mode:" << endl;
    cout << "  1: GET-only" << endl;
    cout << "  2: POST-only (Create)" << endl;
    cout << "  3: MIX (50/50 GET and PUT)" << endl;
    cout << "Choice: ";
    cin >> mode;

    cout << "\nStarting " << num_threads << " clients in mode " << mode << "..." << endl;

    vector<thread> threads;
    auto start_time = chrono::high_resolution_clock::now();

    // Launch all threads
    for (int i = 0; i < num_threads; i++) {
        threads.push_back(thread(client_worker, i, mode));
    }

    // Wait for all threads to finish
    for (auto& t : threads) {
        t.join();
    }

    auto end_time = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::milliseconds>(end_time - start_time);

    cout << "\n\nTest complete." << endl;
    int total_requests = num_threads * 100;
    cout << "Total requests: " << total_requests << endl;
    cout << "Total time: " << duration.count() << " ms" << endl;
    cout << "Requests per second: " << (total_requests * 1000.0 / duration.count()) << endl;

    return 0;
}