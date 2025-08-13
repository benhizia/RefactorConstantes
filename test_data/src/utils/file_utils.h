#ifndef FILE_UTILS_H
#define FILE_UTILS_H

#include <string>

class FileUtils {
public:
    FileUtils();
    bool validate_path(const std::string& path);
    std::string get_path_separator();
    std::string get_line_ending();
    size_t calculate_buffer_size(size_t file_size);
    void create_temp_directory();
    bool check_disk_space();
    void log_version_info();

private:
    std::string temp_dir_prefix_;
};

#endif // FILE_UTILS_H