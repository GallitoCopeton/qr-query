
import pandas as pd
import pymongo
from geopy.geocoders import Nominatim


class DataBrowser:

    def __init__(self, QR, DB, LOCATION):
        self.QR = QR
        self.DB = DB
        self.__timeout = False
        self.LOCATION = LOCATION.upper()
        self.found = False

    def browse_data(self):
        try:
            qr_documents = self.DB.registerstotals.find({'qrCode': self.QR})
        except pymongo.errors.ServerSelectionTimeoutError:
            self.__timeout = True
            self.found = False
            return {
                'timeout': self.__timeout,
                'found': self.found,
                'location': self.LOCATION
            }
        geolocator = Nominatim(user_agent='Query')
        result_dataframe = pd.DataFrame()
        for document in qr_documents:
            # Location extraction
            latitude = str(document['location'][0]['latitude'])
            longitude = str(document['location'][0]['longitude'])
            exact_location = latitude + ',' + longitude
            location = geolocator.reverse(exact_location)
            # Object building
            temporary_dict = {
                'Ciudad': location.raw['address']['city'],
                'Validez': document['control'],
                'No. Imagen': document['count'],
                'Fecha + 5hrs': str(document['createdAt'])
            }
            for marker in document['marker']:
                temporary_dict[marker['name']] = marker['result']
            # Update dataframe
            result_dataframe = result_dataframe.append(
                temporary_dict, ignore_index=True)
