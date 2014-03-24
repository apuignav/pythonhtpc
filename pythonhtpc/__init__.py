#!/usr/bin/env python
# =============================================================================
# @file   __init__.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   09.03.2014
# =============================================================================
""""""

# Configure logging at package level
import logging
logging.getLogger('htpc').addHandler(logging.NullHandler())
logging.getLogger('htpc').setLevel(logging.DEBUG)

# EOF
