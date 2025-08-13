add_library(logging_system
    logger.cpp
    logger.h
    log_formatter.cpp
    log_formatter.h
)

target_include_directories(logging_system PUBLIC .)
target_link_libraries(logging_system core_lib utils_lib)