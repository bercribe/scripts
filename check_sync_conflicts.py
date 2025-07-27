import os
import subprocess
import argparse
from collections import defaultdict

def find_sync_conflict_files(directory):
    sync_conflict_files = []

    for root, _, files in os.walk(directory):
        for filename in files:
            if "sync-conflict" in filename:
                sync_conflict_files.append(os.path.join(root, filename))
    
    return sync_conflict_files

def compare_files_with_difftastic(file1, file2, colors):
    try:
        result = subprocess.run(['difft', f'--color={"always" if colors else "never"}', '--exit-code', file1, file2], capture_output=True, text=True)
        if result.returncode > 0:
            return result.stdout
        else:
            return ""
    except Exception as e:
        return f"Error comparing files: {e}"

def main(directory, colors):
    sync_conflict_files = list(filter(lambda conflict: "/.stversions/" not in conflict, find_sync_conflict_files(directory)))
    if len(sync_conflict_files) > 0:
        print("Conflicts:")
        for file in sync_conflict_files:
            print(f"  {file}")
        print()

    conflict_map = defaultdict(list)
    for conflict_file in sync_conflict_files:
        # Extract the base name of the file (without the ".sync-conflict-<date>" part)
        base_name = conflict_file.rsplit('.sync-conflict', 1)[0]
        original_file = base_name + os.path.splitext(conflict_file)[1]
        print(f"Comparing: {conflict_file} and {original_file}")

        match = False
        for conflict in conflict_map[original_file]:
            diff = compare_files_with_difftastic(conflict_file, conflict, colors)
            if not diff:
                print(f"Identical to {conflict}\n")
                match = True
                break

        conflict_map[original_file].append(conflict_file)
        if match:
            continue

        if os.path.exists(original_file):
            diff_output = compare_files_with_difftastic(conflict_file, original_file, colors)

            if diff_output:
                print(diff_output)
            else:
                print(f"No changes.\n")
        else:
            print(f"Original file not found\n")

    if len(sync_conflict_files) > 0:
        raise RuntimeError("sync conflicts found!")
    else:
        print("No conflicts!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare sync conflict files with original files using Difftastic.")
    parser.add_argument('directory', metavar='DIR', type=str, help="Directory to scan recursively")
    parser.add_argument('--colors', action=argparse.BooleanOptionalAction, default=True)
    
    args = parser.parse_args()

    main(args.directory, args.colors)
