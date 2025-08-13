#include "../sample_constants.h"
#include "network/network_manager.h"
#include "config/config_loader.h"
#include "utils/file_utils.h"
#include <iostream>

int main() {
    std::cout << "Constants Refactor Test Application" << std::endl;
    std::cout << "Version: " << VERSION_MAJOR << "." << VERSION_MINOR << "." << VERSION_PATCH << std::endl;
    
    // Test network module
    NetworkManager network;
    if (network.initialize()) {
        network.connect("localhost");
    }
    
    // Test config module
    ConfigLoader config;
    config.load_config();
    config.set_debug_level();
    
    // Test utils module
    FileUtils utils;
    utils.validate_path("/some/test/path");
    utils.check_disk_space();
    utils.log_version_info();
    
    // Use some constants directly in main
    std::cout << "Array size: " << ARRAY_SIZE << std::endl;
    std::cout << "Hash table size: " << HASH_TABLE_SIZE << std::endl;
    std::cout << "Default timeout: " << DEFAULT_TIMEOUT << std::endl;
    
    // Use math constants
    double circle_area = CIRCLE_AREA(5.0);
    std::cout << "Circle area (r=5): " << circle_area << std::endl;
    
    // Use color constants
    std::cout << "Red color: 0x" << std::hex << COLOR_RED << std::dec << std::endl;
    
    return STATUS_OK;
}