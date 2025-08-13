#include "file_utils.h"
#include "../../sample_constants.h"
#include <iostream>
#include <filesystem>

FileUtils::FileUtils() {
    temp_dir_prefix_ = TEMP_DIR_PREFIX;
}

bool FileUtils::validate_path(const std::string& path) {
    if (path.length() > MAX_PATH_LENGTH) {
        std::cout << ERROR_MESSAGE_PREFIX << "Path too long" << std::endl;
        return false;
    }
    
    // Extract filename and check length
    std::filesystem::path p(path);
    std::string filename = p.filename().string();
    
    if (filename.length() > MAX_FILENAME_LENGTH) {
        std::cout << ERROR_MESSAGE_PREFIX << "Filename too long" << std::endl;
        return false;
    }
    
    return true;
}

std::string FileUtils::get_path_separator() {
    return std::string(1, PATH_SEPARATOR);
}

std::string FileUtils::get_line_ending() {
    return LINE_ENDING;
}

size_t FileUtils::calculate_buffer_size(size_t file_size) {
    if (file_size < KB) {
        return MIN_BUFFER_SIZE;
    } else if (file_size < MB) {
        return KB;
    } else if (file_size < GB) {
        return MB;
    } else {
        return MAX_BUFFER_SIZE;
    }
}

void FileUtils::create_temp_directory() {
    std::string temp_name = TEMP_DIR_PREFIX + "12345";
    std::cout << "Creating temporary directory: " << temp_name << std::endl;
}

bool FileUtils::check_disk_space() {
    // Use size constants for disk space checking
    size_t required_space = 100 * MB;  // 100 MB required
    size_t available_space = 5 * GB;   // Simulate 5 GB available
    
    if (available_space < required_space) {
        std::cout << ERROR_MESSAGE_PREFIX << "Insufficient disk space" << std::endl;
        return false;
    }
    
    return true;
}

void FileUtils::log_version_info() {
    std::cout << "Version: " << VERSION_MAJOR << "." << VERSION_MINOR << "." << VERSION_PATCH << std::endl;
    std::cout << "Build: " << BUILD_NUMBER << std::endl;
    std::cout << "Version string: " << VERSION_STRING << std::endl;
}