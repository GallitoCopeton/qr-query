import pymongo
# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas.
atlasURI = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
atlasClient = pymongo.MongoClient(atlasURI)
atlasDb = atlasClient.datamap
idenmonURI = 'mongodb://findOnlyReadUser:RojutuNHqy@idenmon.zapto.org:888/?authSource=prodLaboratorio'
idenmonClient = pymongo.MongoClient(idenmonURI)
idenmonDb = idenmonClient.prodLaboratorio

atlasImages = atlasDb.imagestotals.find({}, no_cursor_timeout=True).limit(20)

for image in atlasImages:
    fileName = image['fileName']
    count = image['count']
    createdAt = image['createdAt']
    imageFile = image['file']
    idenmonImage = idenmonDb.imagestotals.find({
        'fileName': fileName,
        'count': count
    })
    if len(list(idenmonImage)) == 0:
        print(
            f'The image with qr {fileName} and count {count} should be moved to idenmon')
        newEntry = {
            'fileName': fileName,
            'count': count,
            'createdAt': createdAt,
            'file': imageFile
        }
        try:
            insertion = idenmonDb.imagestotals.insert_one(newEntry)
            print(insertion)
        except pymongo.errors.OperationFailure as err:
            print(err)
    else:
        print(
            f'The image with qr {fileName} and count {count} is already in idenmon')
atlasImages.close()
