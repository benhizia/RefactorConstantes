#!/usr/bin/env python3
"""
Simplified C++ Constants Refactoring Tool

Simple script to analyze a constants file and determine which module uses each constant.
No complex dependencies, no CMake, no CastXML - just simple file parsing.
"""

import re
import os
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Set


@dataclass
class Constant:
    """Simple constant representation."""
    name: str
    value: str
    line_number: int


class SimplifiedConstantsRefactor:
    """Simple constants refactoring analyzer."""

    def __init__(self, constants_file: str, project_root: str):
        """
        Initialize the analyzer.

        Args:
            constants_file: Path to the constants header file
            project_root: Root directory of the project (parent of all modules)
        """
        self.constants_file = Path(constants_file)
        self.project_root = Path(project_root)
        self.constants: List[Constant] = []
        self.modules: List[str] = []
        self.usage_map: Dict[str, Set[str]] = defaultdict(set)

    def extract_constants(self) -> List[Constant]:
        """
        Extract constants from the header file.
        Looks for #define, const, and constexpr declarations.
        """
        print(f"[*] Reading constants from: {self.constants_file}")

        constants = []

        with open(self.constants_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('//') or line.startswith('/*'):
                    continue

                # Match #define CONSTANT_NAME value
                define_match = re.match(r'#define\s+([A-Z_][A-Z0-9_]*)\s+(.*)', line)
                if define_match:
                    name = define_match.group(1)
                    value = define_match.group(2).strip()
                    constants.append(Constant(name, value, line_num))
                    continue

                # Match const/constexpr type CONSTANT_NAME = value
                const_match = re.match(r'(?:const|constexpr)\s+\w+\s+([A-Z_][A-Z0-9_]*)\s*=\s*(.*?);', line)
                if const_match:
                    name = const_match.group(1)
                    value = const_match.group(2).strip()
                    constants.append(Constant(name, value, line_num))
                    continue

        print(f"[OK] Found {len(constants)} constants")
        self.constants = constants
        return constants

    def find_modules(self) -> List[str]:
        """
        Find all modules in project root.
        Modules are directories with names of 3, 4, or 5 letters.
        """
        print(f"\n[+] Searching for modules in: {self.project_root}")

        modules = []

        if not self.project_root.exists():
            print(f"[X] Project root does not exist: {self.project_root}")
            return modules

        for item in self.project_root.iterdir():
            if item.is_dir():
                # Check if directory name is 3, 4, or 5 letters
                name = item.name
                if re.match(r'^[a-zA-Z]{3,5}$', name):
                    modules.append(name)
                    print(f"   [-] Found module: {name}")

        print(f"[OK] Found {len(modules)} modules: {', '.join(modules)}")
        self.modules = modules
        return modules

    def search_constant_usage(self, constant_name: str) -> Dict[str, int]:
        """
        Search for usage of a constant across all modules.

        Args:
            constant_name: Name of the constant to search

        Returns:
            Dictionary mapping module names to usage count
        """
        usage_by_module = defaultdict(int)

        # Search in each module directory
        for module in self.modules:
            module_path = self.project_root / module

            # Walk through all files in the module
            for root, dirs, files in os.walk(module_path):
                # Skip build directories
                if 'build' in root or 'cmake' in root.lower():
                    continue

                for file in files:
                    # Only check source files
                    if not (file.endswith('.cpp') or file.endswith('.h') or
                           file.endswith('.cc') or file.endswith('.hpp')):
                        continue

                    file_path = Path(root) / file

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # Count occurrences (using word boundaries to avoid partial matches)
                            matches = re.findall(r'\b' + re.escape(constant_name) + r'\b', content)
                            if matches:
                                usage_by_module[module] += len(matches)
                    except Exception as e:
                        # Skip files that can't be read
                        pass

        return dict(usage_by_module)

    def analyze_all_constants(self):
        """Analyze usage of all constants across all modules."""
        print(f"\n[>] Analyzing constant usage across modules...")

        for i, constant in enumerate(self.constants, 1):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(self.constants)} constants analyzed...")

            usage = self.search_constant_usage(constant.name)

            if usage:
                self.usage_map[constant.name] = set(usage.keys())

    def categorize_constants(self) -> Dict[str, List[str]]:
        """
        Categorize constants by usage pattern.

        Returns:
            Dictionary with categories:
            - 'unused': Not used anywhere
            - 'single_module': Used in only one module
            - 'shared': Used in multiple modules
            - Module names: Constants specific to that module
        """
        categorized = {
            'unused': [],
            'shared': [],
        }

        # Initialize category for each module
        for module in self.modules:
            categorized[module] = []

        for constant in self.constants:
            modules_using = self.usage_map.get(constant.name, set())

            if not modules_using:
                categorized['unused'].append(constant.name)
            elif len(modules_using) == 1:
                module = list(modules_using)[0]
                categorized[module].append(constant.name)
            else:
                categorized['shared'].append(constant.name)

        return categorized

    def generate_report(self):
        """Generate and print a simple report."""
        print("\n" + "="*80)
        print("*** CONSTANTS ANALYSIS REPORT")
        print("="*80)

        print(f"\n[-] Project: {self.project_root}")
        print(f"[-] Constants file: {self.constants_file}")
        print(f"[-] Total constants: {len(self.constants)}")
        print(f"[-] Modules found: {len(self.modules)}")

        categorized = self.categorize_constants()

        print("\n" + "-"*80)
        print("*** USAGE SUMMARY")
        print("-"*80)

        # Unused constants
        unused = categorized['unused']
        print(f"\n[X] Unused constants: {len(unused)}")
        if unused:
            for const in unused[:10]:  # Show first 10
                print(f"   - {const}")
            if len(unused) > 10:
                print(f"   ... and {len(unused) - 10} more")

        # Shared constants
        shared = categorized['shared']
        print(f"\n[~] Shared constants (used by multiple modules): {len(shared)}")
        if shared:
            for const in shared[:10]:
                modules = ', '.join(sorted(self.usage_map[const]))
                print(f"   - {const} → [{modules}]")
            if len(shared) > 10:
                print(f"   ... and {len(shared) - 10} more")

        # Module-specific constants
        print("\n[-] Module-specific constants:")
        for module in sorted(self.modules):
            module_constants = categorized[module]
            print(f"   {module}: {len(module_constants)} constants")
            if module_constants:
                sample = module_constants[:5]
                print(f"      Examples: {', '.join(sample)}")
                if len(module_constants) > 5:
                    print(f"      ... and {len(module_constants) - 5} more")

        print("\n" + "="*80)

        return categorized

    def generate_files(self, output_dir: str = "refactored_constants"):
        """
        Generate constants files per module and shared constants file.

        Args:
            output_dir: Directory where to generate the files
        """
        print(f"\n*** Generating constants files in: {output_dir}")

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        categorized = self.categorize_constants()

        # Get original constant objects for their values
        constants_dict = {c.name: c for c in self.constants}

        # Generate module-specific files
        for module in self.modules:
            module_constants = categorized[module]
            if not module_constants:
                continue

            module_file = output_path / f"{module}_constants.h"

            with open(module_file, 'w', encoding='utf-8') as f:
                f.write(f"// Module-specific constants for: {module}\n")
                f.write(f"// Auto-generated from {self.constants_file.name}\n")
                f.write(f"// These constants are used ONLY in the {module} module\n\n")
                f.write(f"#ifndef {module.upper()}_CONSTANTS_H\n")
                f.write(f"#define {module.upper()}_CONSTANTS_H\n\n")

                for const_name in sorted(module_constants):
                    const = constants_dict.get(const_name)
                    if const:
                        f.write(f"#define {const.name} {const.value}\n")

                f.write(f"\n#endif // {module.upper()}_CONSTANTS_H\n")

            print(f"   [+] Created: {module_file} ({len(module_constants)} constants)")

        # Generate shared constants file
        shared = categorized['shared']
        if shared:
            shared_file = output_path / "shared_constants.h"

            with open(shared_file, 'w', encoding='utf-8') as f:
                f.write(f"// Shared constants used by multiple modules\n")
                f.write(f"// Auto-generated from {self.constants_file.name}\n\n")
                f.write(f"#ifndef SHARED_CONSTANTS_H\n")
                f.write(f"#define SHARED_CONSTANTS_H\n\n")

                for const_name in sorted(shared):
                    const = constants_dict.get(const_name)
                    if const:
                        # Add comment showing which modules use it
                        modules_using = ', '.join(sorted(self.usage_map[const_name]))
                        f.write(f"// Used by: {modules_using}\n")
                        f.write(f"#define {const.name} {const.value}\n\n")

                f.write(f"#endif // SHARED_CONSTANTS_H\n")

            print(f"   [+] Created: {shared_file} ({len(shared)} constants)")

        # Generate unused constants file (for reference)
        unused = categorized['unused']
        if unused:
            unused_file = output_path / "unused_constants.h"

            with open(unused_file, 'w', encoding='utf-8') as f:
                f.write(f"// UNUSED constants (not found in any module)\n")
                f.write(f"// Auto-generated from {self.constants_file.name}\n")
                f.write(f"// Consider removing these if they're truly unused\n\n")
                f.write(f"#ifndef UNUSED_CONSTANTS_H\n")
                f.write(f"#define UNUSED_CONSTANTS_H\n\n")

                for const_name in sorted(unused):
                    const = constants_dict.get(const_name)
                    if const:
                        f.write(f"#define {const.name} {const.value}\n")

                f.write(f"\n#endif // UNUSED_CONSTANTS_H\n")

            print(f"   [+] Created: {unused_file} ({len(unused)} constants - for reference)")

        print(f"\n[OK] Generated {len(self.modules)} module files + shared/unused files")
        print(f"[OK] Output directory: {output_path.absolute()}\n")

    def run(self):
        """Run the complete analysis."""
        print("\n*** Starting Simplified Constants Refactoring Analysis\n")

        # Step 1: Extract constants
        self.extract_constants()

        # Step 2: Find modules
        self.find_modules()

        if not self.modules:
            print("\n[!] No modules found! Make sure project_root contains directories with 3-5 letter names.")
            return None

        # Step 3: Analyze usage
        self.analyze_all_constants()

        # Step 4: Generate report
        categorized = self.generate_report()

        print("\n[OK] Analysis complete!\n")

        return categorized


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Simplified C++ Constants Refactoring Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s constants.h /path/to/project
  %(prog)s src/common/constants.h .
  %(prog)s --help
        """
    )

    parser.add_argument(
        'constants_file',
        help='Path to the constants header file to analyze'
    )

    parser.add_argument(
        'project_root',
        help='Root directory of the project (parent of all modules)'
    )

    parser.add_argument(
        '--generate',
        '-g',
        action='store_true',
        help='Generate constants files per module (default: analysis only)'
    )

    parser.add_argument(
        '--output-dir',
        '-o',
        default='refactored_constants',
        help='Output directory for generated files (default: refactored_constants)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0 - Simplified Edition'
    )

    args = parser.parse_args()

    # Validate inputs
    constants_file = Path(args.constants_file)
    if not constants_file.exists():
        print(f"[X] Error: Constants file not found: {constants_file}")
        sys.exit(1)

    project_root = Path(args.project_root)
    if not project_root.exists():
        print(f"[X] Error: Project root not found: {project_root}")
        sys.exit(1)

    # Run analysis
    analyzer = SimplifiedConstantsRefactor(args.constants_file, args.project_root)
    result = analyzer.run()

    if result is None:
        sys.exit(1)

    # Generate files if requested
    if args.generate:
        analyzer.generate_files(args.output_dir)
        print(f"\n[OK] Refactoring complete! Check {args.output_dir}/ for generated files.\n")


if __name__ == '__main__':
    main()
