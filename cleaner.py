def remove_comments(input_file, output_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    cleaned_lines = []
    in_multiline_comment = False

    for line in lines:
        stripped_line = line.strip()

        # Handle multi-line comments (""" or ''')
        if not in_multiline_comment:
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                in_multiline_comment = True
                continue
            elif stripped_line.startswith('#'):
                continue
            else:
                # Keep only the code part before a single-line comment
                if '#' in stripped_line:
                    code_part = stripped_line.split('#')[0].rstrip()
                    if code_part:
                        cleaned_lines.append(code_part + '\n')
                else:
                    cleaned_lines.append(line)
        else:
            if stripped_line.endswith('"""') or stripped_line.endswith("'''"):
                in_multiline_comment = False
                continue

    with open(output_file, 'w') as file:
        file.writelines(cleaned_lines)


# Usage
input_file = 'movie-recommender-systems.py'  # Replace with your .py file path
output_file = 'cleaned_file.py'  # Output file path
remove_comments(input_file, output_file)