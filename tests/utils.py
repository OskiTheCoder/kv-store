class FakeClock:
    def __init__(self) -> None:
        self.now_ms = 0

    def __call__(self) -> int:
        return self.now_ms

    def advance(self, milliseconds: int) -> None:
        self.now_ms += milliseconds