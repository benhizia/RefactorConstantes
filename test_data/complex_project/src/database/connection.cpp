#include "connection.h"
#include "../../large_constants.h"
#include <iostream>

DatabaseConnection::DatabaseConnection() {
    url_ = DATABASE_URL;
    timeout_ = Config::QUERY_TIMEOUT;
    pool_size_ = Config::CONNECTION_POOL_SIZE;
}

bool DatabaseConnection::connect() {
    std::cout << "Connecting to database: " << DATABASE_URL << std::endl;
    std::cout << "Connection pool size: " << Config::CONNECTION_POOL_SIZE << std::endl;
    std::cout << "Query timeout: " << Config::QUERY_TIMEOUT << std::endl;
    
    if (Config::AUTO_COMMIT) {
        std::cout << "Auto-commit enabled" << std::endl;
    }
    
    return true;
}

void DatabaseConnection::set_credentials(const std::string& user, const std::string& password) {
    if (user.empty()) {
        username_ = DEFAULT_USER;
    } else {
        username_ = user;
    }
    
    if (password.length() < Security::MIN_PASSWORD_LENGTH) {
        std::cout << ERROR_MESSAGE_PREFIX << "Password too short" << std::endl;
    }
}