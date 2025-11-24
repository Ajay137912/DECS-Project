server.cpp
client.cpp

g++ server.cpp -lpqxx -lpq -lpthread -o server
g++ client.cpp -o client -lpqxx -lpq -lssl -lcrypto



wrk -t400 -c400 -d10s "http://127.0.0.1:1234/val?id=1"
