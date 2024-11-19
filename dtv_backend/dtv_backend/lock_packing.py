"""This script contains the method to fill the lock. It is used in lock.py. 
Given the length and width of a lock, ships from the queue are placed one by one if it fits. """

import simpy
from operator import attrgetter
from packer2d import Item, pack


def fill_lock(queue: simpy.FilterStore, lock_length: float, lock_width: float):
    """method to determine which ships from the queue can enter the lock simultaneously"""
    vessels = queue.items.copy()
    items = [Item((vessel.L, vessel.B), data=ix) for ix, vessel in enumerate(vessels)]

    try:
        pack(
            items,
            (lock_length, lock_width),
            max_depth=3,
            insert_order=attrgetter("data"),
        )
        # als alle boten erin passen:
        leftover_items = []
        items_in_lock = items
    except AttributeError:
        # als niet alle boten erin passen:
        leftover_items = [
            item
            for item in items
            if (item.rect.x1 == 0 and item.rect.y1 == 0 and item.data != 0)
        ]
        items_in_lock = [item for item in items if item not in leftover_items]
    except:
        raise ValueError(
            f"Error in packing the lock for vessels {[vessel.name for vessel in vessels]}"
        )
    vessels_entering_lock = [vessels[item.data] for item in items_in_lock]

    return vessels_entering_lock
