import os
import nbformat


def is_conversion_needed(notebook_path, output_path):
    # If the .py file does not exist, we need to convert
    if not os.path.isfile(output_path):
        return True
    # If the .ipynb file is newer than the .py file, we need to convert
    return os.path.getmtime(notebook_path) > os.path.getmtime(output_path)


def should_skip_cell(cell):
    return 'skip' in cell.metadata.get('tags', [])


def ipynb_to_py(notebook_path):
    # Construct the output path by replacing the .ipynb extension with .py
    output_path = os.path.splitext(notebook_path)[0] + '.py'
    if not is_conversion_needed(notebook_path, output_path):
        return
    
    # Load the notebook
    with open(notebook_path, 'r', encoding='utf-8') as fh:
        nb = nbformat.read(fh, as_version=4)
    
    # Filter out only code cells
    code_cells = [cell for cell in nb.cells
                  if cell.cell_type == 'code' and not should_skip_cell(cell)]
    
    # Combine the code from all code cells into a single string
    code = "\n\n\n".join(cell.source for cell in code_cells)
        
    # Write the code to the output file
    with open(output_path, 'w', encoding='utf-8') as code_file:
        code_file.write(code)


def all_ipynb_to_py(start_path = '.'):
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file.endswith('.ipynb'):
                notebook_path = os.path.join(root, file)
                ipynb_to_py(notebook_path)