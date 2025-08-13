#ifndef NETWORK_MANAGER_H
#define NETWORK_MANAGER_H

#include <string>
#include <vector>

class NetworkManager {
public:
    NetworkManager();
    bool initialize();
    int connect(const std::string& host);
    void set_buffer_size(int size);

private:
    bool attempt_connection(const std::string& host);
    
    int port_;
    int max_connections_;
    int timeout_;
    int retry_count_;
    int buffer_size_;
    std::vector<int> connection_pool_;
};

#endif // NETWORK_MANAGER_H