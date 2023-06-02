"""
Model exported as python.
Name : TweetMyRiver
Group : TweetMyRiver
With QGIS : 32213
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsExpression
import processing
from .Predictions import predict

import subprocess

import os


class AiTraining(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterFile('userstrainningfilexlsx', "User's training file (.xlsx)", optional=True, behavior=QgsProcessingParameterFile.File, fileFilter='All Files (*.*)', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('allowedclassificationerror', 'Allowed classification error (%)', type=QgsProcessingParameterNumber.Double, maxValue=100, minValue=0, defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber('numberofcategoriesn', 'Number of categories (n)',
                                                       type=QgsProcessingParameterNumber.Integer, minValue=1,
                                                       maxValue=100, defaultValue=3))
        self.addParameter(QgsProcessingParameterFeatureSink('Mapces', 'Output Layer', type=QgsProcessing.TypeVectorPoint,
                                                                    createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)
        results = {}
        outputs = {}

        allowed_error = parameters['allowedclassificationerror']

        allowed_error = int(allowed_error)

        # Set the working directory as the current directory from where execute the different files
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Set the path where the predictions executable is found
        #executable_path = os.path.join(current_dir, "EXECUTABLES", "Predictions.exe")

        # Set the path where the data to classify (translated and filtered) is found
        translated_path = os.path.join(current_dir, "Data", "Data_translated.xlsx")

        # If user want to use a personalised training dataset take that as input. Otherwise, use the default training file
        training_file = None
        if parameters['userstrainningfilexlsx']:
            training_file = parameters['userstrainningfilexlsx']

        # Save the number of categories entered as input (3 by default)
        ncategs = str(parameters["numberofcategoriesn"])

        feedback.setProgressText("---- STARTING TRAINING + PREDICTION ----")

        # Start the classification script
        try:
            predict(translated_path, str(allowed_error), training_file, ncategs)
        except Exception as e:
            feedback.setProgressText("---- ERROR WHILE CLASSIFYING ----" + str(e))

        feedback.setProgressText("---- CLASSIFICATION FINISHED ----")

        # Get the histogram file of classified tweets for each point to create the resulting layer
        histo_path = os.path.join(current_dir, "Data", "PointsHistogram.xlsx")

        alg_params = {
            'INPUT': histo_path,
            'MFIELD': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'XFIELD': 'xcoord',
            'YFIELD': 'ycoord',
            'ZFIELD': '',
            'OUTPUT': parameters['Mapces']
        }
        outputs['CreatePointsLayerFromTable'] = processing.run('native:createpointslayerfromtable', alg_params,
                                                               context=context, feedback=feedback,
                                                               is_child_algorithm=True)
        results['Mapces'] = outputs['CreatePointsLayerFromTable']['OUTPUT']


        return results

    def name(self):
        return 'Classification'

    def displayName(self):
        return 'Classification'

    def group(self):
        return 'TweetmyRiver'

    def groupId(self):
        return ''

    def shortHelpString(self):
        return """<html><body><p></p>
<h2>Input parameters</h2>
<h3>User's training file (.xlsx)</h3>
<p> 
This program requires a training file in the correct format to train a data model. 
If no training file is specified, the program will use a default file for training. 
The training file must be located in the "Data" folder, which can be accessed using the instructions provided in the article. 
A training file template called "Training_template.xlsx" is also located in the "Data" folder.
</p>
<h3>Allowed classification error (%)</h3>
<p>
Enter here the maximum percentage  of tweets expected to be incorrectly classified
</p>
<h3> Number of categories (n) </h3>
<p>
The default number of categories is 3, but enter here a different value if the training file used has a different number of possible categories
</p>
<h3> Output Layer </h3>
<p>
Enter the location where the output layer needs to be saved, or save it as a temporary file otherwise
</p>
<br></body></html>"""

    def createInstance(self):
        return AiTraining()
