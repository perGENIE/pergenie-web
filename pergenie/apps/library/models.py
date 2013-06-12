from pymongo import MongoClient, ASCENDING, DESCENDING
from lib.mongo.get_latest_catalog import get_latest_catalog
from django.conf import settings
from lib.mongo import search_variants


def get_latest_catalog_date():
    with MongoClient(host=settings.MONGO_URI) as c:
        catalog_info = c['pergenie']['catalog_info']
        latest_catalog_date = catalog_info.find_one({'status': 'latest'})['date']

        return latest_catalog_date

def get_libarary_and_variatns_of_a_trait(trait, user_id):
    with MongoClient(host=settings.MONGO_URI) as c:

        # catalog = get_latest_catalog(port=settings.MONGO_PORT)
        # founds = catalog.find({'trait': trait})

        data_info = c['pergenie']['data_info']

        uploadeds = list(data_info.find({'user_id': user_id}))
        file_names = [uploaded['name'] for uploaded in uploadeds]
        file_formats = [uploaded['file_format'] for uploaded in uploadeds]

        variants_maps = {}
        for file_name, file_format in zip(file_names, file_formats):
            library_map, variants_maps[file_name] = search_variants.search_variants(user_id=user_id, file_name=file_name, file_format=file_format,
                                                                                    query=trait, query_type='trait')

        library_list = [library_map[found_id] for found_id in library_map]

        return library_list, variants_maps

def get_uniq_snps_list():
    with MongoClient(host=settings.MONGO_URI) as c:
        catalog_stats = c['pergenie']['catalog_stats']
        return sorted(list(set([rec['value'] for rec in list(catalog_stats.find({'field': 'snps'}))])))

def get_omim_av_records(rs):
    with MongoClient(host=settings.MONGO_URI) as c:
        omim_av = c['pergenie']['omim_av']
        return list(omim_av.find({'rs': rs}).sort('mimNumber'))

def get_catalog_records(rs):
    catalog = get_latest_catalog(port=settings.MONGO_PORT)
    return list(catalog.find({'snps': rs}).sort('date', DESCENDING))
