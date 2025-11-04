"""Sample project entry point."""


def main() -> None:
    value = helper(5)
    if value > 0:
        print(f"Result: {value}")


def helper(data: int) -> int:
    total = 0
    for index in range(data):
        total += index
    return total


if __name__ == "__main__":  # pragma: no cover
    main()
