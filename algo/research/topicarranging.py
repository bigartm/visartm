import numpy as np 

research.report_text("just testing...")
research.report_text("That's pretty table")
z = [[1,2],[3,4]]
research.report_table(z)
research.gca().imshow(z, interpolation = "nearest")
research.report_picture()

research.report_text("Another picture example")
z = np.random.rand(20,20)
research.gca().imshow(z, interpolation = "nearest")
research.report_picture()


	

