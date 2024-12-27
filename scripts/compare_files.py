import os
import filecmp
from difflib import unified_diff
from pathlib import Path
import sys

def compare_directories(dir1, dir2):
    """Compare all corresponding files between two directories."""
    dir1_path = Path(dir1)
    dir2_path = Path(dir2)
    
    if not dir1_path.exists() or not dir2_path.exists():
        print("One or both directories do not exist!")
        return

    # Get all files in both directories
    files1 = set(f.relative_to(dir1_path) for f in dir1_path.rglob('*') if f.is_file())
    files2 = set(f.relative_to(dir2_path) for f in dir2_path.rglob('*') if f.is_file())

    # Find common files
    common_files = files1.intersection(files2)
    
    # Print files that exist in one directory but not in the other
    only_in_dir1 = files1 - files2
    only_in_dir2 = files2 - files1
    
    if only_in_dir1:
        print(f"\nFiles only in {dir1}:")
        for file in sorted(only_in_dir1):
            print(f"  {file}")
    
    if only_in_dir2:
        print(f"\nFiles only in {dir2}:")
        for file in sorted(only_in_dir2):
            print(f"  {file}")

    # Compare common files
    print("\nDifferences in common files:")
    print("=" * 80)
    
    for file in sorted(common_files):
        file1_path = dir1_path / file
        file2_path = dir2_path / file
        
        if not filecmp.cmp(file1_path, file2_path, shallow=False):
            print(f"\nDiff for: {file}")
            print("-" * 40)
            
            with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
                diff = unified_diff(
                    f1.readlines(),
                    f2.readlines(),
                    fromfile=str(file1_path),
                    tofile=str(file2_path)
                )
                print(''.join(diff), end='')

if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print("Usage: python compare_files.py <directory1> <directory2>")
        sys.exit(1)
    
    compare_directories(sys.argv[1], sys.argv[2])