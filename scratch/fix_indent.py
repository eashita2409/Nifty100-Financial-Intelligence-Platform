import glob
import re

for f in glob.glob('tests/analytics/*.py'):
    with open(f, 'r') as file:
        content = file.read()
    content = re.sub(r'\n\s*conn\.execute\(\"CREATE TABLE companies', r'\n    conn.execute(\"CREATE TABLE companies', content)
    content = re.sub(r'\n\s*conn\.execute\(\"INSERT INTO companies', r'\n    conn.execute(\"INSERT INTO companies', content)
    with open(f, 'w') as file:
        file.write(content)
