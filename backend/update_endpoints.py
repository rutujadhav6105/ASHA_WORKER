import os
import re

files_to_check = ['visits.py', 'children.py', 'vaccination.py', 'vaccine.py', 'anc.py', 'family_planning.py', 'family.py']
for fname in files_to_check:
    path = os.path.join('C:/FlutterProject/backend/app/routes', fname)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # We find:
        # db.session.add(model)
        # db.session.commit()
        # and we append the logger.info line.
        new_content = re.sub(
            r'(db\.session\.add\([^)]+\)\s*db\.session\.commit\(\))',
            r'\1\n        logger.info("Data saved successfully")',
            content
        )
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {fname}')
        else:
            print(f'No match in {fname}')
