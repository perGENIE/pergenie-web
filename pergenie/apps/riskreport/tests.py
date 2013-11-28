# -*- coding: utf-8 -*-

import sys, os
import time
import datetime
from pymongo import MongoClient

from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import activate as translation_activate
from lib.mongo.import_variants import import_variants
from lib.test import LoginUserTestCase
from utils.clogging import getColorLogger
log = getColorLogger(__name__)


class SimpleTest(LoginUserTestCase):
    def _setUp(self):
        pass

    def _tearDown(self):
        pass

    # def _import_data(self):
    #     """Import genome data for test.
    #     """

    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         catalog_cover_rate = c['pergenie']['catalog_cover_rate']
    #         data_info = c['pergenie']['data_info']

    #         # Import data #1
    #         info = {'user_id': self.test_user_id,
    #                 'name': self.file_cleaned_name,
    #                 'raw_name': self.file_raw_name,
    #                 'date': datetime.datetime.today(),
    #                 'population': self.file_population,
    #                 'file_format': 'andme',
    #                 'catalog_cover_rate': catalog_cover_rate.find_one({'stats': 'catalog_cover_rate'})['values']['andme'],
    #                 'genome_cover_rate': catalog_cover_rate.find_one({'stats': 'genome_cover_rate'})['values']['andme'],
    #                 'status': float(0.0)}
    #         data_info.insert(info)

    #         import_variants(file_path=self.file_raw_path,
    #                         population='unknown',
    #                         file_format='andme',
    #                         user_id=self.test_user_id)

    #         # Import data #2
    #         info = {'user_id': self.test_user_id,
    #                 'name': self.file_cleaned_name_2,
    #                 'raw_name': self.file_raw_name_2,
    #                 'date': datetime.datetime.today(),
    #                 'population': self.file_population_2,
    #                 'file_format': 'andme',
    #                 'catalog_cover_rate': catalog_cover_rate.find_one({'stats': 'catalog_cover_rate'})['values']['vcf_whole_genome'],
    #                 'genome_cover_rate': catalog_cover_rate.find_one({'stats': 'genome_cover_rate'})['values']['vcf_whole_genome'],
    #                 'status': float(0.0)}
    #         data_info.insert(info)

    #         import_variants(file_path=self.file_raw_path_2,
    #                         population='unknown',
    #                         file_format='vcf_whole_genome',
    #                         user_id=self.test_user_id)

    # def _delete_data(self):
    #     """Delete *test data*.
    #     """

    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         db = c['pergenie']
    #         data_info = db['data_info']

    #         # delete collection `variants.user_id.filename`
    #         db.drop_collection('variants.{0}.{1}'.format(self.test_user_id, self.file_cleaned_name))
    #         db.drop_collection('variants.{0}.{1}'.format(self.test_user_id, self.file_cleaned_name_2))

    #         # because it is just a test, no need to delete `file`

    #         # delete document in `data_info`
    #         founds = list(data_info.find({'user_id': self.test_user_id}))
    #         if founds:
    #             for found in founds:
    #                 data_info.remove(found)

    #         user_info = c['pergenie']['user_info']
    #         user_info.update({'user_id': self.test_user_id},
    #                          {'$set': {'last_viewed_file': ''}}, upsert=True)

    def test_login_required(self):
        response = self.client.get('/riskreport/')
        self.assertEqual(response.status_code, 302)

        # TODO: check all studies?
        response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./')
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./?file_name=' + self.file_cleaned_name)
        self.assertEqual(response.status_code, 302)

    # def test_index_success(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.context['err'], '')

    # def test_index_no_data_uploaded(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)

    #     response = self.client.get('/riskreport/')
    #     self.assertEqual(response.context['err'], 'no data uploaded')

    # def test_index_file_is_in_importing(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     # create *in importing* file
    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         data_info = c['pergenie']['data_info']
    #         data_info.update({'name': self.file_cleaned_name,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name})
    #     self.assertEqual(response.context['err'], '{0} is in importing, please wait for seconds...'.format(self.file_cleaned_name))

    # def test_index_files_are_in_importing(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     # create *in importing* file
    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         data_info = c['pergenie']['data_info']
    #         data_info.update({'name': self.file_cleaned_name,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})
    #         data_info.update({'name': self.file_cleaned_name_2,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})

    #     response = self.client.get('/riskreport/')
    #     self.assertEqual(response.context['err'], 'Your files are in importing, please wait for seconds...')

    # def test_index_success_imported_file_and_importing_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     # create *in importing* file
    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         data_info = c['pergenie']['data_info']
    #         data_info.update({'name': self.file_cleaned_name,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})

    #     # if there is *imported* file and *in importing* file,
    #     # show *imported* file.
    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="testvcf40vcf" selected>' in response.content)

    # def test_index_no_such_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.post('/riskreport/', {'file_name': 'dummytxt'})
    #     self.assertEqual(response.context['err'], 'no such file dummytxt')


    # # TODO: will get 302... ?
    # # def test_study_success(self):
    # #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    # #     self._import_data()

    # #     response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./')
    # #     self.assertEqual(response.status_code, 200)

    # def test_study_nosuch_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./?file_name=' + 'dummy')
    #     self.assertEqual(response.status_code, 404)

    # def test_index_not_change_population_or_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name,
    #                                                  'population': self.file_population})
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)

    # def test_index_change_population(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name,
    #                                                  'population': 'Japanese'})
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="Japanese" selected>' in response.content)

    # def test_index_change_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name_2,
    #                                                  'population': self.file_population})
    #     self.assertTrue('<option value="testvcf40vcf" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)
