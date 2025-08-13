#include "config_loader.h"
#include "../../sample_constants.h"
#include <fstream>
#include <iostream>

ConfigLoader::ConfigLoader() {
    config_file_ = DEFAULT_CONFIG_FILE;
    max_retries_ = Config::MAX_RETRIES;
    threshold_ = Config::THRESHOLD;
}

bool ConfigLoader::load_config() {
    std::cout << "Loading configuration from: " << DEFAULT_CONFIG_FILE << std::endl;
    
    std::ifstream file(config_file_);
    if (!file.is_open()) {
        std::cout << ERROR_MESSAGE_PREFIX << "Cannot open config file" << std::endl;
        return false;
    }
    
    // Use various constants during parsing
    char delimiter = DELIMITER;
    std::string section = Config::CONFIG_SECTION;
    
    std::cout << "Using delimiter: '" << delimiter << "'" << std::endl;
    std::cout << "Reading section: " << section << std::endl;
    
    return true;
}

void ConfigLoader::set_debug_level() {
    if (DEBUG_LEVEL > 0) {
        std::cout << "Debug level set to: " << DEBUG_LEVEL << std::endl;
        
        if (ENABLE_LOGGING) {
            std::cout << "Logging enabled" << std::endl;
            log_file_prefix_ = LOG_FILE_PREFIX;
        }
    }
}

double ConfigLoader::get_conversion_factor() const {
    return CONVERSION_FACTOR;
}

bool ConfigLoader::is_cache_enabled() const {
    return ENABLE_CACHE;
}

std::string ConfigLoader::get_database_url() const {
    return DATABASE_URL;
}

std::string ConfigLoader::get_api_endpoint() const {
    return API_ENDPOINT;
}

void ConfigLoader::validate_performance() {
    if (threshold_ < PERFORMANCE_THRESHOLD) {
        std::cout << WARNING_MESSAGE_PREFIX << "Performance threshold too low" << std::endl;
    }
    
    std::cout << "Compile time constant: " << COMPILE_TIME_CONSTANT << std::endl;
    std::cout << "Physics constant: " << PHYSICS_CONSTANT << std::endl;
}