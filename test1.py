import json

import os
import time
import csv

def json_to_csv(path, objectData, objectName):
    header = []
    for index, data in enumerate(objectData['QueryInfo']['SelectFields']):
        header.append(data['Name'])

    body = []
    for index, data in enumerate(objectData['Results']):
        row = []
        # filteredData = json.dumps(data, indent=4)
        for index, headerItem in enumerate(header):
            headerItemArr = headerItem.split('.')
            columnData = ''
            temp = data
            if(len(headerItemArr) > 1):
                for splitedHeaderItem in headerItemArr: #configuration.state.name
                    try:
                        temp = temp[splitedHeaderItem]
                    except:
                        temp = ''

                columnData = temp
            else:
                columnData = data[headerItem]
            
            row.append(columnData)
        body.append(row)

    with open(os.path.join(path, objectName), 'w', newline='') as fp:
        output = csv.writer(fp)
        output.writerow(header)
        # output.writerow(data['QueryInfo']['SelectFields'])
        for row in body:
            output.writerow(row)

def raw_to_json(raw):
    newResults = []
    for item in raw['Results']:
        jsonItem = json.loads(item)
        newResults.append(jsonItem)
    
    raw['Results'] = newResults

    return raw

def lambda_handler():
    # Query for the AWS Config discovery
    f = open('./tmp/Results-origin.json')
    objectData = json.load(f)
    objectName = 'Results-'+ str(time.time()) +'.csv'
    
    jsonData = raw_to_json(objectData)
    print(jsonData)
    json_to_csv('./tmp', jsonData, objectName)

def test():
    print(time.strftime("%Y-%m-%d_%H-%M-%S"))

if __name__ == '__main__':
    test()