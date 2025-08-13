#include "network_manager.h"
#include "../../sample_constants.h"
#include <iostream>
#include <thread>
#include <chrono>

NetworkManager::NetworkManager() {
    port_ = DEFAULT_PORT;
    max_connections_ = MAX_CONNECTIONS;
    timeout_ = SOCKET_TIMEOUT;
    retry_count_ = RETRY_COUNT;
}

bool NetworkManager::initialize() {
    std::cout << "Initializing network manager on port " << DEFAULT_PORT << std::endl;
    
    if (port_ < 1024) {
        std::cout << ERROR_MESSAGE_PREFIX << "Invalid port number" << std::endl;
        return false;
    }
    
    connection_pool_.reserve(MAX_CONNECTIONS);
    return true;
}

int NetworkManager::connect(const std::string& host) {
    for (int i = 0; i < RETRY_COUNT; ++i) {
        if (attempt_connection(host)) {
            return Network::HTTP_OK;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(SOCKET_TIMEOUT));
        std::cout << WARNING_MESSAGE_PREFIX << "Retry " << (i + 1) << " of " << RETRY_COUNT << std::endl;
    }
    
    return Network::HTTP_SERVER_ERROR;
}

bool NetworkManager::attempt_connection(const std::string& host) {
    // Simulate connection attempt
    std::cout << "Connecting to " << host << " with user agent: " << Network::USER_AGENT << std::endl;
    
    // Use timeout value
    std::this_thread::sleep_for(std::chrono::milliseconds(SOCKET_TIMEOUT / 10));
    
    return true; // Simulate successful connection
}

void NetworkManager::set_buffer_size(int size) {
    if (size < MIN_BUFFER_SIZE) {
        buffer_size_ = MIN_BUFFER_SIZE;
    } else if (size > MAX_BUFFER_SIZE) {
        buffer_size_ = MAX_BUFFER_SIZE;
    } else {
        buffer_size_ = size;
    }
}