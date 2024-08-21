# __MODULE__
import os
import nbformat
import re


# Convert only if the notebook has been changed
def is_conversion_needed(notebook_path, output_path):
    # If the .py file does not exist, we need to convert
    if not os.path.isfile(output_path):
        return True
    # If the .ipynb file is newer than the .py file, we need to convert
    return os.path.getmtime(notebook_path) > os.path.getmtime(output_path)


# Convert notebooks only if they are marked as a `__MODULE__`  
# Note: that in a normal notebook in a markdown cell `__MODULE__` may look like
# __MODULE__
def should_convernt_to_module(firstcell, moduleword = '__MODULE__'):
    return bool(re.search(f'(?<!\S)#?{moduleword}=?(?!\S)', firstcell))


def should_skip_cell(cell, skipwords='skip'):
    if type(skipwords) is str:
        skipwords = (skipwords,)
    for a_skip_word in skipwords:
        if a_skip_word in cell.metadata.get('tags', []):
            return True
    return False


def strip_lines_helper(text_lines):
    for i, line in enumerate(text_lines):
        if line.strip():
            break
    return i


def strip_lines(text):
    lines = text.splitlines()
    if not lines:
        return text
    start = strip_lines_helper(lines)
    finish = (-strip_lines_helper(lines[::-1]) or len(lines))
    return '\n'.join(lines[start:finish]) 


def comment_out(text):
    return '\n'.join([f'# {line}' for line in text.splitlines()])


def ipynb_to_py(notebook_path,
                output_base_path='module', module_word='__MODULE__',
                skipwords='skip', celltypes='*', dont_comment='code', code_sep='\n\n'):
    """
    Processes the notebook at the given path.

    Args:
        notebook_path (str): A relative path to the input notebook file.

    Note:
        notebook_path must be a relative path. Absolute paths are not supported.
    """
    assert not os.path.isabs(notebook_path), 'notebook_path must be relative'
    # Construct the output path by replacing the .ipynb extension with .py
    module_path = os.path.splitext(notebook_path)[0] + '.py'
    if not is_conversion_needed(notebook_path, module_path):
        return
    
    # Load the notebook
    print(f'{notebook_path=}')
    with open(notebook_path, 'r', encoding='utf-8') as fh:
        nb = nbformat.read(fh, as_version=4)

    if not should_convernt_to_module(nb.cells[0].source):
        return
    
    if type(dont_comment) is str:
        dont_comment = (dont_comment,)
        
    cells = [cell  
             for cell in nb.cells
             if not should_skip_cell(cell)
             if (celltypes == '*') or (cell.cell_type in celltypes)]
    
    # Combine the code from all code cells into a single string
    output_cells_texts = [strip_lines(cell.source) + code_sep
                          if cell.cell_type in dont_comment else
                          comment_out(strip_lines(cell.source))
                          for cell in cells
                          if cell.source.strip()]
    output = f'# compiled from {notebook_path}\n\n'
    output = "\n".join(cell_text for cell_text in output_cells_texts)
        
    # Write the code to the output file
    output_path = os.path.join(output_base_path, module_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as code_file:
        code_file.write(output)


def all_ipynb_to_py(root_path='.', dest_path='module', init_py=True):
    if init_py:
        os.makedirs(dest_path, exist_ok=True)
        f = open(os.path.join(dest_path, '__init__.py'), 'w')
        if type(init_py) is str: 
            f.write(init_py)
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [a_dir for a_dir in dirs
                   if not a_dir.startswith('.')
                   if not a_dir == dest_path and root == root_path]            
        relative_path = os.path.relpath(root, root_path)
        files[:] = [a_file for a_file in files
                    if a_file.endswith('.ipynb')]
        for a_file in files:
            notebook_path = os.path.join(root, a_file)
            ipynb_to_py(notebook_path, dest_path)

