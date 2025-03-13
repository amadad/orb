import os
import re

def fix_imports_in_file(file_path):
    """Fix import statements in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace "from framework." with "from my_digital_being.framework."
    modified_content = re.sub(
        r'from framework\.', 
        'from my_digital_being.framework.', 
        content
    )
    
    # Replace "import framework." with "import my_digital_being.framework."
    modified_content = re.sub(
        r'import framework\.', 
        'import my_digital_being.framework.', 
        modified_content
    )
    
    if content != modified_content:
        with open(file_path, 'w') as f:
            f.write(modified_content)
        print(f"Fixed imports in {file_path}")
        return True
    return False

def fix_all_activity_imports():
    """Fix imports in all activity files."""
    activities_dir = "my_digital_being/activities"
    skills_dir = "my_digital_being/skills"
    
    # Count the number of files fixed
    fixed_count = 0
    
    # Fix activity files
    for filename in os.listdir(activities_dir):
        if filename.endswith(".py"):
            file_path = os.path.join(activities_dir, filename)
            if fix_imports_in_file(file_path):
                fixed_count += 1
    
    # Fix skill files if the directory exists
    if os.path.exists(skills_dir):
        for filename in os.listdir(skills_dir):
            if filename.endswith(".py"):
                file_path = os.path.join(skills_dir, filename)
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    fix_all_activity_imports() 