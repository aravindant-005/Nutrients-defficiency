import os
import runpy
import sys

# Ensure backend package is importable
sys.path.insert(0, r'e:\nutrients\backend')

os.environ['DB_LOAD'] = '1'
print('DB_LOAD set to', os.environ['DB_LOAD'])
print('Running scripts/load_database.py (this may take several minutes)...')
runpy.run_path(r'e:\nutrients\backend\scripts\load_database.py', run_name='__main__')
print('Seeding completed (script finished).')
