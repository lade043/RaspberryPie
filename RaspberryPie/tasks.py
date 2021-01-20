from RaspberryPie.internetHandling import MajGenApiCom

class Task:
        def __init__(self, function, check):
            self.function = function
            self.check = check
        def test(self, email: MajGenApiCom.Telegram):
            return self.check(email)