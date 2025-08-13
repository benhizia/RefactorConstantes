#ifndef CLIENT_H
#define CLIENT_H

#include <string>
#include <vector>

class NetworkClient {
public:
    NetworkClient();
    bool connect(const std::string& host);
    int get_status_code();

private:
    bool attempt_connection();
    
    int port_;
    int max_connections_;
    int retry_count_;
    std::vector<char> buffer_;
};

#endif // CLIENT_H