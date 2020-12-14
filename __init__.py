# Zoom R16 Control Surface script
# Version 1.0.0
# Author: Bebe Jane
# https://github.com/bebejane/ZoomR16XL

from log import *
from ZoomR16XL import ZoomR16XL
from consts import *
import os
from log import *
from datetime import datetime

start = datetime.now()
log('Starting new log at2: ' + start.strftime("%H:%M:%S"))

DIRNAME = os.path.dirname(__file__);

def create_instance(c_instance):
    return ZoomR16XL(c_instance)

from _Framework.Capabilities import *

def get_capabilities():
    return {CONTROLLER_ID_KEY: controller_id(vendor_id=2675, product_ids=[6], model_name='MCU Pro USB v3.1'),
     PORTS_KEY: [inport(props=[SCRIPT, REMOTE]),
                 inport(props=[]),
                 inport(props=[]),
                 inport(props=[]),
                 outport(props=[SCRIPT, REMOTE]),
                 outport(props=[]),
                 outport(props=[]),
                 outport(props=[])]}
