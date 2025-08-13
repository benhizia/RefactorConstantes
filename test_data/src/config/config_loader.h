#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H

#include <string>

class ConfigLoader {
public:
    ConfigLoader();
    bool load_config();
    void set_debug_level();
    double get_conversion_factor() const;
    bool is_cache_enabled() const;
    std::string get_database_url() const;
    std::string get_api_endpoint() const;
    void validate_performance();

private:
    std::string config_file_;
    std::string log_file_prefix_;
    int max_retries_;
    double threshold_;
};

#endif // CONFIG_LOADER_H