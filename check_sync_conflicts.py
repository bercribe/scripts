import os
import subprocess
import argparse

def find_sync_conflict_files(directory):
    # List to store files with sync conflict in their names
    sync_conflict_files = []

    # Walk through the directory and subdirectories
    for root, _, files in os.walk(directory):
        for filename in files:
            if "sync-conflict" in filename:
                # Full path of the sync conflict file
                sync_conflict_files.append(os.path.join(root, filename))
    
    return sync_conflict_files

def compare_files_with_difftastic(file1, file2, colors):
    # Run the 'difft' command with color output to compare the two files
    try:
        # Pass '--color=always' to ensure color output is maintained
        result = subprocess.run(['difft', f'--color={"always" if colors else "never"}', file1, file2], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error comparing files: {e}"

def main(directory, colors):
    # Find all sync-conflict files in the directory and subdirectories
    sync_conflict_files = find_sync_conflict_files(directory)
    print("Conflicts:")
    for file in sync_conflict_files:
        print(f"  {file}")
    print()

    # Iterate over each sync-conflict file
    for conflict_file in sync_conflict_files:
        # Extract the base name of the file (without the ".sync-conflict-<date>" part)
        base_name = conflict_file.rsplit('.sync-conflict', 1)[0]
        original_file = base_name + os.path.splitext(conflict_file)[1]

        # Check if the original file exists
        if os.path.exists(original_file):
            print(f"Comparing: {conflict_file} and {original_file}")

            # Compare the files and get the difftastic output
            diff_output = compare_files_with_difftastic(conflict_file, original_file, colors)

            if diff_output:
                print(f"Differences between {conflict_file} and {original_file}:")
                print(diff_output)
            else:
                print(f"Files are identical: {conflict_file} and {original_file}")
        else:
            print(f"Original file not found for: {conflict_file}")

    if len(sync_conflict_files) > 0:
        raise RuntimeError("sync conflicts found!")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Compare sync conflict files with original files using Difftastic.")
    parser.add_argument('directory', metavar='DIR', type=str, help="Directory to scan recursively")
    parser.add_argument('--colors', action=argparse.BooleanOptionalAction, default=True)
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided directory
    main(args.directory, args.colors)
