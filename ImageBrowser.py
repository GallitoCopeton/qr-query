import random

import pymongo
import read_image as ir


class ImageBrowser:

    def __init__(self, QR, DB, LOCATION):
        self.QR = QR
        self.DB = DB
        self.__timeout = False
        self.LOCATION = LOCATION.upper()
        self.found = False

    def browse_images(self):
        try:
            images = ir.read_from_DB(self.DB, self.QR)
            if images == 0:
                self.found = False
                return {
                    'timeout': self.__timeout,
                    'found': self.found,
                    'location': self.LOCATION
                }
            elif images != 0 and len(images) < 3:
                ir.show_results(images)
                self.found = True
                return {
                    'timeout': self.__timeout,
                    'found': self.found,
                    'location': self.LOCATION
                }
            elif images != 0 and len(images) > 3:
                rand_sample = random.sample(images, k=3)
                ir.show_results(rand_sample)
                self.found = True
                return {
                    'timeout': self.__timeout,
                    'found': self.found,
                    'location': self.LOCATION
                }
        except pymongo.errors.ServerSelectionTimeoutError:
            self.__timeout = True
            self.found = False
            return {
                'timeout': self.__timeout,
                'found': self.found,
                'location': self.LOCATION
            }
