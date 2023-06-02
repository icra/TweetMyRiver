"""
Model exported as python.
Name : Twitter river CES
Group : Tweet My River
With QGIS : 32213
"""


from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
from qgis.core import QgsProcessingContext
from qgis.core import QgsProcessingFeedback
from qgis.core import QgsProject
from qgis.core import QgsProcessingUtils
from .Extraction import extraction
from .Translate import translation
import processing

import subprocess

import os

import shutil


class TwitterRiverCes(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterNumber('radiusdistancebetwenpoints', 'Radius / distance betwen points (meters)', optional=True, type=QgsProcessingParameterNumber.Integer, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('rivernetworklayer', 'River network layer', optional=True, types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterFile('keywords', 'Key Words file (.txt)', optional=True, behavior=QgsProcessingParameterFile.File, fileFilter='All Files (*.*)', defaultValue=None))
        self.addParameter(QgsProcessingParameterString('apikey', 'API Key', multiLine=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterFile('usearchingpoints', 'Users\' searching points', optional=True, fileFilter='Microsoft Excel (*.xlsx);;Open Document Spreadsheet (*.ods)', defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(11, model_feedback)
        results = {}
        outputs = {}

        if parameters['radiusdistancebetwenpoints'] and parameters['rivernetworklayer']:
            # Field calculator - dis
            alg_params = {
                'FIELD_LENGTH': 5,
                'FIELD_NAME': 'dis',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1,  # Integer
                'FORMULA': '1',
                'INPUT': parameters['rivernetworklayer'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['FieldCalculatorDis'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}

            # Dissolve - dis
            alg_params = {
                'FIELD': ['dis'],
                'INPUT': outputs['FieldCalculatorDis']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['DissolveDis'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(4)
            if feedback.isCanceled():
                return {}

            # Retain fields - dis
            alg_params = {
                'FIELDS': ['dis'],
                'INPUT': outputs['DissolveDis']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['RetainFieldsDis'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(5)
            if feedback.isCanceled():
                return {}

            # Points along geometry - accord. to Dist
            alg_params = {
                'DISTANCE': parameters['radiusdistancebetwenpoints'],
                'END_OFFSET': 0,
                'INPUT': outputs['RetainFieldsDis']['OUTPUT'],
                'START_OFFSET': 0,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['PointsAlongGeometryAccordToDist'] = processing.run('native:pointsalonglines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(6)
            if feedback.isCanceled():
                return {}

            # Field calculator - id
            alg_params = {
                'FIELD_LENGTH': 15,
                'FIELD_NAME': 'id',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1,  # Integer
                'FORMULA': '$id',
                'INPUT': outputs['PointsAlongGeometryAccordToDist']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['FieldCalculatorId'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(7)
            if feedback.isCanceled():
                return {}

            # Field calculator - add Dist field
            alg_params = {
                'FIELD_LENGTH': 10,
                'FIELD_NAME': 'Dist',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1,  # Integer
                'FORMULA': parameters['radiusdistancebetwenpoints'],
                'INPUT': outputs['FieldCalculatorId']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['FieldCalculatorAddDistField'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)




            feedback.setCurrentStep(8)
            if feedback.isCanceled():
                return {}

            # Reproject layer - to 4326
            alg_params = {
                'INPUT': outputs['FieldCalculatorAddDistField']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojectLayerTo4326'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(9)
            if feedback.isCanceled():
                return {}

            # Add geometry attributes
            alg_params = {
                'CALC_METHOD': 0,  # Layer CRS
                'INPUT': outputs['ReprojectLayerTo4326']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['AddGeometryAttributes'] = processing.run('qgis:exportaddgeometrycolumns', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(10)
            if feedback.isCanceled():
                return {}

            # Export to spreadsheet

            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(current_dir, "Data", "River_points.xlsx")

            alg_params = {
                'FORMATTED_VALUES': False,
                'LAYERS': outputs['AddGeometryAttributes']['OUTPUT'],
                'OVERWRITE': False,
                'USE_ALIAS': True,
                'OUTPUT': output_dir
            }
            outputs['ExportToSpreadsheet'] = processing.run('native:exporttospreadsheet', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['Searchingpoints'] = outputs['ExportToSpreadsheet']['OUTPUT']

        #If needed, copy the River points file into the working directory
        elif parameters['usearchingpoints']:
            output_dir = parameters['usearchingpoints']
            current_dir = os.path.dirname(os.path.abspath(__file__))
            folder_dir = os.path.join(current_dir, "Data", "River_points.xlsx")
            if not os.path.samefile(output_dir, folder_dir):
                shutil.copy(output_dir, folder_dir)


        else:
            feedback.setProgressText("---- ERROR: Missing input data (either radius + layer or Users' searching points) ----")

        # TWEET EXTRACTION

        # Define the inputs
        input1 = output_dir
        input2 = parameters['apikey']

        # Set the working directory as the current_dir
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Set the path were an "export_dataframe.xsls" file should be if it already exists
        path_delete = os.path.join(current_dir, "Data", "export_dataframe.xlsx")

        # Check if it already exists an "export_dataframe.xlsx" file and delete it if true
        if os.path.exists(path_delete):
            os.remove(path_delete)
            feedback.setProgressText("---- DELETING PREVIOUS EXTRACTION FILE ----")
        else:
            feedback.setProgressText("---- NO PREVIOUS EXTRACTION FILE FOUND ----")

        # Check if there's the optional keywords file and add it to the arguments list
        input4 = None
        if parameters['keywords']:
            input4 = parameters['keywords']

        feedback.setProgressText("---- STARTING TWEET EXTRACTION ----")

        # Execute the Extraction script with all the given parameters
        try:
            extraction(input1, input2, current_dir+"\Data", input4)
        except Exception as e:
            feedback.setProgressText("---- ERROR WHILE EXTRACTING TWEETS ----" + str(e))

        feedback.setProgressText("---- TWEETS CORRECTLY EXTRACTED ----")

        # TWEET TRANSLATION

        feedback.setProgressText("---- STARTING TWEET TRANSLATION ----")

        # Define the path were the extracted data file is found
        extracted_path = os.path.join(current_dir, "Data", "export_dataframe.xlsx")

        # Execute the translation script with the file generated from the extration process

        try:
            translation(extracted_path)
        except Exception as e:
            feedback.setProgressText("---- ERROR WHILE TRANSLATIONG TWEETS ----" + str(e))

        feedback.setProgressText("---- EXTRACTION + TRANSLATION FINISHED ----")

        return results
        
        # Create points layer from table
        alg_params = {
            'INPUT': QgsExpression('').evaluate(),
            'MFIELD': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'XFIELD': 'xcoord',
            'YFIELD': 'xcoord',
            'ZFIELD': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CreatePointsLayerFromTable'] = processing.run('native:createpointslayerfromtable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['CesTweets'] = outputs['CreatePointsLayerFromTable']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

    def name(self):
        return 'Extraction and Translation'

    def displayName(self):
        return 'Extraction and Translation'

    def group(self):
        return 'Twitter'

    def groupId(self):
        return 'Twitter'

    def createInstance(self):
        return TwitterRiverCes()

    def getApiKey(self):
        return self.apikey

