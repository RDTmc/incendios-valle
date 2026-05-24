path = '/app/main.py'
with open(path) as f:
    c = f.read()

# Fix: ensure File is imported from fastapi
if 'File' not in c.split('from fastapi import')[1].split('\n')[0]:
    c = c.replace(
        'from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile',
        'from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File'
    )

with open(path, 'w') as f:
    f.write(c)
print('FIXED IMPORT')
