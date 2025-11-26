# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 19:38
# @Author  : Yuling Hou
# @File    : test02.py.py
# @Software: PyCharm
import fs as fs

def find_coredump_files(filename):
    coredump_files = []

    # Open file in read mode with 'with' statement for safe file handling
    with open(filename, "r") as fs:
        lines = fs.readlines()

        # Iterate through each line in the file
        for index, line in enumerate(lines):
            # Check if the line contains "export core-dump"
            if "export core-dump" in line:
                # Iterate through subsequent lines until another "export core-dump" is found
                for i in range(1, len(lines) - index):
                    new_line = lines[index + i].strip()

                    # Break if another "export core-dump" is found
                    if "export core-dump" in new_line:
                        break

                    # If line contains "core.zst", add it to coredump_files list
                    if "core.zst" in new_line:
                        coredump_files.append(new_line)
                break  # Exit outer loop after processing first occurrence of "export core-dump"

    return coredump_files

# Example usage
if __name__ == "__main__":
    filename = "6700_coredump_files.txt"
    coredump_files = find_coredump_files(filename)

    number_of_coredump_files = len(coredump_files)
    print(f"Number of coredump files found: {number_of_coredump_files}")

    # Print each coredump file found
    print("Coredump files:")
    for file in coredump_files:
        print(file)
