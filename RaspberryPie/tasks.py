class Task:
        def __init__(self, function, check):
            self.function = function
            self.check = check
        def test(self, email: MajGenApiTelecom.Telegram):
            return self.check

tasks = [
    Task(majGenGPIOController.open, lambda msg: 1 if ("auf" == msg.subject.lower() or "open" == msg.subject.lower()) else 0),
    Task(majGenGPIOController.close, lambda msg: 1 if ("zu" == msg.subject.lower() or "close" == msg.subject.lower()) else 0)
]