cmake_minimum_required(VERSION 3.10)
project(SimpleConstantsTest)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Simple single-target project
add_executable(simple_app
    main.cpp
    utils.cpp
)

target_include_directories(simple_app PRIVATE .)