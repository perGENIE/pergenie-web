#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import re
import subprocess
import datetime
import zipfile
import logging
from pprint import pformat, pprint
from collections import defaultdict
try:
    import cPickle as pickle
except ImportError:
    import pickle

sys.path.append('../')
from mongo.parser.VCFParser import VCFParser, VCFParseError
from mongo.parser.andmeParser import andmeParser, andmeParseError
from riskreport_base import RiskReportBase

# Logger
log = logging.getLogger()
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
log.addHandler(sh)


class CUIRiskReport(RiskReportBase):
    """
    CUI version of RiskReport

    - No Django dependency
    - No MongoDB dependency

    Instead of using databases,

    - Load GWAS Catalog everytime
    - Load Genomes everytime
    """

    def __init__(self):
        self.FILEFORMATS = [
            {'name': 'vcf_whole_genome',
             'extention': '*.vcf',
             'long_name': 'VCF (Whole Genome)',
             'short_name': 'wg',
             'region_file': ''},
            {'name': 'vcf_exome_truseq',
             'extention': '*.vcf',
             'long_name': 'VCF (TruSeq Exome)',
             'short_name': 'truseq',
             'region_file': 'TruSeq-Exome-Targeted-Regions-BED-file'},
            {'name': 'andme',
             'extention': '*.txt',
             'long_name': '23andMe',
             'short_name': 'andme',
             'region_file': 'andme_region'},
        ]

        self.POPULATION_MAP = {'African': ['African'],
                               'European': ['European'],
                               'Asian': ['Asian'],
                               'Japanese': ['Japanese'],
                               'unknown': ['']}

        self.POPULATION = self.POPULATION_MAP.keys()


    def load_gwascatalog(self, population):
        """Load GWAS Catalog

        - for each `population`
        - only `highest reliability rank`
        - with `is_is_region`
        """

        path_to_gwascatalog = 'gwascatalog.pergenie.{population}.p'.format(population=population)
        log.info('Loading: %s' % path_to_gwascatalog)

        with file(path_to_gwascatalog, 'rb') as fin:
            self.gwascatalog_records = pickle.load(fin)

            #
            self.gwascatalog_uniq_snps = set([201752861])


    def load_genome(self, file_path, file_format):
        """Load variants (genotypes)
        """

        variants = defaultdict(int)

        log.info('Input file: %s' % file_path)
        file_lines = int(subprocess.Popen(['wc', '-l', file_path], stdout=subprocess.PIPE).communicate()[0].split()[0])  # py26
        log.info('#lines: %s' % file_lines)
        log.info('Start importing ...')

        with open(file_path, 'rb') as fin:
            try:
                p = {'vcf_whole_genome': VCFParser,
                     'vcf_exome_truseq': VCFParser,
                     'vcf_exome_iontargetseq': VCFParser,
                     'andme': andmeParser}[file_format](fin)

                for i,data in enumerate(p.parse_lines()):
                    if file_format in [x['name'] for x in self.FILEFORMATS if x['extention'] == '*.vcf']:
                        # TODO: handling multi-sample .vcf file
                        # currently, choose first sample from multi-sample .vcf
                        tmp_genotypes = data['genotype']
                        data['genotype'] = tmp_genotypes[p.sample_names[0]]

                    # Minimum load
                    if data['rs'] and data['rs'] in self.gwascatalog_uniq_snps:
                        variants[data['rs']] = dict((k, data[k]) for k in ('chrom', 'pos', 'genotype'))  # py26
                        #                      {k: data[k] for k in ('chrom', 'pos', 'rs', 'genotype')}  # py27

                    if i > 0 and i % 10000 == 0:
                        log.debug('{i} lines done...'.format(i=i+1))

                log.info('done!')
                return variants

            except (VCFParseError, andmeParseError), e:
                log.error('ParseError: %s' % e.error_code)
                return e.error_code


    def write_riskreport(self, infile, file_format, outfile):
        """Write out riskreport(.tsv|.csv) as .zip
        """

        # Load GWAS Catalog -> catalog_map
        catalog_records = self.gwascatalog_records
        catalog_map = {}
        found_id = 0
        snps_all = set()
        for record in catalog_records:
            if record['snps'] != 'na':
                snps_all.update([record['snps']])

                found_id += 1
                # reported_genes = ', '.join([gene['gene_symbol'] for gene in record['reported_genes']])
                # mapped_genes = ', '.join([gene['gene_symbol'] for gene in record['mapped_genes']])
                catalog_map[found_id] = record
                catalog_map[found_id].update({'rs': record['snps'],
                                              # 'reported_genes': reported_genes,
                                              # 'mapped_genes': mapped_genes,
                                              'chr': record['chr_id'],
                                              'freq': record['risk_allele_frequency'],
                                              # 'added': record['added'].date(),
                                              # 'date': record['date'].date()})
                                              })

        # Load Genome -> variants_map
        variants = self.load_genome(infile, file_format)
        variants_map = defaultdict(int)

        for _id, _catalog in catalog_map.items():
            rs = _catalog['rs']
            if rs and rs != 'na':
                found = variants.get(rs)

                # Case1: in catalog & in variants
                if found:
                    variants_map[rs] = found['genotype']

                # Case2: in catalog, but not in variants. so genotype is homozygous of `ref` or `na`.
                else:
                    ref = _catalog['ref']
                    na = 'na'
                    if file_format == 'andme':
                        genotype = na

                    elif file_format == 'vcf_whole_genome':
                        genotype = ref * 2

                    elif file_format == 'vcf_exome_truseq':
                        if rec['is_in_truseq']:
                            genotype = ref * 2
                        else:
                            genotype = na

                    elif file_format == 'vcf_exome_iontargetseq':
                        if rec['is_in_iontargetseq']:
                            genotype = ref * 2
                        else:
                            genotype = na

                    variants_map[rs] = genotype

        # Risk Calculation -> risk_store, risk_report
        risk_store, risk_report = self.risk_calculation(catalog_map, variants_map)
        # pprint(risk_store)
        # pprint(risk_report)


        # Write out Risk Report -> outfile (or stdout)
        if outfile:
            out = open(outfile, 'w')
        else:
            out = sys.stdout

        results = list()
        for trait, record in risk_report.items():
            RR = record.values()[0]
            snps = list()
            for study, snp_level_sotres in risk_store[trait].items():
                for snp, snp_level_sotre in snp_level_sotres.items():
                    snps.append(snp)

            results.append(dict(disease=trait,
                                RR=RR,
                                snps=','.join(['rs'+str(snp) for snp in snps]),
                                pubmed_link=snp_level_sotre['catalog_map']['pubmed_link'],
                                rank=snp_level_sotre['catalog_map']['rank']
                            ))

        header = ['disease', 'RR', 'pubmed_link', 'rank', 'snps']
        print >>out, '\t'.join(header)
        for row in results:
            print >>out, '\t'.join([str(row[x]) for x in header])


if __name__ == '__main__':
    import argparse
    r = CUIRiskReport()

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-I', '--infile', help='', required=True)
    parser.add_argument('-O', '--outfile', help='', default=None)
    parser.add_argument('-F', '--file-format', help='', required=True, choices=[x['name'] for x in r.FILEFORMATS])
    parser.add_argument('-P', '--population', help='', default='unknown', choices=r.POPULATION)
    args = parser.parse_args()

    r.load_gwascatalog(args.population)
    r.write_riskreport(args.infile, args.file_format, args.outfile)
