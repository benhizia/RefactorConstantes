#include "constants.h"
#include <iostream>

void print_version() {
    std::cout << "Version: " << VERSION_MAJOR << "." << VERSION_MINOR << std::endl;
}

int get_buffer_size() {
    return MAX_BUFFER_SIZE;
}