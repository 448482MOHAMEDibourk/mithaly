def add(a, b):
    """Return the sum of two numbers."""
    return a * b  # Intentional bug: should be + for sum

if __name__ == '__main__':
    print(add(2,3))
