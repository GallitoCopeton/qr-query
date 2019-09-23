import random

import pymongo

import Browser
import readImage as ir


class ImageBrowser(Browser.Browser):

    def browseImages(self):
        try:
            images = ir.readManyFromDbDetails(self.DB, self.QR)
            if len(images) == 0:
                print('Images found: {}'.format((images)))
                self.found = False
                return {
                    'timeout': self.timeout,
                    'found': self.found,
                    'location': self.LOCATION,
                    'images': []
                }
            else:
                print('Images found: {}'.format(len(images)))
                self.found = True
                return {
                    'timeout': self.timeout,
                    'found': self.found,
                    'location': self.LOCATION,
                    'images': images
                }
        except pymongo.errors.ServerSelectionTimeoutError:
            self.timeout = True
            self.found = False
            return {
                'timeout': self.timeout,
                'found': self.found,
                'location': self.LOCATION,
                'images': []
            }
