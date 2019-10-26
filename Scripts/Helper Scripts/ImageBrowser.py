import random

import pymongo

import Browser
import readImage as ir


class ImageBrowser(Browser.Browser):

    def browseImages(self):
        try:
            images = ir.readManyFromDbDetails(self.DB, self.QR)
            if len(images) == 0:
                self.found = False
                return {
                    'timeout': self.timeout,
                    'found': self.found,
                    'location': self.LOCATION,
                    'images': []
                }
            else:
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

    def getLatestQrs(self, n):
        cursor = self.DB.imagetotals.find().limit(n).sort('_id', -1)
        foundQrs = [doc['filename'] for doc in cursor]
        return sorted(set(foundQrs), key=foundQrs.index)
    
