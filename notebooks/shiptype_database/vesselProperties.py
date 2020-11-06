# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 09:07:13 2020

@author: KLEF
"""

class createVesselProperties:
    """
    ** openTNSim functionality **
    Add information on possible restrictions to the vessels.
    Height, width, etc.
    """

    def __init__(self,
        cemt_class='unknown',
        rws_class='unknown',
        vessel_type=None, 
        description_dutch=None,
        description_english=None,
        width=0,
        length=0,
        height_empty=0,
        height_full=0,
        draught_empty=0,
        draught_full=0,
        *args,
        **kwargs
    ):
        #super().__init__(*args, **kwargs)

        """Initialization"""
        self.cemt_class = cemt_class
        self.rws_class = rws_class
        self.vessel_type = vessel_type
        self.description_dutch = description_dutch
        self.description_english = description_english

        self.width = width
        self.length = length

        self.height_empty = height_empty
        self.height_full = height_full

        self.draught_empty = draught_empty
        self.draught_full = draught_full