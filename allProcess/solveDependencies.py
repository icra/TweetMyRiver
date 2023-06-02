"""
Model exported as python.
Name : model
Group : 
With QGIS : 32206
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterBoolean
import processing
from .installLibraries import installTweepy

class Model(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterBoolean('tweepy', 'tweepy 4.12.1', defaultValue=False))
        self.addParameter(QgsProcessingParameterBoolean('ergfasgdr', 'ergfasgdr', defaultValue=False))
        self.addParameter(QgsProcessingParameterBoolean('drgdrg', 'drgdrg', defaultValue=False))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)
        results = {}
        outputs = {}

        if parameters['tweepy'] == True:
            feedback.setProgressText("---- IMPORTING TWEEPY 4.12.1 ----")
            installTweepy()

        return results

    def name(self):
        return 'model'

    def displayName(self):
        return 'model'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def shortHelpString(self):
        return """<html><body><p></p>
<h2>Input parameters</h2>
<h3>grtr</h3>
<p>tryhrtgyseryeryse</p>
<br></body></html>"""

    def createInstance(self):
        return Model()
