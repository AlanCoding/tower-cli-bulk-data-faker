
def list_ids(resp_json):
    id_list = []
    try:
        for item in resp_json['results']:
            id_list = item['id']
    except:
        pass
    return id_list