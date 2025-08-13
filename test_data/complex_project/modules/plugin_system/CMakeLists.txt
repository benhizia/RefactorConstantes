add_library(plugin_system
    plugin_manager.cpp
    plugin_manager.h
    plugin_interface.h
)

target_include_directories(plugin_system PUBLIC .)
target_link_libraries(plugin_system core_lib)