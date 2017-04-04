REGULARIZERS = [
	{"name":"SmoothSparsePhiRegularizer", "params": [{"name":"tau","default" : "1.0"}, {"name":"gamma","default":"None"}]},
	{"name":"DecorrelatorPhiRegularizer", "params": [{"name":"tau","default" : "1.0"}, {"name":"gamma","default":"None"}]},
	{"name":"LabelRegularizationPhiRegularizer", "params": [{"name":"tau","default" : "1.0"}, {"name":"gamma","default":"None"}]},
	{"name":"SpecifiedSparsePhiRegularizer", "params": [{"name":"tau","default" : "1.0"}, {"name":"gamma","default":"None"}]},
	{"name":"ImproveCoherencePhiRegularizer", "params": [{"name":"tau","default" : "1.0"}, {"name":"gamma","default":"None"}]},
	{"name":"SmoothPtdwRegularizer", "params": [{"name":"tau","default" : "1.0"}]},
	{"name":"TopicSelectionThetaRegularizer", "params": [{"name":"tau","default" : "1.0"}]},
	{"name":"TopicSegmentationPtdwRegularizer", "params": [
		{"name":"window", "default":"None"},
		{"name":"threshold", "default":"None"}
	]}
]