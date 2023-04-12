import streamlit_authenticator as stauth

hashed_passwords_1 = stauth.Hasher(['234567']).generate()
hashed_passwords_2 = stauth.Hasher(['345678']).generate()
hashed_passwords_3 = stauth.Hasher(['456789']).generate()

print(hashed_passwords_1)
print(hashed_passwords_2)
print(hashed_passwords_3)
