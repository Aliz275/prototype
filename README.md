# how to set up secret key:
python -c "import secrets; print(secrets.token_hex(16))"

example: f7faaa9ab2e1b3145a527a573f3c7489

then > set FLASK_SECRET_KEY=f7faaa9ab2e1b3145a527a573f3c7489 OR $env:FLASK_SECRET_KEY=f7faaa9ab2e1b3145a527a573f3c7489 if on PSH

for now you can use: $env:FLASK_SECRET_KEY="a-secret-key-that-is-long-and-random"
once set up, python main.py


super admin login:
testemail@gmail.com
testpassword

inv URL: http://localhost:8000/api/invitations
inv URL with token: http://localhost:3000/accept-invitation?token=TOKENHERE

Known issue:
password encryption does not work as intended, will fix this asap (backend)