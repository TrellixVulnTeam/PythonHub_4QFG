# Copyright 2017 The UAI-SDK Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from uai.arch.base_model import AiUcloudModel
from uai.arch_conf.xgboost_conf import XGBoostJsonConf
from uai.arch_conf.xgboost_conf import XGBoostJsonConfLoader

class XGBoostUcloudModel(AiUcloudModel):
    """
        Base model class for user defined Tensorflow Model
    """
    def __init__(self, conf=None, model_type='xgboost'):
        super(XGBoostUcloudModel, self).__init__(conf, model_type)
        self.output = {}
        self._parse_conf(conf)
        self.load_model()

    def _parse_conf(self, conf):
        """
            Parse Tensorflow related config
            Args:
                conf: key/val object for AI architecture specific config
        """
        json_conf_loader = XGBoostJsonConfLoader(conf)
        self.model_name = json_conf_loader.get_model_name()

    def load_model(self):
        pass

    def execute(self, data, batch_size):
        pass
