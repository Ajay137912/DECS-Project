#include "httplib.h"
#include <iostream>
#include <string>

using namespace std;
using namespace httplib;

void showMenu() {
    cout << "\n========== Key-Value Store Client ==========\n";
    cout << "1. Set Key-Value\n";
    cout << "2. Get Value by Key\n";
    cout << "3. Delete Key\n";
    cout << "4. Exit\n";
    cout << "============================================\n";
    cout << "Enter your choice: ";
}

int main() {
    Client client("http://127.0.0.1:8080");
    int choice;

    while (true) {
        showMenu();
        cin >> choice;

        if (choice == 1) {
            int key;
            string value;
            cout << "Enter key: ";
            cin >> key;
            cin.ignore();
            cout << "Enter value: ";
            getline(cin, value);

            auto res = client.Post(("/set?id=" + to_string(key)).c_str(), value, "text/plain");
            if (res && res->status == 200)
                cout << "Server: " << res->body;
            else {
                cout << "Failed to store key-value.\n";
                cout << res << "\n";
            }
        }

        else if (choice == 2) {
            int key;
            cout << "Enter key: ";
            cin >> key;

            auto res = client.Get(("/get?id=" + to_string(key)).c_str());
            if (res && res->status == 200)
                cout << "Value: " << res->body;
            else if (res && res->status == 404)
                cout << "Key not found.\n";
            else
                cout << "Request failed.\n";
        }

        else if (choice == 3) {
            int key;
            cout << "Enter key: ";
            cin >> key;

            auto res = client.Delete(("/delete?id=" + to_string(key)).c_str());
            if (res && res->status == 200)
                cout << res->body;
            else if (res && res->status == 404)
                cout << "Key not found.\n";
            else
                cout << "Deletion failed.\n";
        }

        else if (choice == 4) {
            cout << "Exiting client.\n";
            break;
        }

        else {
            cout << "Invalid choice. Try again.\n";
        }
    }

    return 0;
}