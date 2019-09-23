from datetime import datetime

import pandas as pd
import pymongo
from geopy.geocoders import Nominatim
from IPython.display import display

from Browser import Browser


class DataBrowser(Browser):

    def browseData(self):
        try:
            qr_documents = self.DB.registerstotals.find({'qrCode': self.QR})
            self.timeout = False
            if qr_documents.count() == 0:
                self.found = False
                return {
                    'timeout': self.timeout,
                    'found': self.found,
                    'location': self.LOCATION,
                    'data': None
                }
            else:
                self.found = True
        except pymongo.errors.ServerSelectionTimeoutError:
            self.timeout = True
            self.found = False
            return {
                'timeout': self.timeout,
                'found': self.found,
                'location': self.LOCATION,
                'data': None
            }
        geolocator = Nominatim(user_agent='Query')
        list_dicts = []
        default_header = ['No. Imagen', 'Validez',
                          'Fecha + 5hrs', 'Ciudad', 'Fecha Consulta', 'Base', 'QR']
        for document in qr_documents:
            temporary_dict = {}
            # Location extraction
            latitude = str(document['location'][0]['latitude'])
            longitude = str(document['location'][0]['longitude'])
            exact_location = latitude + ',' + longitude
            # Object building
            try:
                location = geolocator.reverse(exact_location)
                temporary_dict = {
                    'Ciudad': location.raw['address']['city'],
                    'Validez': document['control'],
                    'No. Imagen': document['count'],
                    'Fecha + 5hrs': str(document['createdAt'])[0:-10],
                    'Fecha Consulta': str(datetime.now().isoformat())[0:-10],
                    'Base': self.LOCATION,
                    'QR': self.QR
                }
            except:
                location = exact_location
                temporary_dict = {
                    'Ciudad': location,
                    'Validez': document['control'],
                    'No. Imagen': document['count'],
                    'Fecha + 5hrs': str(document['createdAt'])[0:-10],
                    'Fecha Consulta': str(datetime.now().isoformat())[0:-10],
                    'Base': self.LOCATION,
                    'QR': self.QR
                }

            names_proteins = []
            for marker in document['marker']:
                names_proteins.append(marker['name'])
                header = default_header + names_proteins
                temporary_dict[marker['name']] = marker['result']
            list_dicts.append(temporary_dict)
        # Update dataframe
        result_dataframe = pd.DataFrame.from_dict(list_dicts)
        result_dataframe = result_dataframe[header]
        result_dataframe = result_dataframe.sort_values(
            by=['Fecha + 5hrs'], ascending=True)
        display(result_dataframe.head())
        return {
            'timeout': self.timeout,
            'found': self.found,
            'location': self.LOCATION,
            'data': result_dataframe
        }
