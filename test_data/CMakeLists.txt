cmake_minimum_required(VERSION 3.10)
project(ConstantsRefactorTest)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable compile commands generation
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Network module
add_library(network_module
    src/network/network_manager.cpp
    src/network/network_manager.h
)

# Config module  
add_library(config_module
    src/config/config_loader.cpp
    src/config/config_loader.h
)

# Utils module
add_library(utils_module
    src/utils/file_utils.cpp
    src/utils/file_utils.h
)

# Main executable
add_executable(test_app
    src/main.cpp
)

target_link_libraries(test_app 
    network_module 
    config_module 
    utils_module
)

# Include directories
target_include_directories(network_module PUBLIC src/network)
target_include_directories(config_module PUBLIC src/config)
target_include_directories(utils_module PUBLIC src/utils)
target_include_directories(test_app PUBLIC src)