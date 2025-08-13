# Requirements Document

## Introduction

This feature involves creating a script to analyze a large C++ constants file (2k+ lines) and automatically categorize constants based on their usage across modules in a CMake-based project. The script will identify whether constants are module-private (used only within one module) or shared (used across multiple modules), then suggest appropriate file locations for refactoring.

## Requirements

### Requirement 1

**User Story:** As a C++ developer, I want to parse my large constants file and extract all constant definitions, so that I can analyze each constant individually.

#### Acceptance Criteria

1. WHEN the script is executed THEN the system SHALL parse the constants file and extract all #define, const, and constexpr declarations
2. WHEN parsing constants THEN the system SHALL capture the constant name, value, and any associated comments
3. WHEN extraction is complete THEN the system SHALL create a structured list of all constants found
4. IF the constants file contains preprocessor conditionals THEN the system SHALL handle conditional compilation blocks appropriately

### Requirement 2

**User Story:** As a developer, I want to identify which module each constant belongs to based on usage patterns, so that I can determine the appropriate target file location.

#### Acceptance Criteria

1. WHEN analyzing constant usage THEN the system SHALL search for each constant across all source files in the project
2. WHEN searching for constant usage THEN the system SHALL exclude the original constants file from the search results
3. WHEN a constant is found in a file THEN the system SHALL determine which module/directory that file belongs to
4. WHEN usage analysis is complete THEN the system SHALL categorize each constant as either module-private or shared
5. IF a constant is used only within one module THEN the system SHALL mark it for MDL_const.h placement
6. IF a constant is used across multiple modules THEN the system SHALL mark it for MDL_export_const.h placement

### Requirement 3

**User Story:** As a developer, I want to leverage CMake build information to accurately determine module boundaries, so that I can make precise refactoring decisions.

#### Acceptance Criteria

1. WHEN analyzing the project THEN the system SHALL generate CMake compile commands database (compile_commands.json) to get accurate file-to-target mappings
2. WHEN compile commands are available THEN the system SHALL use this information to determine which target each source file belongs to
3. WHEN determining module ownership THEN the system SHALL map CMake targets to modules for precise boundary detection
4. WHEN a file belongs to multiple targets THEN the system SHALL handle the ambiguity by marking constants as shared
5. IF compile commands generation fails THEN the system SHALL parse CMakeLists.txt files as a fallback method
6. IF CMake information is unavailable THEN the system SHALL fall back to directory-based module detection

### Requirement 4

**User Story:** As a developer, I want to generate a detailed analysis report, so that I can review the proposed refactoring before making changes.

#### Acceptance Criteria

1. WHEN analysis is complete THEN the system SHALL generate a report showing each constant and its proposed destination
2. WHEN creating the report THEN the system SHALL include usage statistics for each constant (files using it, modules involved)
3. WHEN reporting results THEN the system SHALL highlight any ambiguous cases that need manual review
4. WHEN generating output THEN the system SHALL support both JSON and human-readable formats

### Requirement 5

**User Story:** As a developer, I want to create the refactored files either in a sandbox environment or directly in the original codebase, so that I can test changes safely or apply them immediately.

#### Acceptance Criteria

1. WHEN executing refactoring in sandbox mode THEN the system SHALL create a sandbox directory with the proposed file structure
2. WHEN executing refactoring in direct mode THEN the system SHALL modify files directly in the original codebase
3. WHEN generating module files THEN the system SHALL create or append to MDL_const.h files for module-private constants
4. WHEN creating shared constants THEN the system SHALL create or append to MDL_export_const.h files for cross-module constants
5. WHEN appending to existing files THEN the system SHALL avoid duplicate constant definitions
6. WHEN writing new files THEN the system SHALL maintain proper C++ header guards and formatting
7. IF the sandbox already exists THEN the system SHALL either clean it or create a new timestamped version
8. WHEN running in direct mode THEN the system SHALL provide a confirmation prompt before making changes

### Requirement 6

**User Story:** As a developer, I want to configure the analysis parameters, so that I can customize the tool for my specific project structure.

#### Acceptance Criteria

1. WHEN running the script THEN the system SHALL accept parameters for the constants file path
2. WHEN configuring analysis THEN the system SHALL allow specification of source directories to scan
3. WHEN setting up the tool THEN the system SHALL support excluding certain directories or file patterns
4. WHEN configuring execution mode THEN the system SHALL accept a flag to choose between sandbox and direct modification modes
5. IF a configuration file exists THEN the system SHALL use those settings as defaults
6. WHEN no configuration is provided THEN the system SHALL use reasonable defaults for C++ CMake projects and default to sandbox mode for safety