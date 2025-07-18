import email_validator
from langchain_core.tools import tool

@tool
def validate_email(email):
    '''this tool use for validate email and checks that email exist or not.
    '''
    try:
        email_validator.validate_email(email)
        return True  # Valid email address
    except email_validator.EmailNotValidError:
        return False  # Invalid email address

# Example usage:
# if validate_email("rohanbanda103@gmail.com"):
#     print("Valid email address")
# else:
#     print("Invalid email address")
