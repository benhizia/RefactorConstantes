#include "core.h"
#include "../../large_constants.h"
#include <iostream>

Core::Core() {
    buffer_size_ = MAX_BUFFER_SIZE;
    timeout_ = DEFAULT_TIMEOUT;
}

void Core::initialize() {
    std::cout << "Core initialization with buffer size: " << MAX_BUFFER_SIZE << std::endl;
    std::cout << "Version: " << VERSION_MAJOR << "." << VERSION_MINOR << "." << VERSION_PATCH << std::endl;
    
    if (ENABLE_CACHE) {
        std::cout << "Cache enabled" << std::endl;
    }
    
    // Use compile-time constants
    array_.resize(HASH_TABLE_SIZE);
    physics_calc_ = PHYSICS_CONSTANT * 10.0;
}

bool Core::validate_config() {
    return Config::THRESHOLD > 0.5 && Config::MAX_RETRIES > 0;
}