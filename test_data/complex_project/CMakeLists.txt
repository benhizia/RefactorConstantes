cmake_minimum_required(VERSION 3.10)
project(ComplexConstantsTest)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable compile commands generation
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Create multiple libraries with overlapping dependencies

# Core library - used by everyone
add_library(core_lib
    src/core/core.cpp
    src/core/core.h
)

# Network library - depends on core
add_library(network_lib
    src/network/client.cpp
    src/network/client.h
    src/network/server.cpp
    src/network/server.h
)

# Database library - depends on core
add_library(database_lib
    src/database/connection.cpp
    src/database/connection.h
    src/database/query.cpp
    src/database/query.h
)

# UI library - depends on core and network
add_library(ui_lib
    src/ui/window.cpp
    src/ui/window.h
    src/ui/dialog.cpp
    src/ui/dialog.h
)

# Utils library - standalone
add_library(utils_lib
    src/utils/string_utils.cpp
    src/utils/string_utils.h
    src/utils/math_utils.cpp
    src/utils/math_utils.h
)

# Main application - depends on all libraries
add_executable(complex_app
    src/main.cpp
)

# Set up dependencies
target_link_libraries(network_lib core_lib)
target_link_libraries(database_lib core_lib)
target_link_libraries(ui_lib core_lib network_lib)
target_link_libraries(complex_app 
    core_lib 
    network_lib 
    database_lib 
    ui_lib 
    utils_lib
)

# Include directories
target_include_directories(core_lib PUBLIC src/core)
target_include_directories(network_lib PUBLIC src/network)
target_include_directories(database_lib PUBLIC src/database)
target_include_directories(ui_lib PUBLIC src/ui)
target_include_directories(utils_lib PUBLIC src/utils)
target_include_directories(complex_app PUBLIC src)

# Add subdirectories for additional modules
add_subdirectory(modules/plugin_system)
add_subdirectory(modules/logging)