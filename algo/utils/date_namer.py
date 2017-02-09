import datetime
class DateNamer:
	def __init__(self):
		self.monthes = ["*", "Jan", "Feb", "Mar","Apr", "May", "Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

				
	def date_hash(self, date, group_by):
		if (group_by == "year"):
			return date.year
		elif (group_by == "month"):
			return date.month + 100 * date.year
		elif (group_by == "week"):
			return (date - datetime.datetime(1970, 1, 5, 0, 0, 0, 1)).days // 7
		elif (group_by == "day"):
			return date.day + 100 * date.month + 10000 * date.year
			
	def hash_date(self, date_hash, group_by):
		if (group_by == "year"):
			return datetime.datetime(year=date_hash, month=1, day=1)
		elif (group_by == "month"):
			return datetime.datetime(year=int(date_hash / 100), month=int(date_hash % 100), day=1)
		elif (group_by == "week"):
			return datetime.datetime(1970, 1, 5, 0, 0, 0, 1) + datetime.timedelta(days=7*date_hash)
		elif (group_by == "day"):
			return datetime.datetime(year=int(date_hash / 10000), month=(int(date_hash / 100) % 100), day=(date_hash % 100))
			
	def date_name(self, date_hash, group_by):
		global monthes
		if (group_by == "year"):
			return str(date_hash)
		if (group_by == "month"):
			return self.monthes[int(date_hash % 100)] + " " + str(int(date_hash / 100))  
		if (group_by == "week"): 
			monday = datetime.date(1970, 1, 5) + datetime.timedelta(days = 7 * date_hash)
			sunday = monday + datetime.timedelta(days=6)
			if monday.month == sunday.month:
				return "%s-%s %s %d" % (monday.day, sunday.day, self.monthes[monday.month], monday.year)
			elif monday.year == sunday.year:
				return "%s %s - %s %s %d" % (monday.day, self.monthes[monday.month], sunday.day, self.monthes[sunday.month], monday.year)
			else:
				return "%s %s %d - %s %s %d" % (monday.day, self.monthes[monday.month], monday.year, monday.day, self.monthes[sunday.month], sunday.year)
		elif (group_by == "day"):
			return str(date_hash % 100) + " " + self.monthes[ int(date_hash / 100) % 100] + " " + str(int(date_hash / 10000) % 100)
