# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 09:01:16 2017

@author: fdm
"""


import pandas as pd
import pickle
import os


def unpack_pickle(input_file, out_folder):
    with open(input_file, "rb") as f:
        model = pickle.load(f)

        theta = model["theta"]
        T, D = theta.shape
        docs_index = theta.columns
        theta.to_pickle(os.path.join(out_folder, "theta"))

        layers = 1
        for i in range(1, 100):
            if ("psi_%d" % i) in model.keys():
                model["psi_%d" % i].to_pickle(
                    os.path.join(out_folder, ("psi%d" % i)))
            else:
                layers = i
                break

        phis = []
        for i in range(layers):
            phi = model["phi_%d" % i]
            print(phi.shape)
            phis.append(phi)
            W, _ = phi.shape

        pd.concat(phis, axis=1).to_pickle(os.path.join(out_folder, "phi"))

        print("Words: %d. Documents: %d. Topics: %d" % (W, D, T))
        print(docs_index)


if __name__ == "__main__":
    model_folder = "D:\\visartm\\data\\datasets\\pn_habr\\models\\model_38"
    unpack_pickle(os.path.join(model_folder, "hartm.mdl"), model_folder)
