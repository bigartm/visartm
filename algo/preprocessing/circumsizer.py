import os

file_name = os.path.join("D:\\visartm\\data\\datasets", "vw-bow-test", "VW","bow.txt")
with open(file_name, "r", encoding='utf-8') as f:
    lines = f.readlines()

with open(file_name, "w", encoding='utf-8') as f:
    f.writelines(lines[0:200])
    