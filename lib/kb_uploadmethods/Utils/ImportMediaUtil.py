
import time
import json
import uuid

from FBAFileUtil.FBAFileUtilClient import FBAFileUtil
from DataFileUtil.DataFileUtilClient import DataFileUtil
from KBaseReport.KBaseReportClient import KBaseReport


def log(message, prefix_newline=False):
    """Logging function, provides a hook to suppress or redirect log messages."""
    print(('\n' if prefix_newline else '') + '{0:.2f}'.format(time.time()) + ': ' + str(message))


class ImportMediaUtil:
    def __init__(self, config):
        self.callback_url = config['SDK_CALLBACK_URL']
        self.token = config['KB_AUTH_TOKEN']
        self.dfu = DataFileUtil(self.callback_url)
        self.fba = FBAFileUtil(self.callback_url)

    def import_tsv_as_media_from_staging(self, params):
        '''
          import_tsv_as_media_from_staging: wrapper method for
                                    FBAFileUtil.tsv_file_to_media

          required params:
          staging_file_subdir_path - subdirectory file path
          e.g.
            for file: /data/bulk/user_name/file_name
            staging_file_subdir_path is file_name
            for file: /data/bulk/user_name/subdir_1/subdir_2/file_name
            staging_file_subdir_path is subdir_1/subdir_2/file_name
          media_name - output Media file name
          workspace_name - the name of the workspace it gets saved to.

          return:
          obj_ref: return object reference
        '''

        log('--->\nrunning ImportMediaUtil.import_tsv_as_media_from_staging\n' +
            'params:\n{}'.format(json.dumps(params, indent=1)))

        self.validate_import_media_from_staging_params(params)

        download_staging_file_params = {
            'staging_file_subdir_path': params.get('staging_file_subdir_path')
        }
        scratch_file_path = self.dfu.download_staging_file(
                        download_staging_file_params).get('copy_file_path')

        file = {
            'path': scratch_file_path
        }

        import_media_params = params
        import_media_params['file'] = file

        ref = self.fba.tsv_file_to_media(import_media_params)

        returnVal = {'obj_ref': ref.get('ref')}

        return returnVal

    def import_excel_as_media_from_staging(self, params):
        '''
          import_excel_as_media_from_staging: wrapper method for
                                    FBAFileUtil.excel_file_to_media

          required params:
          staging_file_subdir_path - subdirectory file path
          e.g.
            for file: /data/bulk/user_name/file_name
            staging_file_subdir_path is file_name
            for file: /data/bulk/user_name/subdir_1/subdir_2/file_name
            staging_file_subdir_path is subdir_1/subdir_2/file_name
          media_name - output Media file name
          workspace_name - the name of the workspace it gets saved to.

          return:
          obj_ref: return object reference
        '''

        log('--->\nrunning ImportMediaUtil.import_excel_as_media_from_staging\n' +
            'params:\n{}'.format(json.dumps(params, indent=1)))

        self.validate_import_media_from_staging_params(params)

        download_staging_file_params = {
            'staging_file_subdir_path': params.get('staging_file_subdir_path')
        }
        scratch_file_path = self.dfu.download_staging_file(
                        download_staging_file_params).get('copy_file_path')

        file = {
            'path': scratch_file_path
        }

        import_media_params = params
        import_media_params['file'] = file

        ref = self.fba.excel_file_to_media(import_media_params)

        returnVal = {'obj_ref': ref.get('ref')}

        return returnVal

    def validate_import_media_from_staging_params(self, params):
        """
        validate_import_media_from_staging_params:
                    validates params passed to import_excel(tsv)_as_media_from_staging method

        """

        # check for required parameters
        for p in ['staging_file_subdir_path', 'workspace_name', 'media_name']:
            if p not in params:
                raise ValueError('"{}" parameter is required, but missing'.format(p))

    def generate_report(self, obj_ref, params):
        """
        generate_report: generate summary report

        obj_ref: generated workspace object references. (return of
                                                        import_excel(tsv)_as_media_from_staging)
        params:
        staging_file_subdir_path: subdirectory file path
          e.g.
            for file: /data/bulk/user_name/file_name
            staging_file_subdir_path is file_name
            for file: /data/bulk/user_name/subdir_1/subdir_2/file_name
            staging_file_subdir_path is subdir_1/subdir_2/file_name
        workspace_name: workspace name/ID that reads will be stored to

        """

        uuid_string = str(uuid.uuid4())
        upload_message = 'Import Finished\n'

        get_objects_params = {
            'object_refs': [obj_ref],
            'ignore_errors': False
        }

        object_data = self.dfu.get_objects(get_objects_params)
        base_count = object_data.get('data')[0].get('data').get('base_counts')
        dna_size = object_data.get('data')[0].get('data').get('dna_size')

        upload_message += "Media Object Name: "
        upload_message += str(object_data.get('data')[0].get('info')[1]) + '\n'
        upload_message += 'Imported File: {}\n'.format(
                              params.get('staging_file_subdir_path'))

        if isinstance(dna_size, (int, long)):
            upload_message += 'DNA Size: {:,}\n'.format(dna_size)

        if isinstance(base_count, dict):
            upload_message += 'Base Count:\n{}\n'.format(json.dumps(base_count, indent=1)[2:-2])

        report_params = {
              'message': upload_message,
              'workspace_name': params.get('workspace_name'),
              'report_object_name': 'kb_upload_mothods_report_' + uuid_string}

        kbase_report_client = KBaseReport(self.callback_url, token=self.token)
        output = kbase_report_client.create_extended_report(report_params)

        report_output = {'report_name': output['name'], 'report_ref': output['ref']}

        return report_output
