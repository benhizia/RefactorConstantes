#ifndef CONNECTION_H
#define CONNECTION_H

#include <string>

class DatabaseConnection {
public:
    DatabaseConnection();
    bool connect();
    void set_credentials(const std::string& user, const std::string& password);

private:
    std::string url_;
    std::string username_;
    int timeout_;
    int pool_size_;
};

#endif // CONNECTION_H