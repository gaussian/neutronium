def get_canonical_email(email=None):
    """
    :param email:
    :return: Returns the lowercase canonical email without `+` or `.` characters.
    """

    if not email:
        return None

    # Convert email to lowercase
    email = email.lower()

    delimited_email = email.split("@")
    domain = delimited_email[-1]

    # Get the significand of an email address (removing any extra @'s)
    significand = "".join(delimited_email[0:-1])

    # Strip substring from first `+` to the `@`
    if "+" in significand:
        significand = significand[0 : significand.find("+")]

    return "@".join([significand, domain])
