class Browser:

    def __init__(self, QR, DB, LOCATION):
        self.QR = QR
        self.DB = DB
        self.timeout = False
        self.LOCATION = LOCATION.upper()
        self.found = False