#ifndef CORE_H
#define CORE_H

#include <vector>

class Core {
public:
    Core();
    void initialize();
    bool validate_config();

private:
    int buffer_size_;
    int timeout_;
    std::vector<int> array_;
    double physics_calc_;
};

#endif // CORE_H