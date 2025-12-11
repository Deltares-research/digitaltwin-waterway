import pickle
import pandas as pd

lock = pd.DataFrame(pickle.load(open("locks.pickle", "rb")))
lock_properties = pd.DataFrame(lock["Value"].values.tolist())
pd.concat([lock, lock_properties], axis=1)
