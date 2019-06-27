import pandas as pd
import pymongo
from geopy.geocoders import Nominatim
from IPython.display import display

from Browser import Browser


class DataBrowser(Browser):

    def browse_data(self):
        try:
            qr_documents = self.DB.registerstotals.find({'qrCode': self.QR})
            self.timeout = False
            if qr_documents.count() == 0:
                self.found = False
                return {
                    'timeout': self.timeout,
                    'found': self.found,
                    'location': self.LOCATION
                }
            else:
                self.found = True
        except pymongo.errors.ServerSelectionTimeoutError:
            self.timeout = True
            self.found = False
            return {
                'timeout': self.timeout,
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
            display(result_dataframe)
            return {
                'timeout': self.timeout,
                'found': self.found,
                'location': self.LOCATION
            }
