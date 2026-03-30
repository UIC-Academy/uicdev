def generate_sms_code():
    import random

    d1 = random.randint(0, 9)
    d2 = random.randint(0, 9)
    d3 = random.randint(0, 9)
    d4 = random.randint(0, 9)
    d5 = random.randint(0, 9)
    d6 = random.randint(0, 9)

    return f"{d1}{d2}{d3}{d4}{d5}{d6}"
